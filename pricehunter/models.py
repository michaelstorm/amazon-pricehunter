import os
import os.path
from sqlalchemy import create_engine, Column, DateTime, ForeignKey, Float, Integer, String, Table, \
                       Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import sessionmaker, relationship
from urllib.parse import urlparse


engine = create_engine('postgresql://postgres:password@localhost:5432/products', echo=False)

Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()

class ItemBrowseNode(Base):
    __tablename__ = 'item_browse_nodes'

    id = Column(Integer(), primary_key=True)
    item_id = Column(String(16), ForeignKey('items.asin'), index=True)
    item = relationship("Item")
    browse_node_id = Column(String(16), ForeignKey('browse_nodes.id'), index=True)
    browse_node = relationship("BrowseNode")

class ItemSalesRank(Base):
    __tablename__ = 'item_sales_rank'

    id = Column(Integer(), primary_key=True)
    item_id = Column(String(16), ForeignKey('items.asin'), index=True)
    item = relationship("Item", backref="item_sales_ranks")
    browse_node_id = Column(String(16), ForeignKey('browse_nodes.id'), index=True)
    browse_node = relationship("BrowseNode")
    sales_rank = Column(Integer())
    timestamp = Column(DateTime())

class Item(Base):
    __tablename__ = 'items'

    asin = Column(String(16), primary_key=True)
    product_group = Column(Text())
    title = Column(Text())
    upc = Column(Text())
    xml = Column(Text())
    amazon_prices = relationship("AmazonPrice", lazy="dynamic")
    datafeedr_prices = relationship("DatafeedrPrice", lazy="dynamic")
    datafeedr_prices_searched_at = Column(DateTime())
    browse_nodes = relationship('BrowseNode', lazy="dynamic", secondary='item_browse_nodes')
    ranked_browse_nodes = relationship('BrowseNode', lazy="dynamic", secondary='item_sales_rank')

    def min_layer(self, session, min_timestamp):
        return (
            session.query(func.min(BrowseNode.layer))
                .select_from(Item)
                .join(ItemSalesRank, BrowseNode)
                .filter(Item.asin == self.asin)
                .filter(ItemSalesRank.timestamp >= min_timestamp)
                .group_by(Item.asin)
                .scalar()
        )

browse_nodes_association = Table('browse_nodes_association', Base.metadata,
    Column('left_id', String(16), ForeignKey('browse_nodes.id'), index=True),
    Column('right_id', String(16), ForeignKey('browse_nodes.id'), index=True)
)

class BrowseNode(Base):
    __tablename__ = 'browse_nodes'

    id = Column(String(16), primary_key=True)
    name = Column(Text())
    search_index = Column(Text())
    ancestors = relationship("BrowseNode",
                             lazy="dynamic",
                             secondary=browse_nodes_association,
                             primaryjoin=id == browse_nodes_association.c.left_id,
                             secondaryjoin=id == browse_nodes_association.c.right_id)
    item_sales_ranks = relationship('ItemSalesRank', lazy="dynamic")
    items = relationship('Item', lazy="dynamic", secondary='item_browse_nodes')
    enqueued_at = Column(DateTime())
    searched_at = Column(DateTime())
    disabled = Column(Boolean(), default=False)
    layer = Column(Integer())

    def tree_to_string(self, separator='\n    '):
        def summarize_node(n):
            name = '"{}"'.format(n.name) if n.name else "<null>"
            return '{} {}'.format(n.id, name)
            # return '{} {} ({})'.format(n.id, name, n.items.count())

        node = self
        out = summarize_node(node)

        node = node.ancestors.first()
        if node:
            out += separator

        while node is not None:
            out += summarize_node(node)

            next_node = node.ancestors.first() if node.ancestors.count() > 0 else None
            if next_node:
                out += separator

            node = next_node

        return out

class AmazonPrice(Base):
    __tablename__ = 'amazon_prices'

    id = Column(Integer(), primary_key=True)
    item_id = Column(String(16), ForeignKey('items.asin'), index=True)
    item = relationship("Item", uselist=False)
    price = Column(Float())
    quantity = Column(Integer())
    condition = Column(String(16))
    timestamp = Column(DateTime())
    merchant_id = Column(Integer())

class DatafeedrPrice(Base):
    __tablename__ = 'datafeedr_prices'

    id = Column(Integer(), primary_key=True)
    item_id = Column(String(16), ForeignKey('items.asin'), index=True)
    item = relationship("Item", uselist=False)
    domain_id = Column(Integer(), ForeignKey('domains.id'), index=True)
    domain = relationship("Domain", uselist=False, back_populates="datafeedr_prices")

    price = Column(Float())
    converted_price = Column(Float())
    merchant_id = Column(String(32))
    condition = Column(String(16))
    _id = Column(String(32))
    timestamp = Column(DateTime())
    url = Column(Text())
    raw = Column(Text())
    webpage = Column(Text())

    def get_webpage_directory(self, timestamp):
        date = timestamp.strftime('%Y-%m-%d')
        domain = urlparse(self.url).netloc
        return os.path.join(os.getcwd(), 'prices', date, self.item.asin, domain)

    def get_webpage_path(self, timestamp):
        dirname = self.get_webpage_directory(timestamp)
        return os.path.join(dirname, '{}.html'.format(self.id))

class Domain(Base):
    __tablename__ = 'domains'

    id = Column(Integer(), primary_key=True)
    datafeedr_prices = relationship("DatafeedrPrice", lazy="dynamic")
    name = Column(Text(), nullable=False)
    trusted = Column(Boolean(), default=False, nullable=False)
