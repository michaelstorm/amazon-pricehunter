from pricehunter.models import BrowseNode, session

def print_browse_nodes(out, browse_nodes, min_items=None):
    for browse_node in browse_nodes:
        items_count = browse_node.items.count()
        if min_items is None or items_count > min_items:
            name = browse_node.name if browse_node.name else "<null>"
            out.write('\t{} [label="{} ({})\n{}"];\n'.format(browse_node.id, name, items_count, browse_node.id))

            print_browse_nodes(out, browse_node.ancestors)

            for ancestor in browse_node.ancestors:
                out.write('\t{} -> {};\n'.format(browse_node.id, ancestor.id))


if __name__ == "__main__":
    out = open('browse_nodes.dot', 'w')
    out.write("strict digraph browse_nodes {\n")
    print_browse_nodes(out, session.query(BrowseNode).all(), 100)
    out.write("}")
