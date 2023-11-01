# -*- coding: utf-8 -*-
"""saketh babu twitter cnn

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1QY43GvyGtoXhVDUuckxDeoQsjM-3GYDu
"""

# This Python 3 environment comes with many helpful analytics libraries installed
# It is defined by the kaggle/python Docker image: https://github.com/kaggle/docker-python
# For example, here's several helpful packages to load

import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)

# Input data files are available in the read-only "../input/" directory
# For example, running this (by clicking run or pressing Shift+Enter) will list all files under the input directory

import os
for dirname, _, filenames in os.walk('/kaggle/input'):
    for filename in filenames:
        print(os.path.join(dirname, filename))

# You can write up to 20GB to the current directory (/kaggle/working/) that gets preserved as output when you create a version using "Save & Run All"
# You can also write temporary files to /kaggle/temp/, but they won't be saved outside of the current session

"""# Dependencies"""

import pandas as pd
import numpy as np
from tensorflow.keras.preprocessing.sequence import pad_sequences
import string
import nltk
from tensorflow.keras.utils import to_categorical
from tensorflow import keras
from sklearn.model_selection import train_test_split
from nltk.stem.wordnet import WordNetLemmatizer
import re
from tensorflow.keras import regularizers
from tensorflow.keras.layers import Embedding,Flatten,Dense,Conv1D,MaxPooling1D
from nltk.corpus import stopwords
import matplotlib.pyplot as plt
import seaborn as sns
from nltk.tokenize import word_tokenize
from wordcloud import WordCloud,STOPWORDS, ImageColorGenerator
import plotly.express as px
from collections import Counter
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras import Sequential
from sklearn.preprocessing import OrdinalEncoder

"""# EDA"""

df = pd.read_csv("/kaggle/input/cyberbullying-classification/cyberbullying_tweets.csv")
df

df.info()

"""**Let's drop duplicates**"""

print(df.duplicated().sum())
df = df.drop_duplicates()
print(df.duplicated().sum())

"""**Is the dataset balanced ?**"""

df.groupby('cyberbullying_type').size().plot(kind='pie')

"""**How long are the messages in each category?**"""

#get the number of words in every tweet
def length(text):
    return len(word_tokenize(text))
df['word_count'] = df['tweet_text'].apply(length)

fig = px.histogram(df, x="word_count", color="cyberbullying_type", title="Words in the tweet (including very long tweets)")
fig.show()
px.histogram(df[df.word_count<900], x="word_count", color="cyberbullying_type", title="Words in the tweet (excluding very long tweets)")

"""**The wordclouds for every type of cyberbullying**"""

print("Gender")
text = " ".join(review for review in df[df.cyberbullying_type=='gender'].tweet_text.astype(str))
wordcloud = WordCloud(stopwords=STOPWORDS).generate(text)
plt.imshow(wordcloud)
plt.axis("off")
plt.show()

print("Ethnicity")
text = " ".join(review for review in df[df.cyberbullying_type=='ethnicity'].tweet_text.astype(str))
wordcloud = WordCloud(stopwords=STOPWORDS).generate(text)
plt.imshow(wordcloud)
plt.axis("off")
plt.show()

print("Religion")
text = " ".join(review for review in df[df.cyberbullying_type=='religion'].tweet_text.astype(str))
wordcloud = WordCloud(stopwords=STOPWORDS).generate(text)
plt.imshow(wordcloud)
plt.axis("off")
plt.show()

print("Age")
text = " ".join(review for review in df[df.cyberbullying_type=='age'].tweet_text.astype(str))
wordcloud = WordCloud(stopwords=STOPWORDS).generate(text)
plt.imshow(wordcloud)
plt.axis("off")
plt.show()

print("Other")
text = " ".join(review for review in df[df.cyberbullying_type=='other_cyberbullying'].tweet_text.astype(str))
wordcloud = WordCloud(stopwords=STOPWORDS).generate(text)
plt.imshow(wordcloud)
plt.axis("off")
plt.show()

print("Non-bullying")
text = " ".join(review for review in df[df.cyberbullying_type=='not_cyberbullying'].tweet_text.astype(str))
wordcloud = WordCloud(stopwords=STOPWORDS).generate(text)
plt.imshow(wordcloud)
plt.axis("off")
plt.show()

"""# Feature engineering and data preprocessing"""

def remove_punct(text):
  #print(text)
  return text.translate(str.maketrans('', '',string.punctuation))

df['no_punctuation'] = df['tweet_text'].apply(remove_punct)
df['no_punctuation']

def lower(text):
    return text.lower()
df['no_punctuation'] = df['no_punctuation'].apply(lower)
def remove_stopwords(text):
    stop_words = set(stopwords.words('english'))
    new_text = []
    for el in word_tokenize(text):
        if not el in stop_words:
            new_text.append(el)
    return new_text
df['no_stopwords'] = df.no_punctuation.apply(remove_stopwords)

"""**Let's separate words and emojis.**"""

def smile_handle(word_list):
  new_word_list = []
  emoji_pattern = re.compile(r"([\U00002600-\U000027BF])|([\U0001f300-\U0001f64F])|([\U0001f680-\U0001f6FF])", flags=re.UNICODE)
  for word in word_list:
    if len(re.findall(emoji_pattern,word))!=0:
      if len(re.findall(emoji_pattern,word))!=len(word):
        new_word_list.append(re.sub(emoji_pattern,'',word))
      new_word_list.extend(re.findall(emoji_pattern,word))
      #print(word,new_word_list)
    else:
      new_word_list.append(word)
  for i,el in enumerate(new_word_list):
    if type(el)==tuple:
      new_word_list[i] = el[1]
  return new_word_list
  #print(new_word_list)
df.no_stopwords = df.no_stopwords.apply(smile_handle)

"""**Let's standartize words with the help of lemmatization**"""

def lemmatize(words):
    new_words = []
    lem = WordNetLemmatizer()
    for w in words:
        new_words.append(lem.lemmatize(w))
    return new_words

df['lemmatized'] = df.no_stopwords.apply(lemmatize)

"""**Let's form the vocabulary and get its length**"""

vocab = Counter()

def add_to_vocab(words):
  global vocab
  vocab.update(words)
df.lemmatized.apply(add_to_vocab)
vocab_size = len(vocab)
print("Vocabulary size: ",vocab_size)

"""**Top-50 words**"""

vocab.most_common(50)

"""**Let's drop too unfrequent words!**"""

words = [key for key,val in vocab.items() if val>=3]
vocab_size = len(words)
print(vocab_size)
def remove_rare(text):
    global words
    for el in text:
        if not el in words:
            text.remove(el)
    return text

df.lemmatized = df.lemmatized.apply(remove_rare)

"""# Model fitting

**train-test-split**
"""

X_train,X_test,y_train,y_test = train_test_split(df[['lemmatized']],df['cyberbullying_type'])

"""**new voacbulary size**"""

vocab = Counter()
def add_to_vocab(words):
  global vocab
  vocab.update(words)
X_train.lemmatized.apply(add_to_vocab)
df.lemmatized.apply(add_to_vocab)
vocab_size = len(vocab)
vocab_size

"""**For simplicity, let's convert texts to number sequences**"""

tokenizer = Tokenizer()
tokenizer.fit_on_texts(X_train.lemmatized)
X_train = tokenizer.texts_to_sequences(X_train.lemmatized)
X_test = tokenizer.texts_to_sequences(X_test.lemmatized)

"""**Now let's bring the sequences to the same size**"""

max_size = len(max(df.lemmatized,key=lambda x:len(x)))
max_size

X_train = pad_sequences(X_train, maxlen=max_size, padding='post')

X_test = pad_sequences(X_test, maxlen=max_size, padding='post')

enc = OrdinalEncoder()
y_train,y_test = to_categorical(enc.fit_transform(X=y_train.to_frame()),num_classes=6),to_categorical(enc.fit_transform(X=y_test.to_frame()),num_classes=6)

"""**defining model**"""

X_train

def define_model(vocab_size,max_length):
    model = Sequential()
    model.add(Embedding(vocab_size, 100, input_length=max_length))
    model.add(Conv1D(filters=32, kernel_size=8, activation='relu'))
    model.add(MaxPooling1D(pool_size=2))
    model.add(Flatten())
    model.add(Dense(10, activation='relu',kernel_regularizer=regularizers.L1L2(l1=1e-5, l2=1e-4)))
    model.add(Dense(, activation='softmax'))6
    model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
    return model

model = define_model(vocab_size,max_size)
model.fit(X_train, y_train, epochs=12, verbose=2)

"""# Model testing"""

results = model.evaluate(X_test, y_test)
results