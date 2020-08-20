from collections import defaultdict
from soynlp.word import WordExtractor
from soynlp.vectorizer import sent_to_word_contexts_matrix
from soynlp.word import pmi as pmi_func
from soynlp.tokenizer import LTokenizer
import pandas as pd
import sqlite3
import numpy as np
import re
from string import punctuation

# Stopwords 처리
pattern1 = re.compile(r'[{}]'.format(re.escape(punctuation)))  # punctuation 제거
pattern2 = re.compile(r'[^가-힣 ]')  # 특수문자, 자음, 모음, 숫자, 영어 제거
pattern3 = re.compile(r'\s{2,}')  # white space 1개로 바꾸기.

class Sentiment:
    def __init__(self):
        self.word_extractor = WordExtractor()

    def extract_sent(self, df, words):
        # 불용어 처리
        df['head'] = df['head'].map(lambda x: pattern3.sub(' ',
                                                           pattern2.sub('',
                                                                        pattern1.sub('', x))))
        # sentence 추출
        sent = defaultdict(lambda: 0)
        for w in words:
            temp = [s for s in df['head'] if w in s]
            sent[w] = '  '.join(temp)

        return sent

    # 입력 k, v에 대해서 (k는 word, v는 sentence이다.) 가장 유사한 10개의 단어에 대해서 (단어, pmi) 쌍을 출력해준다.
    def extract_most_related(self, k, v, words, num=10):
        self.word_extractor.train([v])
        cohesions = self.word_extractor.all_cohesion_scores()
        l_cohesions = {word: score[0] for word, score in cohesions.items()}
        l_cohesions.update(words)
        tokenizer = LTokenizer(l_cohesions)
        x, idx2vocab = sent_to_word_contexts_matrix([v], windows=3, min_tf=10, tokenizer=tokenizer,
                                                    dynamic_weight=False, verbose=True)
        pmi, px, py = pmi_func(x, min_pmi=0, alpha=0.0, beta=0.75)
        vocab2idx = {vocab: idx for idx, vocab in enumerate(idx2vocab)}
        query = vocab2idx[k]
        submatrix = pmi[query, :].tocsr()  # get the row of query
        contexts = submatrix.nonzero()[1]  # nonzero() return (rows, columns)
        pmi_i = submatrix.data
        most_relateds = [(idx, pmi_ij) for idx, pmi_ij in zip(contexts, pmi_i)]
        most_relateds = sorted(most_relateds, key=lambda x: -x[1])[:num]
        most_relateds = [(idx2vocab[idx], pmi_ij) for idx, pmi_ij in most_relateds if len(idx2vocab[idx]) > 1]

        return most_relateds

    # 입력 word - sent 쌍으로 된 입력에 대해서 sentiment 점수를 excel에 저장해주고
    # 신조어와 most_related (단어, pmi) 쌍을 출력해준다.
    def cal_score(self, sentence):
        mapping_most_related = defaultdict(lambda: 0)

        # dictionary 형태로 변환한다.
        sent = defaultdict(lambda: 0)
        for _ in range(len(sentence)):
            sent[sentence['index'][_]] = sentence['0'][_]
        score_dict = defaultdict(lambda: 0)

        words = {_: 1.0 for _ in sent.keys()}
        sentiment = pd.read_excel('sentiment.xlsx')  # 여기서 sentiment.xlsx는 감성사전이다.
        # 이는, 처음에 most_related 한 것들 중 길이가 1보다 큰 단어에 대해서 추출하여 직접 라벨링하였다.

        # 각 단어에 대해서 sentiment 점수를 계산한다.
        for k, v in sent.items():
            mapping_most_related[k] = self.extract_most_related(k,v,words)
            pn_score = 0
            for _ in mapping_most_related[k]:
                if sum(sentiment[0] == _[0]) != 0:
                    pn_score += _[1] * sentiment[sentiment[0] == _[0]]['P/N'].iloc[0]
            score_dict[k] = pn_score

        # sentiment 점수를 엑셀 파일로 저장한다.
        temp = pd.DataFrame(sorted(score_dict.items(), key=lambda _: _[1], reverse=True))
        temp.to_excel('sentiment_result.xlsx')

        return mapping_most_related

    # sentiment_result에서 상위 3개씩 positive, negative 단어를 뽑아서 그에 대한 most_related 20개의 감성사전 score update
    # 이 때, 이미 positive와 negative 목록에 있는 애들은 중복해서 update 되지 않도록 설정.
    # 즉, 신조어에 대한 감성을 평가하기 위해 학습하는 과정이다.
    def update_score(self, positive, negative, sentiment_result):
        sent_dict = defaultdict(lambda: 0)
        # (positive) top3 단어에 대해서, sent_dict에 '단어' : 'P' 로 추가
        count = 0
        for _ in sentiment_result[0]:
            if _ not in positive:
                sent_dict[_] = "P"
                count += 1
            if count > 3:
                break

        # sentiment_result 순서 반대로 변환
        temp = list(sentiment_result[0])
        sentiment_result = []
        for _ in range(len(temp)):
            sentiment_result.append(temp.pop(-1))
        count = 0
        # (negative) top3 단어에 대해서, sent_dict에 '단어' : 'N' 로 추가
        for _ in sentiment_result:
            if _ not in negative:
                sent_dict[_] = "N"
                count += 1
            if count > 3:
                break

        # list 형태로 만들어서 positive, negative 목록에 추가
        sent_dict = pd.DataFrame.from_dict(sent_dict, orient='index')
        ptemp = list(sent_dict[sent_dict[0] == 'P'].index)
        ntemp = list(sent_dict[sent_dict[0] == 'N'].index)
        for _ in ptemp:
            positive.append(_)
        for _ in ntemp:
            negative.append(_)

        # (word, sentence) 쌍으로, pandas dataframe 생성
        conn = sqlite3.connect('sent.db')
        sent = pd.read_sql('SELECT * FROM sent', conn)
        ptemp = pd.DataFrame()
        ntemp = pd.DataFrame()
        for _ in positive:
            ptemp = pd.concat([ptemp, sent[sent['index'] == _]], axis=0, ignore_index=True)
        for _ in negative:
            ntemp = pd.concat([ntemp, sent[sent['index'] == _]], axis=0, ignore_index=True)

        # dictionary 형태로 변환
        psent = defaultdict(lambda: 0)
        nsent = defaultdict(lambda: 0)
        for _ in range(len(ptemp)):
            psent[ptemp['index'][_]] = ptemp['0'][_]
        for _ in range(len(ntemp)):
            nsent[ntemp['index'][_]] = ntemp['0'][_]

        # 긍정 단어에 대해서 most_related한 단어 20개 추출하여, 그들의 감성 score 업데이트
        temp_score_dict = defaultdict(lambda: 0)
        words = {_: 1.0 for _ in psent.keys()}
        for k, v in psent.items():
            most_relateds = self.extract_most_related(k,v,words, 20)
            for _ in most_relateds:
                temp_score_dict[_[0]] += _[1] * 0.1

        # 부정 단어에 대해서 most_related한 단어 20개 추출하여, 그들의 감성 score 업데이트
        words = {_: 1.0 for _ in nsent.keys()}
        for k, v in nsent.items():
            most_relateds = self.extract_most_related(k,v,words, 20)
            for _ in most_relateds:
                temp_score_dict[_[0]] -= _[1] * 0.1

        # 감성사전 dict 형태로 변환
        sentiment = pd.read_excel('sentiment.xlsx')
        temp = defaultdict(lambda: 0)
        for _ in range(len(sentiment)):
            temp[sentiment[0][_]] = sentiment['P/N'][_]

        # 감성사전 update
        for k, v in temp_score_dict.items():
            temp[k] += v

        # 감성사전 excel로 저장
        test = pd.DataFrame.from_dict(temp, orient='index')
        test1 = pd.DataFrame(test.index)
        test2 = pd.DataFrame(test[0].values, columns=['P/N'])
        pd.concat([test1, test2], axis=1).to_excel('sentiment.xlsx')

        return positive, negative

    def sentiment_analysis(self, sentiment, mapping_most_related):
        score_dict = defaultdict(lambda: 0)
        for k, v in mapping_most_related.items():
            pn_score = 0
            for _ in v:
                if sum(sentiment[0] == _[0]) != 0:
                    pn_score += _[1] * sentiment[sentiment[0] == _[0]]['P/N'].iloc[0]
            score_dict[k] = pn_score
        temp = pd.DataFrame(sorted(score_dict.items(), key=lambda _: _[1], reverse=True))
        temp.to_excel('sentiment_result.xlsx')
