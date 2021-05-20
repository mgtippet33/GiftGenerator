import lxml
import requests
from bs4 import BeautifulSoup, SoupStrainer

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
    # Возраст
    'Детский': 'Дитина',
    'Подросток': 'Підліток',
    'Взрослый': 'Дорослий',
    # Пол
    'Мужской': 'Чоловік',
    'Женский': 'Жінка',
    # Другое
    'Інше': 'Інше',
    None: 'Інше'
}


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
