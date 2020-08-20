import sqlite3
import pandas as pd
from soynlp.noun import LRNounExtractor_v2
from collections import defaultdict
import re
import numpy as np
import math
from string import punctuation
from soynlp.word import WordExtractor

# Stopwords 처리
pattern1 = re.compile(r'[{}]'.format(re.escape(punctuation)))  # punctuation 제거
pattern2 = re.compile(r'[^가-힣 ]')  # 특수문자, 자음, 모음, 숫자, 영어 제거
pattern3 = re.compile(r'\s{2,}')  # white space 1개로 바꾸기.


class Ext:
    def __init__(self, df):
        self.df = df
        self.noun_extractor = LRNounExtractor_v2(verbose=True)
        self.word_extractor = WordExtractor(min_frequency=math.floor(len(self.df) * 0.0001))

    def cleaning(self):
        self.df['head'] = self.df['head'].map(lambda x: pattern3.sub(' ',
                                                                     pattern2.sub('',
                                                                                  pattern1.sub('', x))))
        return self.df

    def extract_nouns(self):
        nouns = self.noun_extractor.train_extract(self.df['head'], min_noun_frequency=math.floor(len(self.df) * 0.0001))
        words = {k: v for k, v in nouns.items() if len(k) > 1}
        return words

    def search_dict(self, nouns):
        # 사전 검색 결과 없는 단어 추출
        conn = sqlite3.connect('kr_db.db')
        cur = conn.cursor()
        data = pd.read_sql('SELECT word FROM kr_db', conn)
        data['word'] = data['word'].map(lambda x: pattern3.sub(' ',
                                                               pattern2.sub('',
                                                                            pattern1.sub('', x))))
        data.drop_duplicates(keep='first', inplace=True)
        data = ' '.join(data['word'])
        return pd.DataFrame([_ for _ in nouns if _[0] not in data])

    # 의미 추출을 위한 training data set 생성
    def extract_sent(self, words):
        sent = defaultdict(lambda: 0)
        for w in words[0]:
            temp = [s for s in self.df['head'] if w in s and np.random.uniform() > 0.5]
            sent[w] = '  '.join(temp)
        return sent

    def extract_statistic_value(self, sent):
        statistic = defaultdict(lambda: 0)
        for k, v in sent.items():
            self.word_extractor.train([v])
            try:
                statistic[k] = self.word_extractor.extract()[k]
            except Exception as e:
                print(e)
        return statistic

    def extract_r_rat(self, sent, statistic):
        conn = sqlite3.connect('kr_db.db')
        post_pos = pd.read_sql('SELECT word FROM kr_db WHERE ID="조사_기초" OR ID="조사_상세"', conn)
        post_pos['word'] = post_pos['word'].map(lambda x: pattern3.sub(' ',
                                                                       pattern2.sub('',
                                                                                    pattern1.sub('', x))))
        post_pos.drop_duplicates(keep='first', inplace=True)
        post_pos = ''.join(post_pos['word'])
        r_rat = defaultdict(lambda: 0)
        for k in statistic.keys():
            try:
                self.noun_extractor.train_extract([sent[k]])
                count = pprat = wsrat = pnrat = 0
                for _ in self.noun_extractor.lrgraph.get_r(k, topk=-1):
                    if _[0] == '들':
                        pnrat += _[1]
                    elif _[0] in post_pos:
                        if _[0] != '':
                            pprat += _[1]
                        elif _[0] == '':
                            wsrat = _[1]
                for _ in self.noun_extractor.lrgraph.get_r(k, topk=-1):
                    count += _[1]

                r_rat[k] = {'rpprat': pprat / count, 'rwsrat': wsrat / count, 'rpnrat': pnrat / count}
            except Exception as e:
                print(e)
        return r_rat

    def combine_var(self, statistic, r_rat):
        statistic = pd.DataFrame().from_dict(statistic).T
        r_rat = pd.DataFrame().from_dict(r_rat).T
        statistic["rpprat"] = r_rat["rpprat"]
        statistic["rwsrat"] = r_rat["rwsrat"]
        statistic['rpnrat'] = r_rat["rpnrat"]
        statistic.rename(columns={0: 'cohesion_forward', 1: 'cohesion_backward', 2: 'left_branching_entropy',
                                  3: 'right_branching_entropy', 4: 'left_accessor_variety', 5: 'right_accessor_variety',
                                  6: 'leftside_frequency', 7: 'rightside_frequency',
                                  'rpprat': 'right_post_postion_ratio', 'rwsrat': 'right_whitespace_ratio', 'rpnrat':'rigt_pluralnouns_ratio'},
                         inplace=True)
        return statistic