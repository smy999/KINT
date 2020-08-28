from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import json
import pandas as pd
from random import *
import xlrd
import math

#######################################################################################

app = Flask(__name__)

################################## 전역 변수 #############################################3

# 각 함수에서 쓰이는 변수 값들 global 선언

# 입력 검색어
term = ""
# 신어 데이터에 검색어가 있는지 없는지 판단할 때 사용되는 flag
varbreak = 0
# 감성분석(긍정, 부정), 예문추출
sens = list()
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
sent = pd.read_excel('News_sentiment.xlsx')
print(sent)

# 신어 개수
sentLen = len(sent)
print(sentLen)

# 함수: 해당 검색어에 대한 정보 추출
def sen(term):
    global sens
    sens = list()
    for i in range(sentLen):
        if term == sent['Word'][i]:
            # 예문 가져오기
            sens.append(sent['Sentence'][i])
            # 감성 분석 결과 가져오기
            pos = sent['Positive'][i]
            pos = math.trunc(pos)
            neg = 100 - pos
            sens.append(str(pos)+"%")
            sens.append(str(neg)+"%")
            break
    return sens

############################### 연관 키워드 #############################################

# 연관 키워드 엑셀 파일 불러오기
df2 = pd.read_excel('key_final.xlsx')

# 신어 개수(= row 수)
dfLen = len(df2)

# 편의를 위해 row와 column 뒤집기
df = df2.transpose()

# Nan 값 오류를 방지하기 위해 0으로 값 변경
df = df.fillna(0)

# 함수: 해당 검색어에 대한 정보 추출
def rel(term):
    global rel_term
    global varbreak
    rel_term = list()
    varbreak = 0
    for i in range(dfLen):
        if term == df[i]['key']:
            varbreak = 0
            keyLen = len(df[i])

            for j in range(0, keyLen - 1):
                if df[i][j] == 0:
                    continue
                value = tuple(df[i][j].split("'"))
                rel_term.append(value[1])
            break
        else:
            varbreak = 1
    return rel_term

################################# 빈도 분석 #############################################

# 빈도 엑셀 파일 불러오기
newsDate = pd.read_excel('News_date.xlsx')
print(newsDate)

# 신어 개수
dateNLen = len(newsDate)

# NaN 값 0으로 변환
newsDate = newsDate.fillna(0)

# 날짜 순으로 정렬
newsDate = newsDate.sort_index(axis=1)

# 컬럼(커뮤니티, 신문사, key) 가져와서 key 빼고 저장: 그래프 labels에 쓰일 데이터
labelDate = list(newsDate.columns)
del labelDate[13]

# 함수: 해당 검색어에 대한 정보 추출
def date(term):
    global dataDate
    dataDate = list()
    for i in range(dateNLen):
        if term == newsDate['key'][i]:
            dataDate = list(newsDate.loc[i])
            del dataDate[13]
            break
    return dataDate

################################# 이달의 KINT #############################################

# 빈도 분석 파일에서 key와 마지막 달 column 가져와서 this_month에 저장
this_month = newsDate[['key', labelDate[-1]]]
print(this_month)

# 마지막 달 컬럼 기준이로 내리차순 정렬 > top5 추출
this_month = this_month.sort_values(by=[labelDate[-1]], ascending=[False])

# 해당 검색어에 대한 정보 추출
month_term = list(this_month['key'].head(5))

################################# 비율 분석 #############################################

# 비율 엑셀 파일 불러오기
newsRef = pd.read_excel('News_ref.xlsx')

# 신어 개수
refNLen = len(newsRef)

# NaN 값 0으로 변환
newsRef = newsRef.fillna(0)

# column(년월) 순 정렬
newsRef = newsRef.sort_index(axis=1)

# 한겨레 : 300, 경향신문 : 301, 매일경제 : 302, 조선일보 : 303, 디지털타임스 : 304, 동아일보 : 305, SBS뉴스 : 306, 한국경제 : 307
labelRef = ["한겨레", "경향신문", "매일경제", "조선일보", "디지털타임스", "동아일보", "SBS뉴스", "한국경제"]

# 함수: 해당 검색어에 대한 정보 추출
def ref(term):
    global dataRef
    dataRef = list()
    for i in range(refNLen):
        if term == newsRef[0][i]:
            for j in range(300, 307):
                dataRef.append(newsRef[j][i]*100)
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

        # 검색어에 맞는 연관 키워드 추출
        rel_term = rel(term)

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

                # 바뀐 검색어에 대해 연관 키워드 추출
                rel_term = rel(term)

                if varbreak == 1:
                    print('검색어에 맞는 결과 없음')
                    return render_template("search2.html", month_term=month_term, result="no", term=term)
                else:
                    print('검색어에 맞는 결과 있음')
                    # 예문 출력, 감성 분석 결과 받아오기
                    sens = sen(term)
                    # 빈도 분석 결과 받아오기
                    dataRef = ref(term)
                    # 커뮤니티, 뉴스별 비율 받아오기
                    dataDate = date(term)
                    # search.html: 검색 결과 보여주기
                    return render_template('search.html', sent1=(str(int(sens[1].replace('%', ''))+10)+'%'), sent2=(str(int(sens[2].replace('%', ''))+10)+'%'), sens=sens,
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
            # 예문 출력, 감성 분석 결과 받아오기
            sens = sen(term)
            # 빈도 분석 결과 받아오기
            dataRef = ref(term)
            # 커뮤니티, 뉴스별 비율 받아오기
            dataDate = date(term)
            # search.html: 검색 결과 보여주기
            return render_template('search.html', sent1=sens[1], sent2=sens[2], sentence=sens[0],
                                   term=term, rel_term=rel_term, labelRef=labelRef, labelDate = labelDate, dateDate = dataDate, dataRef = dataRef)



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
