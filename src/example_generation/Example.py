from collections import defaultdict
import tensorflow_datasets as tfds
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Embedding, Dense, LSTM, SimpleRNN, Bidirectional, GRU, Dropout, Masking
import matplotlib.pyplot as plt
from soynlp.tokenizer import LTokenizer
from soynlp.word import WordExtractor
import gensim
import numpy as np

# 불용어 처리하지 않고 sentence 추출
def extract_sent(df, words):
    sent = defaultdict(lambda: 0)
    for w in words:
        temp = [s for s in df['head'] if w in s]
        sent[w] = '  '.join(temp)
    return sent

# Overfitting을 확인하기 위해 그래프 그리기
def plot_history(histories, key='categorical_crossentropy'):
    plt.figure(figsize=(16, 10))

    for name, history in histories:
        val = plt.plot(history.epoch, history.history['loss'],
                       '--', label=name.title() + ' Val')
        plt.plot(history.epoch, history.history['loss'], color=val[0].get_color(),
                 label=name.title() + ' Train')

    plt.xlabel('Epochs')
    plt.ylabel(key.replace('_', ' ').title())
    plt.legend()

    plt.xlim([0, max(history.epoch)])

class generator_subtokenizer:
    # Training tokenizer
    def __init__ (self, sent):
        self.tokenizer = tfds.features.text.SubwordTextEncoder.build_from_corpus(sent, target_vocab_size=2 ** 13)

    def create_var(self, sent):
        sequences = list()
        for line in sent:
            encoded = self.tokenizer.encode(line)
            temp = [encoded[:i+1] for i in range(1, len(encoded))]
            sequences.extend(temp)

        # padding 및 data split
        self.max_len = max(len(l) for l in sequences)
        sequences = pad_sequences(sequences, maxlen=self.max_len, padding='pre')
        X = sequences[:, :-1]
        y = sequences[:, -1]
        y = to_categorical(y, num_classes=self.tokenizer.vocab_size)
        return X, y

    def model(self):
        self.model = Sequential()
        self.model.add(Embedding(self.tokenizer.vocab_size, 10, input_length= self.max_len - 1,
                            mask_zero=True))  # y데이터를 분리하였으므로 이제 X데이터의 길이는 기존 데이터의 길이 - 1
        self.model.add(GRU(64, return_sequences=True))
        self.model.add(Dropout(0.4))
        self.model.add(GRU(64, return_sequences=False))
        self.model.add(Dropout(0.4))
        self.model.add(Dense(self.tokenizer.vocab_size, activation='softmax'))
        self.model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])

    def sentence_generation(self, current_word, n):
        for _ in range(n):  # n번 반복
            encoded = self.tokenizer.encode(current_word)  # 현재 단어에 대한 정수 인코딩
            encoded = pad_sequences([encoded], maxlen= self.max_len - 1, padding='pre')  # 데이터에 대한 패딩
            result = self.model.predict_classes(encoded, verbose=0)
            current_word = current_word + ' ' + self.tokenizer.decode([result[0]])  # 현재 단어 + ' ' + 예측 단어를 현재 단어로 변경
        return current_word



class generator_ltokenizer:
    # Training tokenizer
    def __init__(self, words, sent):
        self.word_extractor = WordExtractor()
        self.words = words
        self.word_extractor.train(sent)  # 바꿀 것
        cohesions = self.word_extractor.all_cohesion_scores()
        l_cohesions = {word: score[0] for word, score in cohesions.items()}
        l_cohesions.update(self.words)
        self.tokenizer = LTokenizer(l_cohesions)

    def train_word_model(self, sentences):
        self.word_model = gensim.models.Word2Vec(sentences, size=100, min_count=1,
                                    window=2, iter=100)
        pretrained_weights = self.word_model.wv.syn0
        self.vocab_size, self.embedding_size = pretrained_weights.shape

    def word2idx(self, word):
        return self.word_model.wv.vocab[word].index

    def idx2word(self, idx):
        return self.word_model.wv.index2word[idx]

    def create_var(self, sentences):
        for i in range(len(sentences)):
            for j in range(len(sentences[i])):
                sentences[i][j] = self.word2idx(sentences[i][j])

        sequences = list()
        for line in sentences:
            for _ in range(1, len(line)):
                sequence = line[:_ + 1]
                sequences.append(sequence)
        self.max_sentence_len = max([len(_) for _ in sentences])
        sequences = pad_sequences(sequences, maxlen=self.max_sentence_len, padding='pre')
        X = sequences[:, :-1]
        y = sequences[:, -1]
        return X, y

    def model(self):
        self.model = Sequential()
        self.model.add(Embedding(self.vocab_size, self.embedding_size, input_length=self.max_sentence_len - 1))  # y데이터를 분리하였으므로 이제 X데이터의 길이는 기존 데이터의 길이 - 1
        self.model.add(Bidirectional(GRU(64, return_sequences=False)))
        self.model.add(Dropout(0.3))
        self.model.add(Dense(self.vocab_size, activation='softmax'))
        self.model.compile(loss='sparse_categorical_crossentropy', optimizer='adam', metrics=['accuracy'])

    def sentence_generation(self, word, n):
        word_idxs = [self.word2idx(word)]
        for _ in range(n):  # n번 반복
            encoded = pad_sequences([word_idxs], maxlen=self.max_sentence_len - 1, padding='pre')  # 데이터에 대한 패딩
            result = self.model.predict(encoded)
            word_idxs.append(np.argmax(result))
        return ' '.join(self.idx2word(idx) for idx in word_idxs)