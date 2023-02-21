import requests

from bs4 import BeautifulSoup

import re

from decimal import *

from shop.models import Product

"""
{
    'name': 'Труба профильная 40х20 2 мм 3м', 
    'image_url': 'https://my-website.com/30C39890-D527-427E-B573-504969456BF5.jpg', 
    'price': Decimal('493.00'), 
    'unit': 'за шт', 
    'code': '38140012'
 }
"""

class ScrapingError(Exception):
    pass


class ScrapingTimeoutError(ScrapingError):
    pass


class ScrapingHTTPError(ScrapingError):
    pass


class ScrapingOtherError(ScrapingError):
    pass


URL_SCRAPING = 'https://biggeek.ru/catalog/apple-iphone'
URL_SCRAPING_DOMAIN = 'https://biggeek.ru'

def scraping():
    try:
        resp = requests.get(URL_SCRAPING, timeout=10.0)
    except requests.exceptions.Timeout:
        raise ScrapingTimeoutError("request timed out")
    except Exception as e:
        raise ScrapingOtherError(f'{e}')

    if resp.status_code != 200:
        raise ScrapingHTTPError(f"HTTP {resp.status_code}: {resp.text}")

    data_list = []
    html = resp.text 
    soup = BeautifulSoup(html, 'html.parser')
    blocks = soup.select('.catalog-card')
    for block in blocks:
        data = {}
        name = block.select_one('.catalog-card__title').get_text()
        data['name'] = name

        image_url = block.select_one('img')['src']
        data['image_url'] = image_url

        price = block.select_one('.cart-modal-count').get_text()
        price = price.replace(' ', '').strip('от₽')
        price += '.00'
        data['price'] = Decimal(price)

        data['unit'] = 'за шт'

        # find and open detail page
        url_detail = block.select_one('.catalog-card__img')
        url_detail = url_detail['href']
        url_detail = URL_SCRAPING_DOMAIN + url_detail
        html_detail = requests.get(url_detail).text
        soup = BeautifulSoup(html_detail, 'html.parser')
        code = soup.select_one('.vendor-code').get_text().removeprefix('Артикул: ')
        data['code'] = code

        data_list.append(data)

        print(data)


        for item in data_list:
            if not Product.objects.filter(code=item['code']).exists():
                Product.objects.create(
                    name=item['name'],
                    code=item['code'],
                    price=item['price'],
                    unit=item['unit'],
                    image_url=item['image_url'],
                )

        return data_list

if __name__ == '__main__':
    scraping()
