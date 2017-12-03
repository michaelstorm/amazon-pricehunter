import os
import os.path
import sys
from datetime import datetime, timedelta
from sqlalchemy import or_

from products import datafeedr
from products.amazon.api import amazon_api_call
from products.amazon.parse import parse_item_browse_nodes, parse_item_offers, parse_item_search
from products.models import AmazonPrice, BrowseNode, DatafeedrPrice, Item, ItemBrowseNode, ItemSalesRank, Session
from products.celery import app

import scrapy
from twisted.internet import reactor
from scrapy.crawler import CrawlerRunner


def get_item_details(aws_credentials_index, item, search_index):
    doc, xml_string = amazon_api_call(aws_credentials_index, Action='ItemLookup', ItemId=item['asin'], ResponseGroup="Offers")
    item = {**item, **parse_item_offers(doc)}
    item['xml'] = xml_string

    doc, _ = amazon_api_call(aws_credentials_index, Action='ItemLookup', ItemId=item['asin'], ResponseGroup="BrowseNodes")
    item['browse_nodes'] = parse_item_browse_nodes(doc, search_index)

    return item


def search_products(aws_credentials_index, search_index, browse_node_id=None, keywords=None, max_pages=10):
    items = []
    item_index = 0

    for page in range(1, max_pages + 1):
        search_args = dict(Action='ItemSearch', SearchIndex=search_index, ResponseGroup="ItemAttributes", Sort="salesrank",
                           ItemPage=str(page))

        if browse_node_id is not None:
            search_args['BrowseNode'] = browse_node_id
        if keywords is not None:
            search_args['Keywords'] = keywords

        doc, _ = amazon_api_call(aws_credentials_index, **search_args)
        page_items = parse_item_search(doc)

        for item in page_items:
            item['sales_rank'] = item_index
            item_index += 1

        items.extend(page_items)

        if len(page_items) == 0:
            break

    return items


@app.task
def get_item_datafeedr_prices(asin):
    session = Session()

    try:
        item = session.query(Item).get(asin)
        datafeedr_prices = []

        if not item:
            print('Item with ASIN {} not found'.format(asin))
        elif not item.upc:
            print('Item with ASIN {} has no UPCs'.format(asin))
        else:
            upcs = item.upc.split(',')
            print('Item with ASIN {} has {} UPC(s): {}'.format(item.asin, len(upcs), upcs))

            datafeedr_prices = datafeedr.get_prices_for_upcs(session, upcs)
            print('Received {} Datafeedr prices'.format(len(datafeedr_prices)))

            for price in datafeedr_prices:
                price.item = item
                session.add(price)

        item.datafeedr_prices_searched_at = datetime.now()
        session.commit()

        for price in datafeedr_prices:
            session.refresh(price)
            download_datafeedr_price_webpage.delay(price.id)

    finally:
        session.close()


def get_item_datafeedr_prices_all(time_delta, min_layer):
    session = Session()

    try:
        print('=====================================')
        print('Scanning all items')

        now = datetime.now()
        searched_time_limit = now - time_delta
        min_layer_sales_rank_time_limit = now - (time_delta * 2)

        def filter_by_layer(item):
            if min_layer != None:
                item_min_layer = item.min_layer(session, min_layer_sales_rank_time_limit)
                return item_min_layer != None and item_min_layer <= min_layer
            else:
                return True

        query = (
            session.query(Item)
            .join(AmazonPrice)
            .filter(
                or_(
                    Item.datafeedr_prices_searched_at == None,
                    Item.datafeedr_prices_searched_at <= searched_time_limit
                ),
                Item.upc != None,
                AmazonPrice.price >= 30,
            )
            .group_by(Item.asin)
            .distinct(Item.asin)
        )

        items = list(filter(filter_by_layer, query))

        print('Found {} items'.format(len(items)))
        for item in items:
            get_item_datafeedr_prices.delay(item.asin)

    finally:
        session.close()


@app.task
def get_item_datafeedr_prices_important():
    get_item_datafeedr_prices_all(timedelta(days=1), 2)


# @app.task
# def get_item_datafeedr_prices_all():
#     get_item_datafeedr_prices_all(timedelta(weeks=2), None)


def build_item(session, item, item_data):
    if 'xml' in item_data:
        item.xml = item_data['xml']

    if 'upcs' in item_data:
        item.upc = ','.join(item_data['upcs'])
        if len(item.upc) == 0:
            item.upc = None

    for price_type, price_info in item_data.get('prices', {}).items():
        if price_info:
            price = AmazonPrice(item=item, condition=price_type, **price_info)
            session.add(price)

    for browse_node_tree in item_data.get('browse_nodes', []):
        previous_browse_node = None

        for browse_node_info in reversed(browse_node_tree):
            browse_node_id = browse_node_info['id']
            browse_node = session.query(BrowseNode).get(str(browse_node_id))

            if browse_node_info['name'] in ['Books', 'Beauty & Personal Care', 'Grocery & Gourmet Food']:
                print('Skipping browse node named {}'.format(browse_node_info['name']))
                break
            elif not browse_node:
                print('Creating browse node "{}"'.format(browse_node_info['name']))
                browse_node = BrowseNode(id=browse_node_id)
                session.add(browse_node)

            browse_node.name = browse_node_info['name']
            browse_node.search_index = browse_node_info['search_index']
            if previous_browse_node is not None:
                browse_node.ancestors.append(previous_browse_node)

            previous_browse_node = browse_node

        if previous_browse_node:
            item_browse_node = ItemBrowseNode(item=item, browse_node=previous_browse_node)
            session.add(item_browse_node)


@app.task(bind=True)
def build_products_from_search(self,
                               search_index,
                               browse_node_id=None,
                               keywords=None,
                               refresh_existing=False,
                               do_get_item_details=True,
                               max_pages=10):

    print('======================================================================================')
    session = Session()
    now = datetime.now()

    try:
        aws_credentials_index = self.request.hostname.split('@')[1]

        if browse_node_id:
            browse_node = session.query(BrowseNode).get(browse_node_id)
            if browse_node:
                print('Searching existing browse node {}'.format(browse_node.tree_to_string()))
            else:
                print('Searching unknown browse node {}'.format(browse_node_id))

        if keywords:
            print('Searching keywords "{}"'.format(keywords))

        new_items = []
        new_items_data = []
        items_data = search_products(aws_credentials_index,
                                     search_index,
                                     browse_node_id=browse_node_id,
                                     keywords=keywords,
                                     max_pages=max_pages)

        print('Found {} items'.format(len(items_data)))

        received_items = []

        for item_data in items_data:
            asin = item_data['asin']
            item = session.query(Item).get(asin)

            if item:
                print('Item already exists: "{}"'.format(item_data['title']))
                if not refresh_existing:
                    received_items.append([item, item_data])
                    continue

            # only retrieve details if item doesn't exist or we're refreshing it
            if do_get_item_details:
                item_detail_data = get_item_details(aws_credentials_index, item_data, search_index)
                item_data = {**item_data, **item_detail_data}

            new_items_data.append(item_data)

        for item_data in new_items_data:
            # however, since another job could've created it in the meantime, check again if it
            # exists
            asin = item_data['asin']
            item = session.query(Item).get(asin)

            # don't create new items if we didn't retrieve their details
            if do_get_item_details and not item:
                print('Creating item "{}"'.format(item_data['title']))
                item = Item(asin=asin, product_group=item_data['product_group'], title=item_data['title'])

                new_items.append(item)
                session.add(item)

            if item:
                build_item(session, item, item_data)
                received_items.append([item, item_data])

        if browse_node_id:
            browse_node = session.query(BrowseNode).get(browse_node_id)
            if browse_node:
                browse_node.searched_at = datetime.now()

                for item, item_data in received_items:
                    item_sales_rank = ItemSalesRank(item=item, browse_node=browse_node, sales_rank=item_data['sales_rank'], timestamp=now)
                    session.add(item_sales_rank)

        session.commit()

        for item_pair in received_items:
            item = item_pair[0]
            session.add(item)

            price_expiration = now - timedelta(days=1)
            if item.datafeedr_prices_searched_at == None or item.datafeedr_prices_searched_at < price_expiration:
                get_item_datafeedr_prices.delay(item.asin)

    finally:
        session.close()


@app.task
def download_datafeedr_price_webpage(datafeedr_price_id):
    session = Session()
    try:
        datafeedr_price = session.query(DatafeedrPrice).get(datafeedr_price_id)
        if datafeedr_price.url == None:
            print('URL not recorded for Datafeedr price {}, item {}'.format(datafeedr_price_id, datafeedr_price.item.asin))
        else:
            print('Downloading webpage for Datafeedr price {}, item {}'.format(datafeedr_price_id, datafeedr_price.item.asin))

            class TestSpider(scrapy.Spider):
                name = "test"
                start_urls = [datafeedr_price.url]

                def parse(self, response):
                    try:
                        now = datetime.now()
                        dirname = datafeedr_price.get_webpage_directory(now)
                        os.makedirs(dirname, exist_ok=True)

                        filename = datafeedr_price.get_webpage_path(now)
                        with open(filename, 'wb') as f:
                            f.write(response.body)
                        f.close()
                    except Exception as e:
                        print(e, file=sys.stderr)
                        raise e

            runner = CrawlerRunner()

            d = runner.crawl(TestSpider)
            d.addBoth(lambda _: reactor.stop())
            reactor.run() # the script will block here until the crawling is finished

    finally:
        session.close()
