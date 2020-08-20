from flask import Flask, render_template, request
import sqlite3
import json
import pandas as pd
from random import *

app = Flask(__name__)


#################################################3

# Test Dataset

# 1.예문
sentence = "예문 출력 Test입니다."

# 2.감성분석 [0]=긍정, [1]=부정
sentimental = ["68%", "32%"]

# 3.1. 분야(커뮤니티)별 비율
dataset=[{
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
},{
    "label": "Humor",
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
},{
    "label": "Entertainment",
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
},{
    "label": "News",
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
}]
# 3.2. json 형식으로 변환
jsdata = json.dumps(dataset, indent=4)


#########################################################

# 데이터셋 확인
print(sentence)
print(sentimental)
print(dataset)
print(jsdata)

# labels = [_ for _ in dataset.keys()]
# data = [_ for _ in dataset.values()]

# for i in dataset:
#     label.append([_ for _ in i.keys()])
#     data.append([_ for _ in i.values()])

###############################################################################3

# 전역변수

term=""



#######################################################################################
# 메인 페이지: home
@app.route('/')
def home():
    # 디비 값 받아오기 연습
    # conn = sqlite3.connect('HP.db')
    # cur = conn.cursor()
    # cur.execute("select * from Head where pk=15")
    # df = pd.read_sql_query("select * from Head where pk < 10", conn)
    # result = df.fetchall()
    # print(type(df))
    # print(df)

    # 엑셀 값 받아오기 연습
    # df2 = pd.read_excel('origin.xlsx')
    # print(df2['index'])

    return render_template("home.html")


#######################################################################################
# home 페이지에서 검색할 때
@app.route('/', methods=['POST', 'GET'])
def search1():
    # 기본 페이지: home
    render_template('home.html')

    if request.method == 'POST':
        # html에서 입력된 용어 받아오기
        req = request.form.to_dict()
        term = req['term']

        # 파이썬 상에서 인자 출력 test
        print("search1: "+term)
        print("search1: "+sentimental[0], sentimental[1])
        print("search1: "+sentence)
        return render_template('search.html', sent1=sentimental[0], sent2=sentimental[1], sentence=sentence, term=term, dataset=dataset, jsdata=jsdata)

#######################################################################################
# search 페이지에서 검색할 때
# search >> search
@app.route('/search', methods=['POST', 'GET'])
def search2():
    # 기본 페이지: search
    render_template('search.html')

    if request.method == 'POST':
        # html에서 입력된 용어 받아오기
        req = request.form.to_dict()
        # 입력된 용어 term에 저장
        term = req['term']

        # 파이썬 상에서 인자 출력 test
        print("search2: "+term)
        print("search2: "+sentimental[0], sentimental[1])
        print("search2: "+sentence)

        # 위의 결과를 인자로 포함하여 search 페이지 렌더링
        return render_template('search.html', sent1=sentimental[0], sent2=sentimental[1], sentence=sentence, term=term, dataset=dataset, jsdata=jsdata)


######################################################################################
# 실행
if __name__ == '__main__':
    app.run()
