from datetime import datetime, timedelta
from terminaltables import AsciiTable
from pricehunter.amazon.compute import compute_elapsed, compute_ranked_items
import os.path
import sys
import time


def format_amount(amount):
    return '{0:.2f}'.format(amount)


print_raw = False

now = datetime.now()
start_time = time.time()

table_data = [['ASIN', 'Layer', 'Sales Rank', 'Browse nodes', 'Title', 'Amazon', 'Condition', 'Datafeedr', 'Cond', 'Diff', 'Webpage', 'URL']]
if print_raw:
    table_data[0] += ['Raw']

ranked_items = compute_ranked_items(now, trusted_only=False)

for layer_index in sorted([l for l in ranked_items.keys() if l != None]):
    layer_items = ranked_items[layer_index]

    for sales_rank in sorted(list(layer_items.keys())):
        sales_rank_items = layer_items[sales_rank]

        for item, price_data in sales_rank_items.items():
            output_row = []

            browse_nodes = '\n'.join([browse_node.tree_to_string() for browse_node in price_data['browse_nodes']])
            output_row += [item.asin, layer_index, sales_rank, browse_nodes, item.title[:50]]

            amazon_price = price_data['amazon_price']
            output_row += [format_amount(amazon_price.price), amazon_price.condition if amazon_price.condition else '']

            for datafeedr_price in price_data['datafeedr_prices']:
                difference = amazon_price.price - datafeedr_price.converted_price
                ratio = difference / amazon_price.price
                output_row += [format_amount(datafeedr_price.converted_price), datafeedr_price.condition if datafeedr_price.condition else '']
                output_row += ['{} ({}%)'.format(format_amount(difference), round(ratio * 100))]

                webpage_path = datafeedr_price.get_webpage_path(now)
                if os.path.exists(webpage_path):
                    webpage_path = 'file://' + webpage_path
                else:
                    webpage_path = ''

                output_row += [webpage_path, datafeedr_price.url]
                if print_raw:
                    output_row += [datafeedr_price.raw]

                table_data.append(output_row)

                output_row = [''] * 7

print('Populated table in {} seconds'.format(compute_elapsed(start_time)), file=sys.stderr)

print(AsciiTable(table_data).table)
