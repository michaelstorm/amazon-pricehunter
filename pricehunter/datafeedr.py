from datetime import datetime
from urllib.parse import urlparse
import hashlib
import hmac
import json
import os
import requests
import time

from currency_converter import CurrencyConverter
from products.models import Item, DatafeedrPrice, Domain, BrowseNode


DATAFEEDR_BASE_URL = 'http://api.datafeedr.com'

def do_request(action, **params):
    data = {
        'aid': os.environ['DATAFEEDR_ACCESS_KEY'],
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()),
        **params
    }

    message = data['aid'] + action + data['timestamp']
    hmac_instance = hmac.new(os.environ['DATAFEEDR_SECRET_KEY'].encode('utf-8'), message.encode('utf-8'), hashlib.sha256)
    data['signature'] = hmac_instance.hexdigest()

    url = '{}/{}'.format(os.environ['DATAFEEDR_BASE_URL'], action)
    r = requests.post(url, json=data)
    return r.json()


def search_products(**params):
    if 'limit' not in params:
        # limit is 20 by default; max is 100
        params['limit'] = 100

    print(params)
    converter = CurrencyConverter()
    results = do_request('search', **params)
    for product in results.get('products', []):
        currency = product.get('currency')
        if currency is not None:
            for field in ['price', 'finalprice']:
                value = product.get(field)
                if value is not None:
                    converted_field = '{}_converted'.format(field)
                    try:
                        converted_value = round(converter.convert(int(value) / 100, currency, 'USD'), 2)
                        product[converted_field] = converted_value
                    except Exception as e:
                        print(e)

    return results


def get_prices_for_field(session, field_name, field_values):
    print('Searching for {} {}...'.format(field_name, field_values), end=' ')
    joined_value = '|'.join(['"{}"'.format(value) for value in field_values])
    result = search_products(query=['{} LIKE {}'.format(field_name, joined_value)])
    print('{} results'.format(len(result['products'])))
    prices = []

    for product_data in result['products']:
        condition = product_data.get('condition')
        if condition:
            condition = condition[:16]

        url = product_data.get('direct_url')
        domain = None
        if url:
            parsed_url = urlparse(url)
            domain = session.query(Domain).filter_by(name=parsed_url.netloc).first()

        price = DatafeedrPrice(price=product_data.get('finalprice'), converted_price=product_data.get('finalprice_converted'),
                               url=url, domain=domain, merchant_id=product_data['merchant_id'], condition=condition,
                               _id=product_data['_id'], timestamp=datetime.now(), raw=json.dumps(product_data, indent=4))
        prices.append(price)

    return prices


def get_prices_for_upcs(session, upcs):
    prices = []

    for field_name in ['upc', 'ean']:
        field_prices = get_prices_for_field(session, field_name, upcs)

        if len(field_prices) >= 100:
            field_prices = []
            for upc in upcs:
                field_prices += get_prices_for_field(session, field_name, [upc])

        prices += field_prices

    return prices
