import re

import lxml
import requests
from bs4 import BeautifulSoup, SoupStrainer
from facebook_scraper import get_posts
from pytwitterscraper import TwitterScraper

from django.db import connection

TRANSLATIONS = {
    # Праздники
    'День рождения': 'День народження',
    '8 марта': '8 березня',
    '14 февраля': '14 Жовтня',
    'День влюбленных': 'День закоханих',
    'Новый год': 'Новий рік',
    # Интересы
    'Спорт': 'Спорт',
    'Фото': 'Фотографія',
    'Социальные сети': 'Соціальні мережі',
    'Мода': 'Мода',
    'Путешевствия': 'Подорожі',
    'Аниме': 'Аніме',
    'Музыка': 'Музика',
    'Кино': 'Кіно',
    'Комиксы': 'Комікси',
    'Устройство': 'Технології',
    'Театр': 'Театр',
    'Программирование': 'Програмування',
    'Косметика': 'Косметика',
    'Одежда': 'Одяг',
    'Моделинг': 'Моделінг',
    'Геймер': 'Ігри',
    'Фитнес': 'Фітнес',
    'Анимация': 'Анімація',
    'Кулинария': 'Кулінарія',
    'Учеба': 'Навчання',
    'Авто': 'Автомобіль',
    'Животные': 'Тварини',
    'Боксерские': 'Боротьба',
    'Футбол': 'Футбол',
    'Япония': 'Японія',
    'BTS': 'BTS',
    # Возраст
    'Детский': 'Дитина',
    'Подросток': 'Підліток',
    'Взрослый': 'Дорослий',
    # Пол
    'Мужской': 'Чоловік',
    'Женский': 'Жінка',
    # Analysis
    'anime': 'Аніме',
    'games': 'Ігри',
    'movie': 'Кіно',
    'technology': 'Технології',
    'traveling': 'Подорожі',
    # Другое
    'Інше': 'Інше',
    None: 'Інше'
}


def cut_url(url):
    name = re.sub(r'.*(twitter|facebook).com/', '', url)

    if name[-1] == '/':
        name = name[:-1]
    return name


def parse_twitter(url, tweets_count=10):
    ts = TwitterScraper()
    name = cut_url(url)
    profile = ts.get_profile(name=name)
    profile_id = profile.__dict__['id']

    tweets_text = set()
    tweets = ts.get_tweets(profile_id, count=tweets_count)
    for tweet in tweets.contents:
        tweets_text.add(tweet['text'])

    return tweets_text


def parse_facebook(url, posts_count=2):
    name = cut_url(url)

    posts_text = set()
    for post in get_posts(name, pages=posts_count):
        posts_text.add(post['text'])

    return posts_text


def to_float(string):
    number = ''
    for char in string:
        if char in '0123456789' or char == '.' and '.' not in number:
            number += char

    if len(number) > 1:
        return float(number)


def get_product(url, request_session=None):
    if request_session:
        response = request_session.get(url)
    else:
        response = requests.get(url)

    if response.status_code == 200:
        strainer = SoupStrainer(['img', 'p', 'span'])
        html = BeautifulSoup(
            response.text, features='lxml', parse_only=strainer)

        img = html.find('img', class_='ek-picture__item')
        desc = html.find('p')
        price = html.find('span', class_='ek-text ek-text_weight_bold')

        if img and desc and price:
            name = ' '.join(img['alt'].strip().split(' ')[:3])
            desc = desc.text.strip()[:60]
            price = to_float(price.text)

            if len(name) and len(desc) and price:
                return name, desc, price


def search_products(interests, holiday):
    session = requests.Session()

    while len(interests) >= 2:
        inter = interests.pop(), interests.pop()
        queries = (
            (None, inter[1], holiday),
            (inter[0], None, holiday),
            (inter[0], inter[1], None)
        )

        for query in queries:
            search_link = f'https://prom.ua/search?search_term={" ".join(filter(None, query))}'
            response = session.get(search_link)

            if response.status_code == 200:
                strainer = SoupStrainer(
                    'a', class_='ek-link ek-link_blackhole_full-hover')
                html = BeautifulSoup(
                    response.text, features='lxml', parse_only=strainer)

                tags = html.findAll('a')
                for tag in tags:
                    product_link = f'https://prom.ua{tag["href"]}'
                    # remove token from link
                    product_link = product_link.split('?')[0]
                    product = get_product(
                        product_link, request_session=session)
                    if product:
                        yield product, product_link, query[0], query[1], query[2]


def get_dict(cursor):
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
    ]


def query(sql):
    with connection.cursor() as cursor:
        cursor.execute(sql)
        result = [dictionary for dictionary in get_dict(cursor)]
    return result
