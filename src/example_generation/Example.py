from collections import defaultdict
import tensorflow_datasets as tfds
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Embedding, Dense, LSTM, SimpleRNN, Bidirectional, GRU, Dropout
import matplotlib.pyplot as plt
from soynlp.tokenizer import LTokenizer
from soynlp.word import WordExtractor

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
    def __init__(self,sent, words):
        self.words = words
        self.word_extractor = WordExtractor()
        self.word_extractor.train(sent.split('  '))  # 바꿀 것
        cohesions = self.word_extractor.all_cohesion_scores()
        l_cohesions = {word: score[0] for word, score in cohesions.items()}
        l_cohesions.update(self.words)
        self.tokenizer = LTokenizer(l_cohesions)

    def create_vocab(self, sent):
        vocab_temp = list(set(self.tokenizer(sent)))
        self.vocab = {vocab_temp[_]: _ + 1 for _ in range(len(vocab_temp))}
        self.idx2vocab = {v: k for k, v in self.vocab.items()}

    def create_var(self, sent):
        sent_list = [self.tokenizer(_) for _ in sent]
        for i in range(len(sent_list)):
            for j in range(len(sent_list[i])):
                sent_list[i][j] = self.vocab[sent_list[i][j]]

        sequences = list()
        for line in sent_list:
            for _ in range(1, len(line)):
                sequence = line[:_ + 1]
                sequences.append(sequence)
        self.max_len = max(len(_) for _ in sequences)
        sequences = pad_sequences(sequences, maxlen=self.max_len, padding='pre')
        X = sequences[:, :-1]
        y = sequences[:, -1]
        y = to_categorical(y, num_classes=len(self.vocab) + 1)
        return X, y

    def model(self):
        self.model = Sequential()
        self.model.add(Embedding(self.tokenizer.vocab_size, 10, input_length=self.max_len - 1,
                                 mask_zero=True))  # y데이터를 분리하였으므로 이제 X데이터의 길이는 기존 데이터의 길이 - 1
        self.model.add(GRU(64, return_sequences=True))
        self.model.add(Dropout(0.4))
        self.model.add(GRU(64, return_sequences=False))
        self.model.add(Dropout(0.4))
        self.model.add(Dense(self.tokenizer.vocab_size, activation='softmax'))
        self.model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])

    def sentence_generation(self, current_word, n):
        for _ in range(n):  # n번 반복
            encoded = [self.vocab[_] for _ in current_word.split(' ')]
            encoded = pad_sequences([encoded], maxlen=self.max_len - 1, padding='pre')  # 데이터에 대한 패딩
            result = self.model.predict_classes(encoded, verbose=0)
            current_word = current_word + ' ' + self.idx2vocab[result[0]]  # 현재 단어 + ' ' + 예측 단어를 현재 단어로 변경
        return current_word