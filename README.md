# KINT(Korean Internet New Terms) :kr:

### 한국 인터넷 신어 API  

:school: 고려대학교 빅데이터 캠퍼스 프로젝트

:date: 프로젝트 일정: 2020년 7월 6일 ~ 2020년 8월 31일

:smiley: 프로젝트 팀원: 김윤기, 서민영, 유주연, 조정현

이 서비스는 웹 사이트에서 제공되며 사용자가 많은 커뮤니티 사이트들에서 새롭게 감지된 상위 5개의 새로운 단어 및 새로운 단어의 감성 분석 결과뿐만 아니라 새로운 단어에 대한 예제 문장을 제공합니다.

이를 통해 KINT는 새로운 단어 정보를 API로 제공함으로써 새로운 단어를 해석하는 데 어려움이 있는 자연어 처리 분야, 언어학 분야, 사회 및 공공 분야에 기여하는 것을 목표로 합니다.

이 프로젝트는 새로 생성된 단어를 감지하고 이를 사전에 자동으로 업데이트하는 작업을 진행합니다.

이를 위해 첫 번째 모델은 새로 만들어진 단어를 감지하고 두 번째 모델은 단어에 대한 감성 분석 및 예문을 추출하는 것으로 총 2가지 모델을 구축합니다.  

# 진행         
다음은 프로젝트의 자동화 시스템 구성도입니다.
![system](https://user-images.githubusercontent.com/68207910/91655449-8652aa00-eaeb-11ea-8b4e-d28d9325c1b4.png)

## Model 1. 신어 감지 및 자동 분류 

![model1](https://user-images.githubusercontent.com/68207910/91655468-ad10e080-eaeb-11ea-8f1d-514d88c721d8.png)

1. 데이터 수집 단계
    - 분야별 커뮤니티에서 웹 크롤러를 통해 데이터를 수집합니다.
    - 이 크롤러는 제목 텍스트 데이터 및 날짜 / 시간 데이터를 수집합니다.
    - 유머 크롤러
      - natepan : 10대 이야기, 20대 이야기, 톡커들의 선택 명예의 전당 (일별)
      - 오늘의 유머 : 베오베, 베스트 게시물
      - ilbe : 일베-일간 베스트
      - dcinside : 야구 갤러리
      - ppomppu : 자유 게시판
    - 정치 크롤러
      - 일베 : 정치 / 시사 게시판
      - 보배드림 : 정치 커뮤니티
    - 엔터테인먼트 크롤러
      - dcinside : 인터넷방송 갤러리, 남자/여자 연예인 갤러리
      - instize : 이슈
    - 뉴스 크롤러
      - 한겨레
      - 경향신문
      - 매일경제
      - 조선일보
      - 디지털타임스
      - 동아일보
      - SBS뉴스
      - 한국경제
    
    
2. 텍스트 데이터 전처리 단계
    - soynlp 라이브러리를 사용하여 용어를 추출합니다.
    - 나온 용어를 국립국어원 전자사전에 검색합니다.
    - 국립국어원 전자사전에 없는 경우 다음 단계에서 사용됩니다.
    - 국립국어원 전자사전에 있는 경우 신어가 아닌 것으로 판단합니다.  

3. 신어 감지 단계
	- 종속변수: 신어 여부
	
	- 독립변수 
	
	  ![Independent Variable](https://user-images.githubusercontent.com/68207910/91655727-cfa3f900-eaed-11ea-8525-9e64320431bd.png)
	
	- 위 종속변수, 독립변수를 학습된 분류 모델에 넣어 신어 여부 파악합니다.  

4. 1,2,3 단계를 반복적으로 적용합니다.  

## Model 2. 신어 분석 모델

![model2](https://user-images.githubusercontent.com/68207910/91655472-aedaa400-eaeb-11ea-8aaf-fc6e6b351b05.png)

1. 텍스트 데이터 불러오기
   - Model 1에서 감지된 신어가 포함된 텍스트 데이터를 불러옵니다.

2. 텍스트 데이터 전처리 단계
   - 텍스트 데이터를 벡터화하여 표현합니다.

3. 감성 분석 및 예문 출력 단계
   - 신어 감성 분석 API (신어 감성 분석 모델)는 Point Mutual Information (PMI) 을 기반으로 신어에 대한 감성을 분석하며  관련 키워드를 추출합니다.
   - 신어 예문추출 API(신어 예문 추출 모델)는 Bidirectional GRU을 통해 예문을 추출하고, N-grame을 활용하여 추출된 예문의 띄어쓰기를 적용합니다. 

        
       
       
       
-------------------------------------------
         
	 
	 
	                                                                  
# KINT(Korean Internet New Terms) :us:


### Korean Internet New Terms API  

Korea Univ Bigdata Campus Project  

This service provides the top 5-newly detected internet terms, sentiment analysis of newly detected internet terms, and example sentence of newly detected internet terms on the website.  

Through this, KINT aims to contribute to Natural Language Processing, Linguistics, Social and Public sectors that have difficulty interpreting new internet terms by providing new internet terms information through API.  


This project automatically detects new internet terms and updates this in our dictionary.  

              
For this, the 1st Model detects new internet terms, and the 2nd Model extracts sentiment analysis result of them and example sentence of them.  

# Progress   
![system](https://user-images.githubusercontent.com/68207910/91655449-8652aa00-eaeb-11ea-8b4e-d28d9325c1b4.png)

## Model 1. New internet terms detection and automatic classification model  

![model1](https://user-images.githubusercontent.com/68207910/91655468-ad10e080-eaeb-11ea-8f1d-514d88c721d8.png)

1. Data collecting Step
    - Web crawlers collect data at each sector community
    - These crawlers collect head data, DateTime data
    - Humor Crawler
      - natepan : 10 대 이야기, 20 대 이야기, 톡커들의 선택 명예의 전당 (일별)
      - 오늘의 유머 : 베오베, 베스트 게시물
      - ilbe : 일베-일간 베스트
      - dcinside : 야구 갤러리
      - ppomppu : 자유 게시판
    - Politic Crawler
      - 일베 : 정치 / 시사게시판
      - 보배드림 : 정치커뮤니티
    - Entertainment Crawler
      - dcinside : 인터넷방송 갤러리, 남자/여자연예인 갤러리
      - instize : 이슈 
    - News Crawler
      - 한겨레
      - 경향신문
      - 매일경제
      - 조선일보
      - 디지털타임스
      - 동아일보
      - SBS뉴스
      - 한국경제
    
2. Text data preprocessing step
    - We use the soynlp library to extract terms.
    - Extract terms are searched in the electronic dictionary of the National Institute of Korean Language.
    - If not in the electronic dictionary of the National Institute of Korean Language, it will be used in the next step.
    - If it is in the electronic dictionary of the National Institute of Korean Language, it is judged that it is not a new internet term.  

3. New internet word detecting step
  - Dependent Variable: Whether it is a new internet term
	- Independent Variable
		![Independent Variable](https://user-images.githubusercontent.com/68207910/91655728-d2065300-eaed-11ea-8a38-7bb352dcf772.png)
		
  - Put the above dependent and independent variables into the learned classification model to determine whether it is a new internet term or not  

4. We apply step 1,2,3 repeatedly.  

## Model 2. New Internet terms analysis Model

![model2](https://user-images.githubusercontent.com/68207910/91655472-aedaa400-eaeb-11ea-8aaf-fc6e6b351b05.png)

1. Text data loading step
   - We load the text data containing the new internet terms detected in Model 1.

2. Text data preprocessing step
   - Text data vectorize.

3. Sentiment analysis and example sentence extracting step
   - The New Internet Terms Sensitivity Analysis API (New Internet Terms Sensitivity Analysis Model) analyzes the sensitivity of new internet terms based on Point Mutual Information (PMI) and extracts related keywords.

   - The New Internet Terms sample extraction API (New Internet Terms sample extraction model) extracts the sample through the Bidirectional GRU and applies the spacing of the extracted sample using N-Gram.


                                                                                                              
-----------------------------------------------------ㅇ
                                                                                  
# API

1. soynlp
   - https://github.com/lovit/soynlp.git
2. 국립국어원 전자사전
   - https://www.korean.go.kr/front/onlineQna/onlineQnaView.do?mn_id=216&qna_seq=10073

# Contribute

- smy999 210112yynim@naver.com
- wtt5857 wtt5857@naver.com
- yujuyeon0511 juyeon.yu0511@gmail.com
- Kimyungi gozj3319@naver.com


