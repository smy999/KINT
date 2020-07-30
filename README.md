# bigdata_project

Korea Univ. Bigdata campus project

This project's purpose is making of newly coined word dictionary and automating of updating this.
To do this, we build 2 model that first model is detecting newly coined word and second model is extracting social meaning of the word.

## Newly Coined Word Detecting Model

1. Data collecting step
    - we uses web crawlers for each sector.
    - This crawlers collect head text data and datetime data.
    - c.f) Humor Crawler : natepan (10대이야기, 20대이야기, 톡커들의 선택 명예의 전당 (일별)), todayhumor (베오베, 베스트게시물), ilbe (일베-일간베스트)
    -      politic Crawler : ilbe (정치/시사), 보배드림 (정치)
    -      Entertainment Crawler : dcinside (인방갤, 야구갤러리, 연예인), instize (이슈)
    -      Mom Crawler : 맘스홀릭 베이비 (자유수다방)
    -      Shopping Crawler : ppomppu (자유게시판)
    
2. Text data preprocessing step
    - We may use soynlp library to extract words.
    - And then, they are searched Standard Korean Language Dictionary.
    - If they are not in Standard Korean Language Dictionary, they are used at next step (1).
    - Othewise, they are used at next step (2).

3. Model building step
    - (1) we will apply word2vector to vectorize word data.
    -    Then, we calculate similarity between word data.
    -    If newly coined word have highly similarity, we apply clustering technique to word data.
    -    Otherwise, we apply classficiation technique to word data.
    - (2) we analyze time-series data to find newly coined word.

4. We apply step 1,2,3 repeatedly.

## Socical Meaning Extracting Model

1. Data collecting step
   - Our crawlers search a word in each commnuity and collect head, body, comment, datetime.

2. Text data preprocessing
   - we may nomalize text data and analyze morpheme with our word dictionary.
   - c.f) our word dictionary consists of detected newly coined words.

3. Model building step
   - we apply attention technique to extract social meaning of the word.
