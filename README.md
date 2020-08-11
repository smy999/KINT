# KITS(Korean Internet Term Search)

### 한국 인터넷 신어 API

고려 대학교 빅데이터 캠퍼스 프로젝트

이 서비스는 웹 사이트에서 제공되며 사용자가 많은 커뮤니티 사이트의 빈도, 새로 검색된 상위 5개의 새로운 단어 및 새로운 단어의 감성 분석 결과뿐만 아니라 새로운 단어에 대한 해석 및 예제 문장을 제공합니다.

이를 통해 KITS은 새로운 단어 정보를 API로 제공함으로써 새로운 단어를 해석하는 데 어려움이 있는 언어학 분야, 사회 및 공공 분야에 기여하는 것을 목표로 합니다.

이 프로젝트의 목적은 새로 작성된 단어 사전을 작성하고 자동으로 업데이트하는 것입니다.

이를 위해 첫 번째 모델은 새로 만들어진 단어를 감지하고 두 번째 모델은 단어의 사회적 의미를 추출하는 것으로 총 2 가지 모델을 구축합니다.               

# 진행

이 프로젝트는 두 가지 모델로 구성됩니다.                

## Model 1. 새로 만들어진 단어 감지 모델

1. 데이터 수집 단계
    - 각 부문마다 웹 크롤러를 사용합니다.
    - 이 크롤러는 헤드 텍스트 데이터 및 날짜 / 시간 데이터를 수집합니다.
    - 유머 크롤러 : natepan (10 대 이야기, 20 대 이야기, 톡커들의 선택 명예의 전당 (일별)), 오늘 유머 (베오베, 베스트 게시물), ilbe (일베-지역 베스트), dcinside (야구 갤러리), ppomppu (자유 게시판)
    - 정치 크롤러 : 일베 (정치 / 시사), 보배 드림 (정치), 네이버 (뉴스)
    - 엔터테인먼트 크롤러 : dcinside (인방 갤러, 연예인), instize (이슈), 맘스 홀릭 베이비 (자유 수다방), 네이버 (뉴스)
    
2. 텍스트 데이터 전처리 단계
    - 우리는 soynlp 라이브러리를 사용하여 단어를 추출 할 수 있습니다.
    - 그런 다음 표준 한국어 사전을 검색합니다.
    - 표준 한국어 사전에없는 경우 다음 단계 (1)에서 사용됩니다.
    - 다음 단계 (2)에서 사용됩니다.

3. 모델 구축 단계
    
    - (1) 표준 한국어 사전에 없음
    	-  신어/신어가아님 라벨링 실시
	- 종속변수: 신어여부, 독립변수 : left_frequency, right_frequency, cohesion_forward,  cohesion_backward, left_accessor_variety, right_accessor_variety, left_branching_entropy, right_branching_entropy, 9. right_post_postion_ratio, ight_whitespace_ratio
	- 위 종속변수, 독립변수를 사용하여 로지스틱 회귀분석을 실시하여 분류모델 생성
	- 분류 모델을 활용한 
	
    - (2) 표준 한국어 사전에 있음
       - 신어가 아닌 것으로 

4. 1,2,3 단계를 반복적으로 적용합니다.

## Model 2. 사회적 의미 추출 모델

1. 데이터 수집 단계
   - Google 크롤러는 각 commnuity에서 단어를 검색하고 머리, 몸, 의견, 날짜 시간을 수집합니다.

2. 텍스트 데이터 전처리
   - 텍스트 데이터를 정규화하고 해당 단어로 형태소를 분석 할 수 있습니다.
   - c.f) 우리의 단어 사전은 새로 발견 된 단어들로 구성되어 있습니다.

3. 모델 구축 단계
   - 우리는 단어의 사회적 의미를 추출하기 위해주의 기술을 적용합니다.    
       
       
       
       
-------------------------------------------
         
	 
	 
	                                                                  
# Amanbo Sinsa

Korea Univ. Bigdata campus project

This service is provided on the website and provides interpretations and example sentences for new words, as well as the frequency of famous community sites, the top 5 newly detected new words, and emotional analysis results of the new words.

Through this, Amanbo Shrine aims to contribute the linguistic, social, and public fields that have difficulties in interpreting the new word by providing new word information as an API.

The purpose of this project is to create a newly created dictionary of words and automatically update them.

To do this, we build 2 model that first model is detecting newly coined word and second model is extracting social meaning of the word.

# Progress

This project consists of two models:     

## Mode 1. Newly Coined Word Detecting Model

1. Data collecting step
    - we uses web crawlers for each sector.
    - This crawlers collect head text data and datetime data.  
    	- Humor Crawler : natepan (10대이야기, 20대이야기, 톡커들의 선택 명예의 전당 (일별)), todayhumor (베오베, 베스트게시물), ilbe (일베-일간베스트), dcinside (야구갤러리)
    	- politic Crawler : ilbe (정치/시사), 보배드림 (정치), naver (뉴스)
    	- Entertainment Crawler : dcinside (인방갤, 연예인), instize (이슈), naver (뉴스)
    	- Mom Crawler : 맘스홀릭 베이비 (자유수다방)
	- shopping Crawler: ppomppu (자유게시판)
    
2. Text data preprocessing step
    - We may use soynlp library to extract words.
    - And then, they are searched Standard Korean Language Dictionary.
    - If they are not in Standard Korean Language Dictionary, they are used at next step (1).
    - Othewise, they are used at next step (2).

3. Model building step
    - (1)  Not in Standard Korean Language Dictionary
    	- we will apply word2vector to vectorize word data.
    	- Then, we calculate similarity between word data.
    	- If newly coined word have highly similarity, we apply clustering technique to word data.
    	- Otherwise, we apply classficiation technique to word data.
	
    - (2)  In Standard Korean Language Dictionary
    	- we analyze time-series data to find newly coined word.

4. We apply step 1,2,3 repeatedly.

## Model 2. Socical Meaning Extracting Model

1. Data collecting step
   - Our crawlers search a word in each commnuity and collect head, body, comment, datetime.

2. Text data preprocessing
   - we may nomalize text data and analyze morpheme with corresponding word.
   - c.f) our word dictionary consists of detected newly coined words.

3. Model building step
   - we apply attention technique to extract social meaning of the word.



                                                                                                              
-----------------------------------------------------

                                                                                  
# API

1. soynlp
   - https://github.com/lovit/soynlp.git
2. 국립국어원 표준국어대사전 표제어 DB(잇다)
   - https://github.com/korean-word-game/db

# Contribute

- smy999 210112yynim@naver.com
- wtt5857 wtt5857@naver.com
- yujuyeon0511 juyeon.yu0511@gmail.com
- Kimyungi gozj3319@naver.com


