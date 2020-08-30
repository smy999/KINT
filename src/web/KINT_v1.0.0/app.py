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



################################## 신어 DB 확인 #############################################

# word_pd = pd.read_excel('word.xlsx')
# print(word_pd)
#
# # 신어 개수
# wordLen = len(word_pd)
# print(wordLen)
#
# # 함수: 검색어가 신어 DB에 있는지 확인
# def word_func(term):
#     global varbreak
#     varbreak = 0
#     print(word_pd['Word'])
#     for i in range(wordLen):
#         if term in word_pd['Word']:
#             varbreak = 0
#             break
#         else:
#             varbreak = 1

################################# 감성 분석 #############################################

# 감성 분석 엑셀 파일 불러오기
sent_pd = pd.read_excel('sentiment_final.xlsx')
print(sent_pd)

# 신어 개수
sentLen = len(sent_pd)
print(sentLen)

# 함수: 해당 검색어에 대한 정보 추출
def sent_func(term):
    global sens
    sens = list()
    for i in range(sentLen):
        if term == sent_pd['Word'][i]:
            # 예문 가져오기
            # sens.append(sent['Sentence'][i])
            # 감성 분석 결과 가져오기
            pos = sent_pd['Positive'][i]
            pos = math.trunc(pos)
            neg = 100 - pos
            sens.append(str(pos)+"%")
            sens.append(str(neg)+"%")
            break
    print(sens)
    return sens


################################# 예문 출력 #############################################

# 감성 분석 엑셀 파일 불러오기
exam_pd = pd.read_excel('News_example.xlsx')
print(exam_pd)

# 신어 개수
examLen = len(exam_pd)
print(examLen)


# 함수: 해당 검색어에 대한 정보 추출
def exam_func(term):
    global exams
    exams = ""
    for i in range(sentLen):
        if term == exam_pd['Word'][i]:
            # 예문 가져오기
            exams = exam_pd[0][i]
            # 감성 분석 결과 가져오기
            break
    print(exams)
    return exams


############################### 연관 키워드 #############################################
print("############################### 연관 키워드 #############################################")
# 연관 키워드 엑셀 파일 불러오기
newsK = pd.read_excel('News_key.xlsx')
commK = pd.read_excel('key.xlsx')
key_pd = pd
key_pd = pd.concat([newsK, commK])
print(key_pd)

# 신어 개수(= row 수)
key_Len = len(key_pd)
print(key_Len)

key_pd = key_pd.rename({'Unnamed: 0': 'word'}, axis=1)
print(key_pd)

key_pd = key_pd.sort_values(by='word', axis=0, ascending=True)
print(key_pd)
key_pd = key_pd.reset_index(drop=True)
print(key_pd)
# 편의를 위해 row와 column 뒤집기
# key_pd = key_pd.transpose()
# print(key_pd)

# Nan 값 오류를 방지하기 위해 0으로 값 변경
key_pd = key_pd.fillna(0)
print(key_pd)

# 함수: 해당 검색어에 대한 정보 추출

rel_term = list()

tempK = key_pd[key_pd['word'].duplicated()]
print(tempK)

for i in range(key_Len):
    rel_dict = dict()

    if i+1 in tempK.index:
        continue
    if i in tempK.index:
        tempKK = list()

        # 중복 키워드 받아오기
        tempKK.append(key_pd.loc[i]['word'])
        print(tempKK)

        keyLen1 = len(key_pd.loc[i])
        print(keyLen1)

        for j in range(keyLen1 - 1):
            if key_pd.loc[i][j] == 0:
                continue
            value = tuple(key_pd.loc[i][j].split("'"))
            value2 = tuple(value[2].split(","))
            value2 = tuple(value2[1].split(")"))
            value2 = tuple(value2[0].split(" "))

            rel_dict[value[1]] = value2[1]
        print(rel_dict)

        keyLen2 = len(key_pd.loc[i-1])
        print(keyLen2)
        for j in range(keyLen2 - 1):
            if key_pd.loc[i-1][j] == 0:
                continue
            value = tuple(key_pd.loc[i-1][j].split("'"))
            value2 = tuple(value[2].split(","))
            value2 = tuple(value2[1].split(")"))
            value2 = tuple(value2[0].split(" "))

            rel_dict[value[1]]= value2[1]
        print(rel_dict)
        rel_list=list()
        rel_list = sorted(rel_dict.items(), key = lambda x:x[1], reverse=True)
        print(rel_list)

        print(tempKK)
        for k in range(keyLen1+keyLen2):
            tempKK.append(rel_list[k][0])
            if k == 4:
                break
        print(tempKK)
        print()
        key_pd.drop(i, inplace=True)
        key_pd.drop(i - 1, inplace=True)

        # 중복 검색어 빈도합 추가
        key_pd.loc[i] = tempKK
        print(key_pd)

    else:
        tempKK = list()

        # 중복 키워드 받아오기
        tempKK.append(key_pd.loc[i]['word'])
        print(tempKK)

        keyLen = len(key_pd.loc[i])
        print(keyLen)

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
        print(tempKK)
        key_pd.drop(i, inplace=True)
        key_pd.loc[i] = tempKK
        print(key_pd)



# 함수: 해당 검색어에 대한 정보 추출
def rel_func(term):
    global rel_term
    global varbreak
    rel_term = list()
    varbreak = 0
    for i in range(key_Len):
        if term == key_pd.iloc[i]['word']:
            varbreak = 0
            print(key_pd.iloc[i])
            keyLen = len(key_pd.iloc[i])
            for j in range(0, keyLen - 1):
                if key_pd.loc[i][j] == 0:
                    continue
                rel_term.append(key_pd.iloc[i][j])
            print(rel_term)
            break
        else:
            varbreak = 1
    return rel_term

################################# 빈도 분석 #############################################

# 빈도 엑셀 파일 불러오기
# date_pd = pd.read_excel('News_date.xlsx')
# print(date_pd)

newsD = pd.read_excel("News_date.xlsx")
print("newsD")
print(newsD)

wordD2 = pd.read_excel("word2_date.xlsx")
print("wordD2")
print(wordD2)

wordD4 = pd.read_excel("word4_date.xlsx")
# print("wordD4")
# print(wordD4)

finalD = pd.concat([newsD, newsD, wordD2, wordD4])
print("finalM")

print(finalD["Unnamed: 0"])
finalD = finalD.rename({'Unnamed: 0': '0'}, axis=1)
# print(finalD)

finalD = finalD.fillna(0)
# print(finalD)

labelD = list(finalD.columns)
labelD = sorted(labelD)
# print(labelD)

finalD = finalD[labelD]
# print(finalD)

# finalD = finalD.rename({'0': 'key'}, axis=1)
# print(finalD)


del labelD[0]
print(labelD)
print(len(labelD))


# finalD.sort_values(by='word', ascending=True)
print("합치고 정렬")
finalD = finalD.sort_values(by='0', axis=0, ascending=True)
print(finalD)

finalD = finalD.reset_index(drop=True)
print(finalD)


# 중족 데이터 받아오기
tempD = finalD[finalD['0'].duplicated()]
# print(tempD)
# print(tempD['0'])

for i in tempD.index:
    tempDD = list()

    # 중복 키워드 받아오기
    tempDD.append(finalD.loc[i]['0'])
    # print(tempDD)
    # 중복 빈도수 더하기
    for j in labelD:
        tempDD.append(finalD.loc[i][j]+finalD.loc[i-1][j])
    # print(tempDD)

    # 기존 데이터 삭제
    finalD.drop(i, inplace=True)
    finalD.drop(i-1, inplace=True)

    # 중복 검색어 빈도합 추가
    finalD.loc[i]=tempDD
    # print(finalD)


#------------------------------------------
date_pd = pd
date_pd = finalD

# 신어 개수
dateLen = len(date_pd)

# NaN 값 0으로 변환
# date_pd = date_pd.fillna(0)

# 날짜 순으로 정렬
# date_pd = date_pd.sort_index(axis=1)

# 컬럼(커뮤니티, 신문사, key) 가져와서 key 빼고 저장: 그래프 labels에 쓰일 데이터
labelDate = list(date_pd.columns)
del labelDate[0]


def date_func(term):
    global dataDate
    dataDate = list()
    print(date_pd)
    for i in range(dateLen):
        print('for')
        # print(date_pd['0'][i])
        if term == date_pd.iloc[i]['0']:
            dataDate = list(date_pd.iloc[i])
            print(dataDate)
            del dataDate[0]
            break
    return dataDate

################################# 이달의 KINT #############################################

# 빈도 분석 파일에서 key와 마지막 달 column 가져와서 this_month에 저장
# this_month = finalD[['0', labelDate[-1]]]
# print(this_month)

# 마지막 달 컬럼 기준이로 내리차순 정렬 > top5 추출
# this_month = this_month.sort_values(by=[labelDate[-1]], ascending=[False])

# 해당 검색어에 대한 정보 추출
# month_term = list(this_month['0'].head(5))


newsM = pd.read_excel("News_month.xlsx")
# print("newsM")
# print(newsM)

word2 = pd.read_excel("word2_month.xlsx")
# print("word2")
# print(word2)

word4 = pd.read_excel("word4_month.xlsx")
# print("word4")
# print(word4)

finalM = pd.concat([newsM, newsM, word2, word4])
# print("finalM")
# print(finalM["Unnamed: 0"])
finalM = finalM.rename({'Unnamed: 0': 1}, axis=1)
print(finalM)

labelM = list(finalM.columns)
print(labelM)
del labelM[0]

finalM = finalM.fillna(0)
print(finalM)

# 여기에 이달의 신조어 중복되는 것들 그냥 값만 더하면 된다.
print("합치고 정렬")
finalM = finalM.sort_values(by=1, axis=0, ascending=True)
print(finalM)

finalM = finalM.reset_index(drop=True)
print(finalM)


# 중족 데이터 받아오기
tempM = finalM[finalM[1].duplicated()]
print(tempM)
print(tempM[1])


for i in tempM.index:
    tempMM = list()

    # 중복 키워드 받아오기
    tempMM.append(finalM.loc[i][1])
    # 중복 빈도수 더하기
    for j in labelM:
        tempMM.append(finalM.loc[i][j]+finalM.loc[i-1][j])
    # print(tempMM)

    # 기존 데이터 삭제
    finalM.drop(i, inplace=True)
    finalM.drop(i-1, inplace=True)

    # 중복 검색어 빈도합 추가
    finalM.loc[i]=tempMM
    # print(finalM)

# 내림차순 정렬
finalM = finalM.sort_values(by=0, axis=0, ascending=False)
# print(finalM)
# top5 추출
month_term = list(finalM[1].head(5))
# print(month_term)

################################# 비율 분석 #############################################

# 비율 엑셀 파일 불러오기
ref_pd = pd.read_excel('News_ref.xlsx')

# 신어 개수
refLen = len(ref_pd)

# NaN 값 0으로 변환
ref_pd = ref_pd.fillna(0)

# column(년월) 순 정렬
ref_pd = ref_pd.sort_index(axis=1)

# 한겨레 : 300, 경향신문 : 301, 매일경제 : 302, 조선일보 : 303, 디지털타임스 : 304, 동아일보 : 305, SBS뉴스 : 306, 한국경제 : 307
labelRef = ["한겨레", "경향신문", "매일경제", "조선일보", "디지털타임스", "동아일보", "SBS뉴스", "한국경제"]

# 함수: 해당 검색어에 대한 정보 추출
def ref_func(term):
    global dataRef
    dataRef = list()
    for i in range(refLen):
        if term == ref_pd[0][i]:
            for j in range(300, 307):
                dataRef.append(ref_pd[j][i]*100)
            break
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

    # 디비 값 받아오기 연습
    # conn = sqlite3.connect('HP.db')
    # cur = conn.cursor()
    # cur.execute("select * from Head where pk=15")
    # df = pd.read_sql_query("select * from Head where pk < 10", conn)
    # result = df.fetchall()
    # print(type(df))
    # print(df)

    # home.html 렌더링
    return render_template("home.html", month_term=month_term)


################################ 검색 페이지 ##################################################

# search
@app.route('/', methods=['POST', 'GET'])
def search():
    global month_term
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
        print(term)

        # word_func(term)

        # 검색어에 맞는 연관 키워드 추출
        rel_term = rel_func(term)

        # 1. 입력된 검색어가 없을 때 처리방법
        if len(term) == 0:
            # 1-1. 검색어가 없고, 이달의 신조어가 클릭되었을 때
            if 'mon' in req:
                # 선택된 이달의 신조어를 검색어로 변경하고 필터링
                term = req['mon']
                print('선택된 이달의 신조어(mon)가 있을 때')
                term = term.replace('#', '')
                term = term.replace('들', '')
                print(term)

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



##################################### 에러 핸들링 ################################################

# @app.errorhandler(500)
# def page_not_found(error):
#     return redirect('/search2')
#
#
# @app.errorhandler(404)
# def page_not_found1(error):
#     return redirect('/search2')


############################### 실행 #######################################################

if __name__ == '__main__':
    app.run()
