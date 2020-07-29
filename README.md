# bigdata_project

Korea Univ. Bigdata campus project

This project's purpose is making of newly coined word dictionary and automating of updating this.
To do this, we build 2 model that first model is detecting newly coined word and second model is automating model using fisrt model.

## Fisrt Model

1. To collecting data, we uses web crawler for each community.

2. And then, we may use khaiii library for text data preprocessing.

3. To build model, we will apply W2V and classficiation technique to text data.

4. We apply step 1,2,3 repeatedly.

## Second Model

1. If first model is detecting newly coined word, we apply attention deep learning technique to corresponding text data.
    Then, we can drive social meaning of newly coined word.

2. To find out origin of newly coined word, we analyze corresponding date based on time-series.
