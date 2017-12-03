from pricehunter.models import BrowseNode, session


for browse_node in session.query(BrowseNode).all():
    node = browse_node
    print(node.id, end=': ')
    while node is not None:
        print('{} ({})'.format(node.name, len(node.items.all())), end=', ')
        node = node.ancestors.first() if len(node.ancestors.all()) > 0 else None
    print()
