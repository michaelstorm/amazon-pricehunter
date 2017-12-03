from datetime import datetime


xml_namespace = '{http://webservices.amazon.com/AWSECommerceService/2013-08-01}'


def ns_find(item, name):
    return item.find('{}{}'.format(xml_namespace, name))


def ns_findall(item, name):
    return item.findall('{}{}'.format(xml_namespace, name))


def ns_get(item, *names):
    for name in names:
        if item is not None:
            item = ns_find(item, name)

    return item


def ns_getall(item, *names):
    for name in names[:-1]:
        if item is not None:
            item = ns_find(item, name)

    if item is not None:
        item = ns_findall(item, names[-1])
        return item if item is not None else []
    else:
        return []


def ns_get_text(item, *names):
    item = ns_get(item, *names)
    return item.text if item is not None else item


def ns_get_int(item, *names):
    item = ns_get(item, *names)
    return int(item.text) if item is not None else item


def parse_upcs(item):
    upcs = [ns_get_text(item, 'ItemAttributes', 'UPC')]
    upcs += [ns_get_text(upc_list_element) for upc_list_element in ns_getall(item, 'ItemAttributes', 'UPCList', 'UPCListElement')]
    return set([upc for upc in upcs if upc is not None and len(upc) > 0])


def parse_item_search(doc):
    results = []

    for error in ns_getall(doc, 'Items', 'Request', 'Errors', 'Error'):
        code = ns_get_text(error, 'Code')
        if code == 'AWS.ECommerceService.NoExactMatches':
            return []
        else:
            raise Exception(code)

    for item in ns_getall(doc, 'Items', 'Item'):
        asin = ns_get_text(item, 'ASIN')
        product_group = ns_get_text(item, 'ItemAttributes', 'ProductGroup')
        title = ns_get_text(item, 'ItemAttributes', 'Title')
        upcs = parse_upcs(item)
        results.append({'asin': asin, 'product_group': product_group, 'title': title, 'upcs': upcs})

    return results


def parse_price_info(item_xml, price_type):
    offer_summary = ns_get(item_xml, 'OfferSummary')
    quantity = ns_get_int(offer_summary, 'Total{}'.format(price_type))

    amount = ns_get_int(offer_summary, 'Lowest{}Price'.format(price_type), 'Amount')
    if amount is not None:
        # amount can be missing when FormattedAmount is "Too low to display", but seems to be
        # available in the Offers elements
        return {'price': float(amount) / 100, 'quantity': quantity, 'timestamp': datetime.now()}


def parse_buy_button_price(item_xml):
    offer = ns_get(item_xml, 'Offers', 'Offer')
    condition = ns_get_text(offer, 'OfferAttributes', 'Condition')
    amount = ns_get_int(offer, 'OfferListing', 'Price', 'Amount')
    if amount is not None:
        return {'price': float(amount) / 100, 'timestamp': datetime.now()}


def parse_item_offers(doc):
    price_infos = {}
    item = ns_get(doc, 'Items', 'Item')

    for price_type in ('Used', 'New', 'Collectible'):
        price_info = parse_price_info(item, price_type)
        price_infos[price_type] = price_info

    price_infos['BuyButton'] = parse_buy_button_price(item)

    return {'prices': price_infos}


def parse_browse_node(xml, search_index):
    data = {}
    browse_node_id = ns_get_text(xml, 'BrowseNodeId')
    name_element = ns_get(xml, 'Name')
    name = name_element.text if name_element is not None else None

    ancestors = ns_get(xml, 'Ancestors')
    if ancestors is not None:
        ancestor = ns_get(ancestors, 'BrowseNode')
        parsed_ancestor = parse_browse_node(ancestor, search_index)
    else:
        parsed_ancestor = None

    return {'id': browse_node_id, 'name': name, 'search_index': search_index, 'ancestor': parsed_ancestor}


def parse_item_browse_nodes(doc, search_index):
    item = ns_get(doc, 'Items', 'Item')
    browse_nodes = ns_getall(item, 'BrowseNodes', 'BrowseNode')

    browse_node_trees = [parse_browse_node(browse_node, search_index) for browse_node in browse_nodes]

    flattened_browse_node_trees = []
    for browse_node_tree in browse_node_trees:
        flattened_browse_node_tree = []
        while browse_node_tree is not None:
            new_browse_node_tree = {**browse_node_tree}
            del new_browse_node_tree['ancestor']
            flattened_browse_node_tree.append(new_browse_node_tree)
            browse_node_tree = browse_node_tree['ancestor']

        flattened_browse_node_trees.append(flattened_browse_node_tree)

    return flattened_browse_node_trees
