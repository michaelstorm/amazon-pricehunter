from pricehunter.models import Item, session
from .browse_nodes_to_graphviz import print_browse_nodes

out = open('browse_nodes.dot', 'w')
out.write("digraph browse_nodes {\n")

for item in session.query(Item).all():
    out.write('\t"{}" [label="{}\n{}"];\n'.format(item.asin, item.title.replace('"', '\\"'), item.asin))
    for browse_node in item.browse_nodes:
        out.write('\t"{}" -> "{}";\n'.format(item.asin, browse_node.id))

out.write('\t{ rank=same; ')
for item in session.query(Item).all():
    out.write('"{}" '.format(item.asin))
out.write('}\n')

print_browse_nodes(out)

out.write("}")
