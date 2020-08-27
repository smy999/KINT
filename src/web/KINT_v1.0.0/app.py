from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import json
import pandas as pd
from random import *
import xlrd
import math

app = Flask(__name__)


#################################################3

# Test Dataset

# 1.예문
# sentence = "예문 출력 Test입니다."

# 2.감성분석 [0]=긍정, [1]=부정
# sentimental = ["68%", "32%"]

# 3.1. 분야(커뮤니티)별 비율

# 3.1.1. x축 12달
# dataset=[{
#     "label": "Poitics",
#     "data": [randrange(1, 101),
#              randrange(1, 101),
#              randrange(1, 101),
#              randrange(1, 101),
#              randrange(1, 101),
#              randrange(1, 101),
#              randrange(1, 101),
#              randrange(1, 101),
#              randrange(1, 101),
#              randrange(1, 101),
#              randrange(1, 101),
#              randrange(1, 101)
#              ]
# },{
#     "label": "Humor",
#     "data": [randrange(1, 101),
#              randrange(1, 101),
#              randrange(1, 101),
#              randrange(1, 101),
#              randrange(1, 101),
#              randrange(1, 101),
#              randrange(1, 101),
#              randrange(1, 101),
#              randrange(1, 101),
#              randrange(1, 101),
#              randrange(1, 101),
#              randrange(1, 101)
#              ]
# },{
#     "label": "Entertainment",
#     "data": [randrange(1, 101),
#              randrange(1, 101),
#              randrange(1, 101),
#              randrange(1, 101),
#              randrange(1, 101),
#              randrange(1, 101),
#              randrange(1, 101),
#              randrange(1, 101),
#              randrange(1, 101),
#              randrange(1, 101),
#              randrange(1, 101),
#              randrange(1, 101)
#              ]
# },{
#     "label": "News",
#     "data": [randrange(1, 101),
#              randrange(1, 101),
#              randrange(1, 101),
#              randrange(1, 101),
#              randrange(1, 101),
#              randrange(1, 101),
#              randrange(1, 101),
#              randrange(1, 101),
#              randrange(1, 101),
#              randrange(1, 101),
#              randrange(1, 101),
#              randrange(1, 101)
#              ]
# }]

# 3.1.2. x축 6개
dataset={
    "label": "Poitics",
    "data": [randrange(1, 101),
             randrange(1, 101),
             randrange(1, 101),
             randrange(1, 101),
             randrange(1, 101),
             randrange(1, 101),
             randrange(1, 101),
             randrange(1, 101),
             randrange(1, 101),
             randrange(1, 101),
             randrange(1, 101),
             randrange(1, 101)
             ]
}

# 3.2. json 형식으로 변환
jsdata = json.dumps(dataset, indent=4)
print(jsdata)
#4 이달의 신조어
month_term = ["꿀잼", "상상코로나", "가성비", "가즈아", "나일리지"]


#########################################################

# 데이터셋 확인
# print(sentence)
# print(sentimental)
# print(dataset)
# print(jsdata)
print(month_term)

# labels = [_ for _ in dataset.keys()]
# data = [_ for _ in dataset.values()]

# for i in dataset:
#     label.append([_ for _ in i.keys()])
#     data.append([_ for _ in i.values()])

###############################################################################3

# 전역변수

term=""



################################# 감성 분석 #############################################

# 연관 키워드 엑셀 파일 불러오기
sent = pd.read_excel('News_sentiment.xlsx')
print(sent)

sentLen = len(sent)
print(sentLen)

# sentimental = list()
#
# term = "직구족"
#
# for i in range(sentLen):
#     if term == sent['Word'][i]:
#         print('yes')
#         pos = sent['Positive'][i]
#         print(type(pos))
#         pos = math.trunc(pos)
#         print(pos)
#         neg = 100 - pos
#         print(neg)
#         sentimental.append(pos)
#         sentimental.append(neg)
#         break


############################### 연관 키워드 #############################################

# 연관 키워드 엑셀 파일 불러오기
df2 = pd.read_excel('key.xlsx')
# print(df2)

# 신어 목록 출력
# print(df2['key'])

# 신어 개수(= row 수)
dfLen = len(df2)

# 편의를 위해 row와 column 뒤집기
df = df2.transpose()
# print(df)

# Nan 값 오류를 방지하기 위해 0으로 값 변경
df = df.fillna(0)
# print(df)

# print(df.loc['key'])
################################### 메인 페이지 ####################################################

# home page
@app.route('/')
def home():
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
    # 검색 기본 페이지 > search2.html
    render_template('search2.html', month_term=month_term)
    # 현재 실행 위치 출력
    print('search')
    # request 방식 확인 출력
    print(request.method)

    # "POST" 일 때
    if request.method == 'POST':
        # render_template('search2.html', month_term=month_term)

        # 변수 초기화
        result = ""

        # html에서 입력된 검색어 받아오기
        req = request.form.to_dict()
        print(req)
        # 검색어 받아와서 필터링
        term = req['term']
        term = term.replace('#', '')
        term = term.replace('들', '')
        print(term)

        # 검색어에 맞는 연관 키워드 추출
        rel_term = list()
        varbreak = 0
        for i in range(dfLen):
            if term == df[i]['key']:
                varbreak = 0
                print(df[i])
                keyLen = len(df[i])
                print(len(df[i]))
                for j in range(0, keyLen - 1):
                    if df[i][j] == 0:
                        print(j,"is NaN")
                        continue
                    value = tuple(df[i][j].split("'"))
                    print(value)
                    rel_term.append(value[1])
                break
            else:
                varbreak = 1
        print(rel_term)



        # 1. 입력된 검색어가 없을 때 처리방법
        if len(term) == 0:
            # 1-1. 검색어가 없고, 이달의 신조어가 클릭되었을 때
            if 'mon' in req:
                # 선택된 이달의 신조어를 검색어로 변경하고 필터링
                term = req['mon']
                print('mon이 있을 때')
                term = term.replace('#', '')
                term = term.replace('들', '')
                print(term)

                # 바뀐 검색어에 대해 연관 키워드 추출
                rel_term = list()
                varbreak = 0
                for i in range(dfLen):
                    if term == df[i]['key']:
                        varbreak = 0
                        print(df[i])
                        keyLen = len(df[i])
                        print(len(df[i]))
                        for j in range(0, keyLen - 1):
                            if df[i][j] == 0:
                                print(j, "is NaN")
                                continue
                            value = tuple(df[i][j].split("'"))
                            print(value)
                            rel_term.append(value[1])
                        break
                    else:
                        varbreak = 1
                print(rel_term)

                if varbreak == 1:
                    print('검색어에 맞는 결과 없음')
                    return render_template("search2.html", month_term=month_term, result="no", term=term)
                else:
                    print('검색어에 맞는 결과 있음')

                    sentimental = list()
                    for i in range(sentLen):
                        if term == sent['Word'][i]:
                            # 예문 가져오기
                            sentence = sent['Sentence'][i]
                            # 감성 분석 결과 가져오기
                            pos = sent['Positive'][i]
                            pos = math.trunc(pos)
                            neg = 100 - pos
                            sentimental.append(str(pos)+"%")
                            sentimental.append(str(neg)+"%")
                            break

                    return render_template('search.html', sent1=sentimental[0], sent2=sentimental[1], sentence=sentence,
                                           term=term, dataset=dataset, jsdata=jsdata, rel_term=rel_term,
                                           month_term=month_term)



            # 1-2. 검색어도 없고, 이달의 신조어 클릭도 아닐 때 > 그냥 검색 버튼을 누르거나 검색창에서 Enter 눌렀을 때
            else:
                print('mon이 없을 때')
                # 검색어에 맞는 결과가 없을 때 > "검색 결과가 없습니다." 출력
                return render_template("search2.html", month_term=month_term, result="")

        # 2. 입력된 검색어가 있을 때
        # 2-1. 위에서 필더링한 검색어의 결과가 없을 때 > 검색 페이지로 이동(search2.hmtl)
        if varbreak == 1:
            print('검색 결과가 없습니다.')
            return render_template("search2.html", month_term=month_term, result="no", term=term)
        # 2-2. 위에서 필터링한 검색어의 결과가 있을 때 > 결과 페이지로 이동(search.html)
        else:
            print('검색 결과가 있습니다.')

            sentimental = list()
            for i in range(sentLen):
                if term == sent['Word'][i]:
                    # 예문 가져오기
                    sentence = sent['Sentence'][i]
                    # 감성 분석 결과 가져오기
                    pos = sent['Positive'][i]
                    pos = math.trunc(pos)
                    neg = 100 - pos
                    sentimental.append(str(pos)+"%")
                    sentimental.append(str(neg)+"%")
                    break

            return render_template('search.html', sent1=sentimental[0], sent2=sentimental[1], sentence=sentence,
                                   term=term, dataset=dataset, jsdata=jsdata, rel_term=rel_term,
                                   month_term=month_term)


    # # "GET" 일 때
    # if request.method == 'GET':
    #     # term = request.args.get('term0')
    #     req = request.form.to_dict()
    #     print(req)
    #
    #     if len(req) == 0:
    #         return render_template("search2.html")
    #
    #
    #     term = req['term']
    #
    #     if len(term) == 0:
    #         if 'mon' in req:
    #             term = req['mon']
    #         else:
    #             return render_template("search2.html", month_term=month_term)
    #
    #     return render_template('search.html', sent1=sentimental[0], sent2=sentimental[1], sentence=sentence,
    #                            term=term, dataset=dataset, jsdata=jsdata, rel_term=rel_term, month_term=month_term)




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
