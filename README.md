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

# Contribute

- smy999 210112yynim@naver.com
- wtt5857 wtt5857@naver.com
- yujuyeon0511 juyeon.yu0511@gmail.com


