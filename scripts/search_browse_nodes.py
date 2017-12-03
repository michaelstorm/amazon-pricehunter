import sys
from pricehunter.amazon.query import build_products_from_search


for browse_node_id in sys.argv[2:]:
    build_products_from_search.delay(sys.argv[1], browse_node_id=browse_node_id)
