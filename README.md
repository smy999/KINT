# KITS(Korean Internet Term Search)  

### 한국 인터넷 신어 API  

고려 대학교 빅데이터 캠퍼스 프로젝트  

이 서비스는 웹 사이트에서 제공되며 사용자가 많은 커뮤니티 사이트들에서 새롭게 감지된 상위 5개의 새로운 단어 및 새로운 단어의 감성 분석 결과뿐만 아니라 새로운 단어에 대한 예제 문장을 제공합니다.  

이를 통해 KITS은 새로운 단어 정보를 API로 제공함으로써 새로운 단어를 해석하는 데 어려움이 있는 자연어 처리 분야, 언어학 분야, 사회 및 공공 분야에 기여하는 것을 목표로 합니다.  

이 프로젝트는 새로 생성된 단어를 감지하고 이를 사전에 자동으로 업데이트하는 작업을 진행합니다.  

이를 위해 첫 번째 모델은 새로 만들어진 단어를 감지하고 두 번째 모델은 단어에 대한 감성분석 및 예제를 추출하는 것으로 총 2 가지 모델을 구축합니다.  

# 진행             
![system](https://user-images.githubusercontent.com/33407191/89900519-cf1aef80-dc1e-11ea-97ab-e201765e17ca.png)

## Model 1. 신어 감지 및 자동 분류 

![model1](https://user-images.githubusercontent.com/33407191/89895976-a17e7800-dc17-11ea-8713-4733b2706b84.png)

1. 데이터 수집 단계
    - 각 분야별 커뮤니티에서 웹 크롤러를 통해 데이터를 수집합니다.
    - 이 크롤러는 제목 텍스트 데이터 및 날짜 / 시간 데이터를 수집합니다.
    - 유머 크롤러
      - natepan : 10 대 이야기, 20 대 이야기, 톡커들의 선택 명예의 전당 (일별)
    	- 오늘 유머 : 베오베, 베스트 게시물
	    - ilbe : 일베-일간 베스트
      - dcinside : 야구 갤러리
      - ppomppu : 자유 게시판
    - 정치 크롤러
      - 일베 (정치 / 시사)
      - 보배 드림 (정치)
    - 엔터테인먼트 크롤러
      - dcinside : 인터넷방송 갤러리, 남자/여자연예인 갤러
      - instize : 이슈  
    
2. 텍스트 데이터 전처리 단계
    - soynlp 라이브러리를 사용하여 용어를 추출합니다.
    - 나온 용어를 국립국어원 전자사전에 검색합니다.
    - 국립국어원 전자사전에 없는 경우 다음 단계에서 사용됩니다.
    - 국립국어원 전자사전에 있는 경우 신어가 아닌 것으로 판단합니다.  

3. 신어 감지 단계
	- 종속변수: 신어여부
	- 독립변수
		- left_frequency
		- right_frequency
		- cohesion_forward
		- cohesion_backward
		- left_accessor_variety
		- right_accessor_variety
		- left_branching_entropy
		- right_branching_entropy
		- right_post_postion_ratio
		- right_whitespace_ratio
	- 위 종속변수, 독립변수를 학습된 분류 모델에 넣어 신어 여부 파악합니다.  

4. 1,2,3 단계를 반복적으로 적용합니다.  

## Model 2. 신어 분석 모델

![model2](https://user-images.githubusercontent.com/33407191/89896074-c8d54500-dc17-11ea-8867-98776b2b3011.png)

1. 텍스트 데이터 불러오기
  - Model 1에서 감지된 신어가 포함된 텍스트 데이터를 불러옵니다.

2. 텍스트 데이터 전처리 단계
   - 텍스트 데이터를 벡터화하여 표현합니다.

3. 감성분석 및 예문 출력 단계
   - 감성분석을 위해 준지도학습과 LSTM Model을 사용합니다.
   - 예문 출력을 위해 N-gram과 BPE을 사용합니다.         
       
       
       
-------------------------------------------
         
	 
	 
	                                                                  
# KITS(Korean Internet Term Search)  


### Korean Internet Term API  

Korea Univ Bigdata Campus Project  

This service provide top 5-newly detected internet terms, sentiment analysis of newly detected internet terms and example sentence of newly detected internet terms in the website.  

Through this, KITS aims to contribute to Natural Language Processing, Linguistics, Social and Public sectors that have difficulty interpreting new internet terms by providing new internet terms information through API.  


This project automatically detect new internet terms and update this in our dictionary.  

              
For this, 1st Model detect new internet terms and 2nd Model extract sentiment analysis of them and example sentence of them.  

# Progress   
![system](https://user-images.githubusercontent.com/33407191/89900519-cf1aef80-dc1e-11ea-97ab-e201765e17ca.png)

## Model 1. New internet terms detection and automatic classfication model  

![model1](https://user-images.githubusercontent.com/33407191/89895976-a17e7800-dc17-11ea-8713-4733b2706b84.png)

1. Data collecting Step
    - 각 분야별 커뮤니티에서 웹 크롤러를 통해 데이터를 수집합니다.
    - Web crawlers collect data at each sector community
    - 이 크롤러는 제목 텍스트 데이터 및 날짜 / 시간 데이터를 수집합니다.
    - This crawlers collect head data, datetime data
    - Humor Crawler
      - natepan : 10 대 이야기, 20 대 이야기, 톡커들의 선택 명예의 전당 (일별)
    	- 오늘 유머 : 베오베, 베스트 게시물
	    - ilbe : 일베-일간 베스트
      - dcinside : 야구 갤러리
      - ppomppu : 자유 게시판
    - Politic Crawler
      - 일베 (정치 / 시사)
      - 보배 드림 (정치)
    - Entertainment Crawler
      - dcinside : 인터넷방송 갤러리, 남자/여자연예인 갤러리
      - instize : 이슈  
    
2. Text data preprocessing step
    - We use the soynlp library to extract terms.
    - Extract terms are searched in the electronic dictionary of the National Institute of Korean Language.
    - If not in electronic dictionary of the National Institute of Korean Language, it will be used in the next step.
    - If it is in the electronic dictionary of the National Institute of Korean Language, it is judged that it is not a new internet term.  

3. New internet word detecting step
  - Dependent Variable : Whether it is a new internet term
	- Independent Variable
		- left_frequency
		- right_frequency
		- cohesion_forward
		- cohesion_backward
		- left_accessor_variety
		- right_accessor_variety
		- left_branching_entropy
		- right_branching_entropy
		- right_post_postion_ratio
		- right_whitespace_ratio
  - Put the above dependent and independent variables into the learned classification model to determine whether it is a new internet term or not  

4. We apply step 1,2,3 repeatedly.  

## Model 2. New Internet terms analysis Model

![model2](https://user-images.githubusercontent.com/33407191/89896074-c8d54500-dc17-11ea-8867-98776b2b3011.png)

1. Text data loading step
  - We loads the text data containing the new internet terms detected in Model 1.

2. Text data preprocessing step
   - Text data vectorize.

3. Sentiment analysis and example sentence extracting step
   - We use semi-supervised learning and LSTM Model for sentiment analysis
   - We use N-gram and Byte Pair Encoding (BPE) for extracting of example sentence  



                                                                                                              
-----------------------------------------------------

                                                                                  
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


