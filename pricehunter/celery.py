from __future__ import absolute_import, unicode_literals
from celery import Celery

app = Celery('products', backend='redis://127.0.0.1',
                         broker='redis://127.0.0.1:6379/0',
                         include=['products.amazon.query', 'products.amazon.crawl'])
app.config_from_object('products.celeryconfig')
