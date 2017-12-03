task_acks_late = True
worker_prefetch_multiplier = 1

task_routes = {
    'products.amazon.query.get_item_datafeedr_prices': 'datafeedr',
    'products.amazon.query.get_item_datafeedr_prices_important': 'datafeedr',
    'products.amazon.query.download_datafeedr_price_webpage': 'datafeedr_webpages',
    'products.amazon.crawl.enqueue_browse_node_if_necessary': 'crawler',
    'products.amazon.crawl.update_layers': 'crawler',
}

beat_schedule = {
    'enqueue_browse_node_if_necessary': {
        'task': 'products.amazon.crawl.enqueue_browse_node_if_necessary',
        'schedule': 10.0,
        'args': (),
        'options': {
            'expires': 15.0
        }
    },
    'update_layers': {
        'task': 'products.amazon.crawl.update_layers',
        'schedule': 3600 * 3,
        'args': (),
        'options': {
            'expires': 3600
        }
    },
    # 'get_item_datafeedr_prices': {
    #     'task': 'products.amazon.query.get_item_datafeedr_prices_important',
    #     'schedule': 30.0,
    #     'args': (),
    #     'options': {
    #         'expires': 29.0
    #     }
    # }
}
