from collections import defaultdict
from sqlalchemy import func
from pricehunter.models import Domain, DatafeedrPrice, Item, ItemSalesRank, BrowseNode, session

max_layers = 3
print('Trusted,Items in all layers,Items in top layers,{},Name'.format(','.join('Layer {} items'.format(i) for i in range(max_layers + 1))))

for domain in session.query(Domain).order_by(Domain.name.asc()):
    if len(domain.name) > 0:
        result = (
            session.query(Item)
                   .select_from(Domain, DatafeedrPrice)
                   .join(DatafeedrPrice, Item)
                   .filter(Domain.name == domain.name)
        )

        layer_counts = defaultdict(int)

        for item in result:
            item_result = (
                session.query(func.min(BrowseNode.layer))
                       .select_from(Item, ItemSalesRank, BrowseNode)
                       .join(ItemSalesRank, BrowseNode)
                       .filter(Item.asin == item.asin)
                       .one()[0]
            )
            if item_result != None:
                layer_counts[item_result] += 1

        top_layers = [layer_counts[i] for i in range(max_layers + 1)]
        print(','.join(['y' if domain.trusted else '',
                        str(sum(layer_counts.values())),
                        str(sum(top_layers)),
                        *[str(l) for l in top_layers],
                        domain.name]))
