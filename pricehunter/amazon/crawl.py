from datetime import datetime, timedelta
from sqlalchemy import or_, and_

from products.amazon.query import build_products_from_search
from products.models import BrowseNode, Session
from products.celery import app


def get_browse_node_layers(session, max_layers=None):
    all_browse_nodes = session.query(BrowseNode).all()
    browse_nodes = [b for b in all_browse_nodes if b.ancestors.count() == 0]

    layers = [browse_nodes]

    while True:
        if len(layers) == max_layers:
            break

        layer = []
        for browse_node in layers[-1]:
            results = session.query(BrowseNode).filter(BrowseNode.ancestors.any(BrowseNode.id == browse_node.id)).all()
            layer.extend(results)

        if len(layer) == 0:
            break

        layers.append(layer)

    return layers


def enqueue_next_browse_nodes(session, count):
    print('Ensuring {} browse nodes are enqueued'.format(count))
    now = datetime.now()
    searched_time_limit = now - timedelta(days=1)
    enqueued_time_limit = now - timedelta(minutes=30)
    enqueues_remaining = count

    layer_index = 0
    while True:
        layer_query = session.query(BrowseNode).filter_by(layer=layer_index)
        done = False

        pending_nodes_query = (
            layer_query
                .filter(BrowseNode.enqueued_at > enqueued_time_limit,
                        or_(BrowseNode.enqueued_at > BrowseNode.searched_at,
                            BrowseNode.searched_at == None))
        )

        print('------------------------------------------')
        print('{} browse nodes in layer {}'.format(layer_query.count(), layer_index))
        if layer_query.count() == 0:
            break

        possible_nodes_query = (
            layer_query
                .filter(or_(BrowseNode.enqueued_at == None,
                            and_(BrowseNode.searched_at <= searched_time_limit, BrowseNode.enqueued_at <= BrowseNode.searched_at),
                            and_(BrowseNode.enqueued_at <= enqueued_time_limit,
                                 or_(BrowseNode.searched_at == None,
                                     BrowseNode.searched_at <= BrowseNode.enqueued_at))))
        )

        print('Unqueued nodes: {}'.format(possible_nodes_query.count()))
        print('Pending nodes: {}'.format(pending_nodes_query.count()))

        for browse_node in pending_nodes_query.all():
            minutes = round((now - browse_node.enqueued_at).seconds / 60, 2)
            print('Browse node {} already enqueued ({} minutes ago)'.format(browse_node.tree_to_string(), minutes))

        enqueues_remaining -= pending_nodes_query.count()
        if enqueues_remaining <= 0:
            break

        for browse_node in possible_nodes_query.all():
            enqueues_remaining -= 1
            print('Enqueuing {}; enqueued at: {}, searched at: {}; enqueues remaining: {}'.format(
                browse_node.tree_to_string(), browse_node.enqueued_at, browse_node.searched_at, enqueues_remaining))

            browse_node.enqueued_at = now
            build_products_from_search.apply_async(args=['Electronics'],
                                                   kwargs=dict(browse_node_id=browse_node.id, refresh_existing=True),
                                                   expires=3660)

            if enqueues_remaining == 0:
                print('Reached queue limit')
                done = True
                break

        if done:
            break

        layer_index += 1


@app.task()
def enqueue_browse_node_if_necessary():
    print('=========================================================')
    session = Session()

    try:
        enqueue_next_browse_nodes(session, 12)
        session.commit()
    finally:
        session.close()


@app.task()
def update_layers():
    session = Session()

    try:
        total = session.query(BrowseNode).count()
        layers = get_browse_node_layers(session)

        print('Total browse nodes: {}'.format(total))
        print('Layers: [{}]'.format([len(layer) for layer in layers]))

        for layer_index, layer in enumerate(layers):
            for browse_node in layer:
                browse_node.layer = layer_index

        session.commit()
    finally:
        session.close()
