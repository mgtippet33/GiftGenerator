"""
If first run, download this packages
    nltk.download('wordnet')
    nltk.download('stopwords')
"""

import os.path
import pickle
import re

import nltk
import numpy
import pandas
from nltk.corpus import stopwords
from sklearn import preprocessing
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

lemma = nltk.wordnet.WordNetLemmatizer()
classes = ('anime', 'games', 'movie', 'music', 'technology', 'traveling')


def clean_text(text):
    if type(text) != str:
        text = str(text)

    text = text.lower()
    text = re.sub(r"(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)|^rt|http.+?", "", text)
    text = re.sub(r"^\W+", "", text)

    words = []
    for word in text.split():
        word = lemma.lemmatize(word)
        if word not in stopwords.words('english'):
            words.append(word)

    text = ' '.join(words)
    return text


def make_classification_tools():
    classifier_path = 'classification_data/classifier.sav'
    vectorizer_path = 'classification_data/vectorizer.sav'

    if os.path.exists(classifier_path) and os.path.exists(vectorizer_path):
        return pickle.load(open(classifier_path, 'rb')), pickle.load(open(vectorizer_path, 'rb'))

    handle = pandas.read_csv('classification_data/interests.csv')

    X = handle['text'].apply(lambda x: numpy.str_(x))
    y = handle['classification']

    le = preprocessing.LabelEncoder()
    y = le.fit_transform(y)

    vectorizer = TfidfVectorizer(
        stop_words='english',
        sublinear_tf=True,
        strip_accents='unicode',
        analyzer='word',
        token_pattern=r'\w{2,}',
        ngram_range=(1, 1),
        max_features=30000)

    X = vectorizer.fit_transform(X)

    classifier = MultinomialNB().fit(X, y)

    pickle.dump(vectorizer, open(vectorizer_path, 'wb'))
    pickle.dump(classifier, open(classifier_path, 'wb'))

    return classifier, vectorizer


def predict(text, classifier, vectorizer):
    clear_string = clean_text(text)
    coded_string = vectorizer.transform([clear_string])

    class_ = classifier.predict(coded_string)[0]
    probs = list(classifier.predict_proba(coded_string)[0])

    return class_, probs


if __name__ == '__main__':
    model, text_transformer = make_classification_tools()
    strings = (...,)

    for string in strings:
        prediction_class, prediction_probs = predict(
            text=string,
            classifier=model,
            vectorizer=text_transformer
        )
        print(classes[prediction_class])
        print(prediction_probs)
