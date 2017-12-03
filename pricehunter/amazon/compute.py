from datetime import timedelta
from headhunter.models import AmazonPrice, DatafeedrPrice, Domain, Item, session
import sys
import time


def compute_elapsed(start_time):
    return round(time.time() - start_time, 1)


def compute_ranked_items(now, trusted_only=True):
    # options
    min_difference = 50
    max_ratio = .9
    price_time_limit = now - timedelta(days=1)

    query = (
        session.query(Item, DatafeedrPrice, AmazonPrice)
            .select_from(Domain)
            .join(DatafeedrPrice, Item, AmazonPrice)
            .filter(DatafeedrPrice.url != None)
            .filter(DatafeedrPrice.converted_price != None)
            .filter(DatafeedrPrice.timestamp >= price_time_limit)
            .filter(AmazonPrice.timestamp >= price_time_limit)
            .order_by(Item.asin.asc(), AmazonPrice.price.asc(), DatafeedrPrice.price.asc())
    )

    if trusted_only:
        query = query.filter(Domain.trusted == True)

    previous_asin = None
    lowest_amazon_price = None
    previous_datafeedr_price = None

    start_time = time.time()

    row_count = query.count()
    print('Total rows: {}; computed in {} seconds'.format(row_count, compute_elapsed(start_time)), file=sys.stderr)

    ranked_items = {}
    price_data = None
    new_item = False
    last_percentage = 0

    start_time = time.time()
    enumerated_query = enumerate(query)
    print('Ran SELECT in {} seconds'.format(compute_elapsed(start_time)), file=sys.stderr)

    start_time = time.time()

    for row_index, row in enumerated_query:
        item, datafeedr_price, amazon_price = row[0], row[1], row[2]

        redundant_datafeedr_price = previous_datafeedr_price != None \
            and previous_datafeedr_price.converted_price == datafeedr_price.converted_price \
            and previous_datafeedr_price.merchant_id == datafeedr_price.merchant_id \
            and previous_datafeedr_price.condition == datafeedr_price.condition \
            and previous_datafeedr_price.url == datafeedr_price.url

        previous_datafeedr_price = datafeedr_price

        output_row = []

        if previous_asin != item.asin:
            new_item = True
            min_layer = ''

            previous_asin = item.asin
            lowest_amazon_price = amazon_price

        elif amazon_price.id != lowest_amazon_price.id or redundant_datafeedr_price:
            continue
        else:
            output_row += ['', '', '', '', '', '']

        difference = lowest_amazon_price.price - datafeedr_price.converted_price
        ratio = difference / lowest_amazon_price.price
        if min_difference is not None and (difference < min_difference or ratio > max_ratio):
            continue

        if new_item:
            new_item = False
            item_sales_ranks = set([i for i in item.item_sales_ranks if i.browse_node.layer != None])
            min_layer = min([i.browse_node.layer for i in item_sales_ranks]) if len(item_sales_ranks) > 0 else None
            min_layer_item_sales_ranks = set([i for i in item_sales_ranks if i.browse_node.layer == min_layer])

            browse_nodes = set([item_sales_rank.browse_node for item_sales_rank in min_layer_item_sales_ranks])

            if min_layer != None:
                min_sales_rank = min([i.sales_rank for i in min_layer_item_sales_ranks])
            else:
                min_sales_rank = None

            if min_layer not in ranked_items:
                ranked_items[min_layer] = {}
            layer_items = ranked_items[min_layer]

            if min_sales_rank not in layer_items:
                layer_items[min_sales_rank] = {}
            sales_rank_items = layer_items[min_sales_rank]

            sales_rank_items[item] = {'browse_nodes': browse_nodes, 'amazon_price': lowest_amazon_price, 'datafeedr_prices': []}
            price_data = sales_rank_items[item]

        price_data['datafeedr_prices'].append(datafeedr_price)

    return ranked_items
