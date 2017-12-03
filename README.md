# Overview

Amazon Pricehunter is a "trading" engine that finds price differences between Amazon products and
offers for those same products elsewere on the Internet. It crawls Amazon's Product Advertising API
using roughly the following procedure:

1) Every N hours:
  1) For each unvisited product category in the database, ordered from "highest-level" to "lowest-level":
    1) Retrieve the top N products in that category
    2) For each product in that category:
        1) Retrieve product details
        2) Save product details and prices to the database
        3) Save any newly-discovered categories to which the product belongs to the database
        4) Retrieve offers from other merchants from the Datafeedr API for matching UPCs or EINs
        5) For each alternative offer:
        	1) Scrape a snapshot of the offer on the merchant's web site and save it to disk

Amazon Pricehunter is not endorsed by or affiliated with Amazon.com, the company.

## Output

A big ol' table comparing "interesting" products with their best competing offers. It looks like
this (with middle rows elided):

```
+------------+-------+------------+------------------------------------------------+----------------------------------------------------+---------+-----------+-----------+-------------+---------------+--------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------+
| ASIN       | Layer | Sales Rank | Browse nodes                                   | Title                                              | Amazon  | Condition | Datafeedr | Cond        | Diff          | Webpage                                                                              | URL                                                                                                                        |
+------------+-------+------------+------------------------------------------------+----------------------------------------------------+---------+-----------+-----------+-------------+---------------+--------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------+
| B019VM3CPW | 0     | 0          | 7141123011 "Clothing, Shoes & Jewelry"         | Fitbit Blaze Smart Fitness Watch, Black, Silver, L | 187.10  | New       | 135.86    | new         | 51.24 (27%)   | file:///home/michael/ebooks/prices/2017-11-12/B019VM3CPW/www.very.co.uk/222530.html  | http://www.very.co.uk/fitbit-alta-fitness-tracker/1600068913.prd                                                           |
|            |       |            |                                                |                                                    |         |           | 135.86    | new         | 51.24 (27%)   | file:///home/michael/ebooks/prices/2017-11-12/B019VM3CPW/www.very.co.uk/222532.html  | http://www.very.co.uk/fitbit-alta-fitness-tracker/1600068913.prd?sku=sku20127404                                           |
| B00FLYWNYQ | 0     | 0          | 2619525011 "Appliances"                        | Instant Pot DUO60 6 Qt 7-in-1 Multi-Use Programmab | 67.99   | Used      | 14.99     | new         | 53.00 (78%)   | file:///home/michael/ebooks/prices/2017-11-12/B00FLYWNYQ/www.bonanza.com/221162.html | https://www.bonanza.com/listings/AC-Power-Cord-for-Instant-Pot-IP-DUO60-IP-DUO50-Smart-and-Ultra-Pressure-Cooker/465982322 |
|            |       |            | 1055398 "Home & Kitchen"                       |                                                    |         |           |           |             |               |                                                                                      |                                                                                                                            |
| B01019T6O0 | 0     | 1          | 229534 "Software"                              | Microsoft Windows 10 Home USB Flash Drive          | 105.00  | New       | 19.39     | new         | 85.61 (82%)   | file:///home/michael/ebooks/prices/2017-11-12/B01019T6O0/www.bonanza.com/217568.html | https://www.bonanza.com/listings/Windows-10-Home-32-64-Bit-Full-Retail-Edition-Full-Edition-Lifetime/500982763             |
|            |       |            |                                                |                                                    |         |           | 19.39     | new         | 85.61 (82%)   | file:///home/michael/ebooks/prices/2017-11-12/B01019T6O0/www.bonanza.com/217575.html | https://www.bonanza.com/listings/Windows-10-Home-32-64-Bit-Fast-Download-Lifetime-Official/503201958                       |
|            |       |            |                                                |                                                    |         |           | 20.27     | new         | 84.73 (81%)   | file:///home/michael/ebooks/prices/2017-11-12/B01019T6O0/www.bonanza.com/217572.html | https://www.bonanza.com/listings/Windows-10-Enterprise-32-64-Bit-Full-Retail-Edition/508724013                             |
|            |       |            |                                                |                                                    |         |           | 20.27     | new         | 84.73 (81%)   | file:///home/michael/ebooks/prices/2017-11-12/B01019T6O0/www.bonanza.com/217573.html | https://www.bonanza.com/listings/Genuine-Product-Windows-10-Enterprise-32-64-Bit-Full-Retail-Edition/512674412             |
| B075N7RDTM | 0     | 5          | 172282 "Electronics"                           | Nintendo Switch - Super Mario Odyssey Edition      | 459.99  | New       | 379.99    |             | 80.00 (17%)   | file:///home/michael/ebooks/prices/2017-11-12/B075N7RDTM/www.walmart.com/215372.html | http://www.walmart.com/ip/Nintendo-Switch-Super-Mario-Odyssey-Edition/56205102                                             |
|            |       |            | 468642 "Video Games"                           |                                                    |         |           |           |             |               |                                                                                      |                                                                                                                            |
.            .       .            .                                                .                                                    .         .           .           .             .               .                                                                                      .                                                                                                                            .
.            .       .            .                                                .                                                    .         .           .           .             .               .                                                                                      .                                                                                                                            .
.            .       .            .                                                .                                                    .         .           .           .             .               .                                                                                      .                                                                                                                            .
| B006QMGSDO | 3     | 88         | 3563987011 "Plant Covers"                      | Nuvue Winter Shrub Cover Hunter Green Fiberglass   | 114.25  | BuyButton | 18.11     | new         | 96.14 (84%)   |                                                                                      | http://www.homedepot.ca/en/home/p.1000709901.html                                                                          |
|            |       |            |     3610851 "Gardening & Lawn Care"            |                                                    |         |           |           |             |               |                                                                                      |                                                                                                                            |
|            |       |            |     3238155011 "Categories"                    |                                                    |         |           |           |             |               |                                                                                      |                                                                                                                            |
|            |       |            |     2972638011 "Patio, Lawn & Garden"          |                                                    |         |           |           |             |               |                                                                                      |                                                                                                                            |
+------------+-------+------------+------------------------------------------------+----------------------------------------------------+---------+-----------+-----------+-------------+---------------+--------------------------------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------+
```

## Purpose

It was an experiment. The goal was to list these products on Amazon at a slight discount to the
prevailing price, and then pocket the difference in price from wherever I'd bought them. No
inventory to buy or hold, no demand to predict. Just pure arbitrage, minus shipping costs.

For my purposes, the experiment failed. It turned out that the set of products that are available at
an interesting discount (say at least $30, to recoup costs and make it worthwhile), are frequently
bought, are small enough to be easily shipped (i.e., not a TV), are available from a non-sketchy
seller, and (this was unexpectedly important) do not require special permission from Amazon to sell
is small. Not nothing, but not enough to keep my interest going.

Perhaps someone else will find a purpose for it, though: get rich? Annoy Amazon? The opportunities
are endless. Please let me know if you do something fun with it.

## Crawling

How do you iterate through all of Amazon's products? The most naive answer is, "one-by-one," but (a)
the API rate limit won't let you get close to that, and (b) the API doesn't actually support that
type of query. You can't simply paginate through all products; you must form an actual search query
of some kind: keywords, IDs, categories, etc.

So: knowing nothing about the products on Amazon, how does one form a "starter" query, a procedure
to repeatedly query Amazon for more products, and target those queries such that they result in
products you're interested in? Pricehunter does this with product categories -- what Amazon calls
"browse nodes". Browse nodes have a name, ID, zero or many parents, and zero or many children. Given
a starting browse node, e.g. "Electronics", it will iterate through its top N (by default 100)
items, discovering new browse nodes from those items and adding them to the queue. Browse nodes at a
higher level than others are searched first. A browse node's level is calculated as the minimum
number of steps up its chain of parents to a node without a parent.

Browse nodes' level also comes into play when ranking products by popularity. Since the Product
Advertising API gives no global sales ranking or data by which we can derive it, we use the minimum
level of all browse nodes a product belongs to as the first item in a tuple defining its sort order.
The intuition is that products that appear in the top N sales for a highly-ranked category, e.g. the
#10 seller in Electronics, are generally more popular than higher-ranked sales in lower-ranked
categories, e.g. the #5 seller in Smart Watches and Fitness Trackers. In that example, since
Electronics is a level 0 category and Smart Watches is around level 2, the #10 seller would outrank
the #5 seller when printing results.

## Performance

The Product Advertising API rate limit is 1 request per second, which is... low. To get around this
limit, Pricehunter round-robins between multiple API accounts for each request. For example, if one
used 8 accounts in parallel, the effective request rate would be 8 requests per second. This is
probably against the API Terms of Service, so of course one would never do this.

Pricehunter ekes out a bit more parallelism by running independent tasks, such as retrieving
Datafeedr offers and scraping offer web pages, in separate Celery tasks. Those tasks are scheduled
on different queues than Product Advertising API retrieval tasks, to allow finer-grained worker
distribution.

## Testing

Lol none. (Like I said, it was an experiment.)

# Usage

## Installation

Clone the repo and install dependencies with:

```
$ git clone https://github.com/michaelstorm/pricehunter.git
$ cd pricehunter
$ virtualenv -p python3 venv
$ source venv/bin/activate
$ pip install -r requirements.txt
```

## Credentials

You need you some Product Advertising API credentials. Follow the instructions
[here](https://docs.aws.amazon.com/AWSECommerceService/latest/DG/becomingDev.html) to set up an
Amazon Seller account and get them.

If you want to get competing offers from other websites, you'll need a [Datafeedr
subscription](https://members.datafeedr.com/subscribe).

Once you have them, create `setup_env.sh` with the following contents:

```
#!/bin/bash
source venv/bin/activate

export DATAFEEDR_ACCESS_KEY = 'YOUR_DATAFEEDR_ACCESS_KEY'
export DATAFEEDR_SECRET_KEY = 'YOUR_DATAFEEDR_SECRET_KEY'

export AWS_REGION='YOUR_AWS_REGION' # e.g. us-west-1

export AWS_ACCESS_KEY_ID_0="YOUR_ACCESS_KEY_ID"
export AWS_SECRET_ACCESS_KEY_0="YOUR_SECRET_ACCESS_KEY"
export AWS_STORE_ID_0="YOUR_STORE_ID"
```

Repeat the `AWS_*` block with incrementing indices to use more accounts.

Then run `$ source setup_env.sh` (**not** `./setup_env.sh`) in every shell you'll be working with
Pricehunter in.

## Workers

### Query workers

Query workers run Product Advertising API queries. To avoid multiple jobs using the same API
credentials simultaneously, each worker process has its own set of credentials, and that worker
executes one job at a time. (This doesn't slow down the process, since the per-credential rate limit
is a far more onerous bottleneck.) One must therefore create one worker per Amazon Seller account to
maximize performance, e.g.:

```
$ ./run_query_worker.sh 0
$ ./run_query_worker.sh 1
$ ./run_query_worker.sh 2
```

where `0`, `1`, and `2` are the indices of the `AWS_*` credentials blocks in `setup_env.sh`.
**Multiple workers must not share an index.** An arbitrary number of workers are supported; the only
limit is the number of Seller accounts you have.

### Crawler workers

The crawler worker schedules browse nodes to be queried, reschedules query jobs that have died, and
periodically calculates the levels of browse nodes. Only one crawler worker is necessary. I haven't
tested with multiple crawler workers. It can be started with:

```
$ ./run_crawler_worker.sh
```

### Datafeedr workers

Datafeedr workers, true to name, query Datafeedr for competing offers by UPC or EIN. Any number can
be run simultaneously by executing:

```
$ ./run_datafeedr_worker.sh
```

### Datafeedr webpage workers

Datafeedr webpage workers scrape the contents of offer pages and save them to disk. This allows one
to verify whether an offer has changed since it was returned by Datafeedr, which makes it easier to
verify whether Datafeedr scrapes a particular merchant's offers correctly. Any number can be run
simultaneously by executing:

```
$ ./run_datafeedr_webpage_worker.sh
```

### celerybeat

The celerybeat process schedules periodic tasks. For convenience, it can be invoked via:

```
$ ./beat.sh
```

## Seeding the crawler

The crawler needs at least one browse node to start crawling. If you have a known browse node ID,
you can supply it with:

```
$ python -m scripts.search_browse_nodes SEARCH_INDEX BROWSE_NODE_ID...
```

Where `SEARCH_INDEX` is e.g. "Electronics". See
[here](https://docs.aws.amazon.com/AWSECommerceService/latest/DG/localevalues.html) for a list of
possible search indices.

Otherwise, you can perform a keyword product search. The resulting products will be mined for browse
nodes:

```
$ python -m scripts.search_keywords SEARCH_INDEX "SEARCH_STRING"
```

## Creating output

After sufficient data has been collected, run:

```
$ python -m scripts.print_differences > output.txt
```

Options for the output can be tweaked in `pricehunter.amazon.compute.compute_ranked_items`. If you
get no output, try making adjustments there.
