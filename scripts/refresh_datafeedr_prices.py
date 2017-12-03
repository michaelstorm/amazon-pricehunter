from pricehunter import datafeedr
from pricehunter.models import DatafeedrPrice, Item, session


items = session.query(Item).filter(Item.upc != None).filter(Item.upc > "619125629036").order_by(Item.upc.asc()).all()

for item in items:
    if item.upc:
        datafeedr_prices = datafeedr.get_prices_for_upc(item.upc)
        for price in datafeedr_prices:
            price.item = item
            if not session.query(DatafeedrPrice).filter_by(_id=price._id).first():
                session.add(price)

        session.commit()
