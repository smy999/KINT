from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import json
import pandas as pd
from random import *
import xlrd
import math

#######################################################################################

app = Flask(__name__)

################################## 전역 변수 #############################################

# 각 함수에서 쓰이는 변수 값들 global 선언

# 입력 검색어
term = ""
# 신어 데이터에 검색어가 있는지 없는지 판단할 때 사용되는 flag
varbreak = 0
# 감성분석(긍정, 부정)
sens = list()
# 예문추출
exams = ""
# 연관 키워드
rel_term = list()
# 이달의 KINT
month_term = list()
# 날짜별 빈도 데이터
dataDate = list()
# 커뮤니티, 뉴스별 비율 데이터
dataRef = list()



################################# 감성 분석 #############################################

# 감성 분석 엑셀 파일 불러오기
sent_pd = pd.read_excel('sentiment_final.xlsx')
# print(sent_pd)

# 신어 개수
sentLen = len(sent_pd)
print(sentLen)

# 함수: 해당 검색어에 대한 정보 추출
def sent_func(term):
    global sens
    sens = list()
    for i in range(sentLen):
        if term == sent_pd['Word'][i]:
            # 감성 분석 결과 가져오기
            pos = sent_pd['Positive'][i]
            pos = math.trunc(pos)
            neg = 100 - pos
            sens.append(str(pos)+"%")
            sens.append(str(neg)+"%")
            break
    return sens


################################# 예문 출력 #############################################
# 감성 분석 엑셀 파일 불러오기
exam1_pd = pd.read_excel('News_example.xlsx')
exam2_pd = pd.read_excel('Total_wsexample.xlsx')
exam_pd = pd.concat([exam1_pd, exam2_pd])

# 신어 개수
examLen = len(exam_pd)

# 함수: 해당 검색어에 대한 정보 추출
def exam_func(term):
    global exams
    exams = ""
    for i in range(len(exam_pd)):
        if term == exam_pd.iloc[i]['Word']:
            # 예문 가져오기
            exams = exam_pd.iloc[i][0]
            # 감성 분석 결과 가져오기
            break
    return exams


############################### 연관 키워드 #############################################
# 연관 키워드 엑셀 파일 불러오기
newsK = pd.read_excel('News_key.xlsx')
commK = pd.read_excel('key.xlsx')

key_pd = pd
key_pd = pd.concat([newsK, commK])

key_pd = key_pd.rename({'Unnamed: 0': 'word'}, axis=1)

key_pd = key_pd.sort_values(by='word', axis=0, ascending=True)
key_pd = key_pd.reset_index(drop=True)

# Nan 값 오류를 방지하기 위해 0으로 값 변경
key_pd = key_pd.fillna(0)

# 함수: 해당 검색어에 대한 정보 추출
rel_term = list()

tempK = key_pd[key_pd['word'].duplicated()]

for i in range(len(key_pd)):
    rel_dict = dict()

    if i+1 in tempK.index:
        continue
    if i in tempK.index:
        tempKK = list()

        # 중복 키워드 받아오기
        tempKK.append(key_pd.loc[i]['word'])

        keyLen1 = len(key_pd.loc[i])

        for j in range(keyLen1 - 1):
            if key_pd.loc[i][j] == 0:
                continue
            value = tuple(key_pd.loc[i][j].split("'"))
            value2 = tuple(value[2].split(","))
            value2 = tuple(value2[1].split(")"))
            value2 = tuple(value2[0].split(" "))

            rel_dict[value[1]] = value2[1]


        keyLen2 = len(key_pd.loc[i-1])

        for j in range(keyLen2 - 1):
            if key_pd.loc[i-1][j] == 0:
                continue
            value = tuple(key_pd.loc[i-1][j].split("'"))
            value2 = tuple(value[2].split(","))
            value2 = tuple(value2[1].split(")"))
            value2 = tuple(value2[0].split(" "))

            rel_dict[value[1]]= value2[1]

        rel_list=list()
        rel_list = sorted(rel_dict.items(), key = lambda x:x[1], reverse=True)

        for k in range(keyLen1+keyLen2):
            tempKK.append(rel_list[k][0])
            if k == 4:
                break

        key_pd.drop(i, inplace=True)
        key_pd.drop(i - 1, inplace=True)

        # 중복 검색어 빈도합 추가
        key_pd.loc[i] = tempKK


    else:
        tempKK = list()

        # 중복 키워드 받아오기
        tempKK.append(key_pd.loc[i]['word'])


        keyLen = len(key_pd.loc[i])


        for j in range(keyLen-1):
            if key_pd.loc[i][j] == 0:
                tempKK.append(0)
                continue
            value = tuple(key_pd.loc[i][j].split("'"))
            value2 = tuple(value[2].split(","))
            value2 = tuple(value2[1].split(")"))
            value2 = tuple(value2[0].split(" "))

            tempKK.append(value[1])
            if j == 4:
                break

        key_pd.drop(i, inplace=True)
        key_pd.loc[i] = tempKK


# 함수: 해당 검색어에 대한 정보 추출
def rel_func(term):
    global rel_term
    rel_term = list()
    global varbreak
    varbreak = 0
    for i in range(len(key_pd)-1):

        if term == key_pd.iloc[i]['word']:
            varbreak = 0
            keyLen = len(key_pd.iloc[i])
            for j in range(0, keyLen-1):
                if key_pd.iloc[i][j] == 0:
                    continue
                rel_term.append(key_pd.iloc[i][j])
            return rel_term
    varbreak = 1
    return rel_term



################################# 빈도 분석 #############################################

# 빈도 엑셀 파일 불러오기
newsD = pd.read_excel("News_date.xlsx")
wordD2 = pd.read_excel("word2_date.xlsx")
wordD4 = pd.read_excel("word4_date.xlsx")
wordD31 = pd.read_excel("word3_1_date.xlsx")
wordD32 = pd.read_excel("word3_2_date.xlsx")
addword = pd.read_excel("addword_date.xlsx")

finalD = pd.concat([newsD, newsD, wordD2, wordD4, wordD31, wordD31, addword])
finalD = finalD.rename({'Unnamed: 0': '0'}, axis=1)
finalD = finalD.fillna(0)

labelD = list(finalD.columns)
labelD = sorted(labelD)

finalD = finalD[labelD]

del labelD[0]


finalD = finalD.sort_values(by='0', axis=0, ascending=True)
finalD = finalD.reset_index(drop=True)


# 중족 데이터 받아오기
tempD = finalD[finalD['0'].duplicated()]

for i in tempD.index:
    tempDD = list()

    # 중복 키워드 받아오기
    tempDD.append(finalD.loc[i]['0'])

    # 중복 빈도수 더하기
    for j in labelD:
        tempDD.append(finalD.loc[i][j]+finalD.loc[i-1][j])

    # 기존 데이터 삭제
    finalD.drop(i, inplace=True)
    finalD.drop(i-1, inplace=True)

    # 중복 검색어 빈도합 추가
    finalD.loc[i]=tempDD


date_pd = pd
date_pd = finalD

# 신어 개수
dateLen = len(date_pd)

# 컬럼(커뮤니티, 신문사, key) 가져와서 key 빼고 저장: 그래프 labels에 쓰일 데이터
labelDate = list(date_pd.columns)
del labelDate[0]

def date_func(term):
    global dataDate
    dataDate = list()

    for i in range(dateLen):
        if term == date_pd.iloc[i]['0']:
            dataDate = list(date_pd.iloc[i])

            del dataDate[0]
            break
    return dataDate

################################# 이달의 KINT #############################################

newsM = pd.read_excel("News_month.xlsx")
word2 = pd.read_excel("word2_month.xlsx")
word4 = pd.read_excel("word4_month.xlsx")
word31 = pd.read_excel("word3_1_month.xlsx")
word32 = pd.read_excel("word3_2_month.xlsx")
addwordM = pd.read_excel("addword_month.xlsx")

finalM = pd.concat([newsM, newsM, word2, word4, word31, word32, addwordM])
finalM = finalM.rename({'Unnamed: 0': 1}, axis=1)

labelM = list(finalM.columns)
del labelM[0]

finalM = finalM.fillna(0)
finalM = finalM.sort_values(by=1, axis=0, ascending=True)
finalM = finalM.reset_index(drop=True)

# 중족 데이터 받아오기
tempM = finalM[finalM[1].duplicated()]

for i in tempM.index:
    tempMM = list()

    # 중복 키워드 받아오기
    tempMM.append(finalM.loc[i][1])
    # 중복 빈도수 더하기
    for j in labelM:
        tempMM.append(finalM.loc[i][j]+finalM.loc[i-1][j])

    # 기존 데이터 삭제
    finalM.drop(i, inplace=True)
    finalM.drop(i-1, inplace=True)

    # 중복 검색어 빈도합 추가
    finalM.loc[i]=tempMM


# 내림차순 정렬
finalM = finalM.sort_values(by=0, axis=0, ascending=False)

# top5 추출
month_term = list(finalM[1].head(5))


################################# 비율 분석 #############################################

# 오늘의유머베스트오브베스트 : 1
# 오늘의유머베스트게시판 : 2
# 일베일간베스트 : 3
# 일베정치/시사 : 201
# 디시인사이드야구갤러리 : 4
# 디시인사이드인터넷방송갤러리 : 100
# 디시인사이드남자연예인갤러리 : 101
# 디시인사이드여자연예인갤러리 : 102
# 뽐뿌_자유게시판 : 5
# 네이트판_10대게시판 : 6
# 네이트판20대게시판 :7
# 네이트판톡커들의선택 : 8
# 인스티즈이슈 : 103
# 보배드림정치 : 200

wordR2 = pd.read_excel('word2_ref.xlsx')
wordR4 = pd.read_excel('word4_ref.xlsx')
wordR31 = pd.read_excel('word3_1_ref.xlsx')
wordR32 = pd.read_excel('word3_2_ref.xlsx')
addwordR = pd.read_excel('addword_ref.xlsx')
wordR = pd.concat([wordR2, wordR4, wordR31, wordR32, addwordR])

wordR.columns = ["word","d1", "d2", "i1", "p1", "t2", "d3", "n3", "n1", "n2", "t1", "b1", "i2"]

wordR = wordR.fillna(0)
wordR = wordR.sort_values(by='word', axis=0, ascending=True)
wordR = wordR.reset_index(drop=True)

wordRR = pd
wordR['오늘의유머'] = wordR.apply(lambda x:x.t1+x.t2, axis='columns')
wordR['일간베스트'] = wordR.apply(lambda x:x.i1+x.i2, axis='columns')
wordR['디시인사이드'] = wordR.apply(lambda x:x.d1+x.d2+x.d3, axis='columns')
wordR['뽐뿌'] = wordR["p1"]
wordR['네이트판'] = wordR.apply(lambda x:x.n1+x.n2+x.n3, axis='columns')
wordR['보배드림'] = wordR["b1"]
print(wordR)

wordR.drop(["d1", "d2", "i1", "p1", "t2", "d3", "n3", "n1", "n2", "t1", "b1", "i2"], axis='columns', inplace=True)

# 비율 엑셀 파일 불러오기
ref_pd = pd.read_excel('News_ref.xlsx')

# 신어 개수
refLen = len(ref_pd)

# NaN 값 0으로 변환
ref_pd = ref_pd.fillna(0)
ref_pd = ref_pd.rename({'Unnamed: 0': 0}, axis=1)

# column(년월) 순 정렬
ref_pd = ref_pd.sort_index(axis=1)


ref_pd['한겨레'] = ref_pd[300]
ref_pd['경향신문'] = ref_pd[301]
ref_pd['매일경제'] = ref_pd[302]
ref_pd['조선일보'] = ref_pd[303]
ref_pd['디지털타임스'] = ref_pd[304]
ref_pd['동아일보'] = ref_pd[305]
ref_pd['SBS뉴스'] = ref_pd[306]

ref_pd.drop([300, 301, 302, 303, 304, 305, 306], axis='columns', inplace=True)
ref_pd['뉴스'] = ref_pd.apply(lambda x: x.한겨레 + x.경향신문 + x.매일경제 + x.조선일보 + x.디지털타임스 + x.동아일보 + x.SBS뉴스, axis='columns')


def ref_func(term):

    global flagN, flagC
    global dataRef
    global labelRef

    news_i = 0
    cumm_i = 0
    flagN = 0
    flagC = 0
    for news_i in range(len(ref_pd)):
        if term == ref_pd[0][news_i]:
            flagN = 1
            break

    for cumm_i in range(len(wordR)):
        if term == wordR['word'][cumm_i]:
            flagC = 1
            break

    if flagN+flagC == 2:

        # 그래프 라벨
        labelRef = wordR.columns.tolist()
        del labelRef[0]
        labelRef.append("뉴스")

        for j in range(len(labelRef)-1):
            dataRef.append(wordR[labelRef[j]][cumm_i])
        dataRef.append(ref_pd['뉴스'][news_i])

        data_sum = 0
        for i in range(len(dataRef)):
            data_sum += dataRef[i]

        for i in range(len(dataRef)):
            dataRef[i] = (dataRef[i] * 100) / data_sum

        return dataRef

    # 뉴스와 커뮤니티 한 곳에만 존재하는 신어일 때
    else:
        # 뉴스에만 존재하는 신어
        if flagN == 1:
            # 한겨레 : 300, 경향신문 : 301, 매일경제 : 302, 조선일보 : 303, 디지털타임스 : 304, 동아일보 : 305, SBS뉴스 : 306, 한국경제 : 307
            labelRef = ref_pd.columns.tolist()

            del labelRef[len(labelRef)-1]
            del labelRef[0]
            refLen = len(labelRef)

            dataRef = list()

            if term == ref_pd[0][news_i]:
                for j in labelRef:
                    dataRef.append(ref_pd[j][news_i])

            data_sum = 0
            for i in range(len(dataRef)):
                data_sum += dataRef[i]

            for i in range(len(dataRef)):
                dataRef[i] = (dataRef[i]*100)/data_sum

            return dataRef
        # 커뮤니티에만 존재하는 신어
        else:
            labelRef = wordR.columns.tolist()
            del labelRef[0]
            refLen = len(labelRef)

            if term == wordR['word'][cumm_i]:
                for j in labelRef:
                    dataRef.append(wordR[j][cumm_i])

            data_sum = 0
            for i in range(len(dataRef)):
                data_sum += dataRef[i]

            for i in range(len(dataRef)):
                dataRef[i] = (dataRef[i] * 100) / data_sum

            return dataRef


################################### 메인 페이지 ####################################################

# home page
@app.route('/')
def home():
    global month_term

    # 현재 실행 위치 출력
    print('home')
    # reauest 방식 확인 출력
    print(request.method)

    # home.html 렌더링
    return render_template("home.html", month_term=month_term)


################################ 검색 페이지 ##################################################

# search
@app.route('/', methods=['POST', 'GET'])
def search():
    global month_term
    global varbreak
    # 검색 기본 페이지 > search2.html
    render_template('search2.html', month_term=month_term)
    # 현재 실행 위치 출력
    print('search')
    # request 방식 확인 출력
    print(request.method)

    # "POST" 일 때
    if request.method == 'POST':

        # html에서 입력된 검색어 받아오기
        req = request.form.to_dict()
        print(req)
        # 검색어 받아와서 필터링
        term = req['term']
        term = term.replace('#', '')
        term = term.replace('들', '')

        # word_func(term)


        # 1. 입력된 검색어가 없을 때 처리방법
        if len(term) == 0:
            # 1-1. 검색어가 없고, 이달의 신조어가 클릭되었을 때
            if 'mon' in req:
                # 선택된 이달의 신조어를 검색어로 변경하고 필터링
                term = req['mon']
                print('선택된 이달의 신조어(mon)가 있을 때')
                term = term.replace('#', '')
                term = term.replace('들', '')

                # word_func(term)

                # 바뀐 검색어에 대해 연관 키워드 추출
                rel_term = rel_func(term)

                if varbreak == 1:
                    print('검색어에 맞는 결과 없음')
                    return render_template("search2.html", month_term=month_term, result="no", term=term)
                else:
                    print('검색어에 맞는 결과 있음')
                    # 감성 분석 결과 받아오기
                    sens = sent_func(term)
                    # 빈도 분석 결과 받아오기
                    dataRef = ref_func(term)
                    # 예문 받아오기
                    sentence = exam_func(term)
                    # 커뮤니티, 뉴스별 비율 받아오기
                    dataDate = date_func(term)

                    # search.html: 검색 결과 보여주기
                    return render_template('search.html', sent1=sens[0], sent2=sens[1], sentence=sentence,
                                           term=term, rel_term=rel_term, labelRef=labelRef, labelDate=labelDate,
                                           dataDate=dataDate, dataRef=dataRef)

            # 1-2. 검색어도 없고, 이달의 신조어 클릭도 아닐 때 > 그냥 검색 버튼을 누르거나 검색창에서 Enter 눌렀을 때
            else:
                print('선택된 이달의 신조어(mon)가 없을 때')
                # search2.html: 아무것도 검색하지 않았을 때 > 검색 페이지 이동
                return render_template("search2.html", month_term=month_term, result="")



        # 검색어에 맞는 연관 키워드 추출
        rel_term = rel_func(term)
        # 2. 입력된 검색어가 있을 때
        # 2-1. 위에서 필더링한 검색어의 결과가 없을 때 > 검색 페이지로 이동(search2.hmtl)
        if varbreak == 1:
            print('입력된 검색어의 검색 결과가 없습니다.')
            # search2.html: 검색어에 맞는 결과가 없을 때 > "검색 결과가 없습니다." 출력
            return render_template("search2.html", month_term=month_term, result="no", term=term)

        # 2-2. 위에서 필터링한 검색어의 결과가 있을 때 > 결과 페이지로 이동(search.html)
        else:
            print('입력된 검색어의 검색 결과가 있습니다.')
            # 감성 분석 결과 받아오기
            sens = sent_func(term)
            # 빈도 분석 결과 받아오기
            dataRef = ref_func(term)
            # 예문 받아오기
            sentence = exam_func(term)
            # 커뮤니티, 뉴스별 비율 받아오기
            dataDate = date_func(term)

            # search.html: 검색 결과 보여주기
            return render_template('search.html', sent1=sens[0], sent2=sens[1], sentence=sentence,
                                   term=term, rel_term=rel_term, labelRef=labelRef, labelDate=labelDate,
                                   dataDate=dataDate, dataRef=dataRef)

    if request.method == 'GET':
        return render_template("search2.html", month_term=month_term, result="")


##################################### 에러 핸들링 ################################################

@app.errorhandler(404)
def page_not_found1(error):
    return redirect('/search2')


############################### 실행 #######################################################

if __name__ == '__main__':
    app.run()
