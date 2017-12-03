import sys
from pricehunter.amazon import api
from pricehunter.amazon.query import build_products_from_search
from pricehunter.models import session


try:
    build_products_from_search.delay(sys.argv[1], keywords=sys.argv[2])
    session.commit()


except:
    print(api.last_pretty_xml)
    raise sys.exc_info()[1]
