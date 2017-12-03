import json
import sys

from pricehunter import datafeedr
from pricehunter.models import Item, session


# result = datafeedr.search_products(query=['name LIKE "{}"'.format(sys.argv[1])])
result = datafeedr.search_products(query=['ean = "097855066466"'], limit=100)
print(json.dumps(result, indent=4))
