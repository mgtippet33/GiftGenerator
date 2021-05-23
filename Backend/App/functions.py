import datetime
import re

import lxml
import requests
from bs4 import BeautifulSoup, SoupStrainer
from django.db import connection
from facebook_scraper import get_posts
from pytwitterscraper import TwitterScraper

from .models import Holiday

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


def add_event(text, event_date, user_id):
    """Requires date should be in format YYYY-MM-DD"""
    if re.search(r'народження|рождения', text, re.IGNORECASE):
        today = datetime.date.today()
        if type(event_date) is str:
            event_date = datetime.datetime.strptime(
                event_date, '%Y-%m-%d').date()

        if today > event_date:
            event_date = event_date.replace(year=today.year + 1)

        h = Holiday(name=text, date=event_date, owner_id=user_id)
        h.save()


def get_upcoming(user_id):
    h = []
    holidays = Holiday.objects.filter(owner_id=1)
    user_holidays = Holiday.objects.filter(owner_id=user_id)
    for remain_days in range(6):
        day = datetime.date.today() + datetime.timedelta(days=remain_days)
        for event_day in (day, day.replace(year=1900)):
            holidays_data = holidays.filter(date=event_day)
            user_holidays_data = user_holidays.filter(date=event_day)

            if holidays_data.exists():
                h.append([remain_days, holidays_data.values()])

            if user_holidays_data.exists():
                h.append([remain_days, user_holidays_data.values()])

    return h


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
            name = img['alt'].strip()
            name = re.sub(r'[^\w\s]', '', name)
            name = re.sub(r'\s\s', ' ', name)
            name = ' '.join(name.split(' ')[:4])
            name = name[:50]

            desc = desc.text.strip().split('.')
            desc = ' '.join(desc[:2])
            desc = desc[:400]

            price = to_float(price.text)

            if len(name) > 2 and len(desc) > 3 and price:
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

        for q in queries:
            search_link = f'https://prom.ua/search?search_term={" ".join(filter(None, q))}'
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
                        yield product, product_link, q[0], q[1], q[2]


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
