from collections import defaultdict
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Embedding, Dense, LSTM, SimpleRNN, Bidirectional, GRU, Dropout, Masking
from soynlp.tokenizer import LTokenizer
from soynlp.word import WordExtractor
import gensim
import numpy as np

# 불용어 처리하지 않고 sentence 추출
def extract_sent(df, words): # 전체 Dataset과 신어를 입력
    sent = defaultdict(lambda: 0)
    for w in words:
        temp = [s for s in df['head'] if w in s]
        sent[w] = '  '.join(temp)
        # DataFrame 에서 각 문장에서 신어가 포함되어있으면 그 문장을 temp에 저장한다. 
        # sent dict에 key = 신어, value = 신어가 포함된 예문 전체(문장은 double space로 구분)로 저장한다. 
    return sent # Stopwords가 처리되지 않은, 신어가 포함된 모든 문장 출력

class generator_ltokenizer:
    # Training soynlp tokenizer
    def __init__(self, words, sent): # 해당 신어와 그에 매치되는 sentences set 입력
        self.word_extractor = WordExtractor()
        self.words = words
        self.word_extractor.train(sent)  # 바꿀 것
        cohesions = self.word_extractor.all_cohesion_scores()  # cohesion_scores를 cohesions에 저장
        l_cohesions = {word: score[0] for word, score in cohesions.items()} # 각 단어와 각 단어의 cohesion_forward값을 l_cohesions에 저장
        l_cohesions.update(self.words)
        self.tokenizer = LTokenizer(l_cohesions) # LTokenizer 사용

    # 각 신어-문장 set에 대하여 Word2Vec Training
    def train_word_model(self, sentences): # 위 학습된 tokenizer로 tokenizing된 sentences set 입력
        self.word_model = gensim.models.Word2Vec(sentences, size=100, min_count=1,
                                    window=2, iter=100) # Word2Vec Training
        pretrained_weights = self.word_model.wv.syn0
        self.vocab_size, self.embedding_size = pretrained_weights.shape

    # 입력된 단어에 대해 매치되는 index 반환
    def word2idx(self, word):
        return self.word_model.wv.vocab[word].index

    # 입력된 index에 대해 매치되는 단어 반환
    def idx2word(self, idx):
        return self.word_model.wv.index2word[idx]

    # 각 문장의 단어를 index로 변환
    def create_var(self, sentences): # Tokenizing된 sentences set 입력
        for i in range(len(sentences)):
            for j in range(len(sentences[i])):
                sentences[i][j] = self.word2idx(sentences[i][j])

        sequences = list()
        for line in sentences:
            for _ in range(1, len(line)):
                sequence = line[:_ + 1]
                sequences.append(sequence)
        self.max_sentence_len = max([len(_) for _ in sentences]) # 전체 문장 중 최대 길이
        sequences = pad_sequences(sequences, maxlen=self.max_sentence_len, padding='pre') # max_sentence_len을 기준으로 패딩
        X = sequences[:, :-1]
        y = sequences[:, -1]
        return X, y # index set으로 변환하고 그것을 model에 fit 시킬 수 있도록 X변수와 y변수로 출력

    # Bidirectional GRU Model 설계
    def model(self):
        self.model = Sequential()
        self.model.add(Embedding(self.vocab_size, self.embedding_size, input_length=self.max_sentence_len - 1))  # y데이터를 분리하였으므로 이제 X데이터의 길이는 기존 데이터의 길이 - 1
        self.model.add(Bidirectional(GRU(64, return_sequences=False)))
        self.model.add(Dropout(0.3))
        self.model.add(Dense(self.vocab_size, activation='softmax'))
        self.model.compile(loss='sparse_categorical_crossentropy', optimizer='adam', metrics=['accuracy'])

    # 위 model을 이용하여 해당 신어에 대해 원하는 길이만큼의 문장 출력
    def sentence_generation(self, word, n): # 신어와 원하는 길이를 입력하면 해당 길이 만큼 문장 생성
        word_idxs = [self.word2idx(word)]
        for _ in range(n):  # n번 반복
            encoded = pad_sequences([word_idxs], maxlen=self.max_sentence_len - 1, padding='pre')  # 데이터에 대한 패딩
            result = self.model.predict(encoded)
            word_idxs.append(np.argmax(result))
        return ' '.join(self.idx2word(idx) for idx in word_idxs) # 생성된 문장 출력