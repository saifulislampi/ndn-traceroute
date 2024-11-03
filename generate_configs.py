#!/usr/bin/env python3

import sys
import pydot
from typing import Union, TypeVar
import itertools

NFD_Node = TypeVar("Union[NFD_Producer, NFD_Client, NFD_Forwarder]")

class NFD_Network():
    def __init__(self, graph):
        self.nodes = set()

        for node in graph.get_nodes():
            self.create_node(node)

        for edge in graph.get_edges():
            e = dict(zip(('src', 'dest'), edge.obj_dict['points']))

            for node in ('src', 'dest'):
                try:
                    e[node] = next(n for n in self.nodes if n.name == e[node])
                except StopIteration:
                    raise RuntimeError(f'edge {edge} has undefined node: {e[node]}')

            src  = e['src']
            dest = e['dest']

            if type(src) == NFD_Producer:
                raise RuntimeError(f'cannot route from producer: {src.name}')
            elif type(src) in (NFD_Client, NFD_Forwarder):
                try:
                    prefixes = pydot.dot_parser.QuotedString('"').search_string(edge.obj_dict['attributes']['label'])[0][0].split('\n')
                except KeyError:
                    raise RuntimeError(f'edge missing label attr: {edge}')

                for prefix in prefixes:
                    src.add_route(prefix, dest)

    def create_node(self, node: pydot.core.Node):
        name = node.obj_dict['name']

        try:
            role = pydot.dot_parser.QuotedString('"').search_string(node.obj_dict['attributes']['class'])[0][0]
        except KeyError:
            raise RuntimeError(f'must define class for node {name}')

        if role == 'client':
            self.nodes.add(NFD_Client(name))
        elif role == 'producer':
            self.nodes.add(NFD_Producer(name))
        elif role == 'forwarder':
            self.nodes.add(NFD_Forwarder(name))
        else:
            raise RuntimeError(f'unknown class: {role}')

    def __repr__(self):
        nodes_str = '\n'.join('\n'.join(' '*4 + line for line in repr(node).split('\n')) for node in self.nodes)
        return f'NFD_Network(\n{nodes_str}\n)'

class NFD_Producer():
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f'{type(self).__name__}(name={self.name})'

class NFD_Forwarder():
    def __init__(self, name):
        self.name = name
        self.routes = {}

    def add_route(self, prefix: str, node: NFD_Node):
        if type(node) == NFD_Client:
            raise RuntimeError(f'cannot route towards client: {node.name}')

        self.routes[prefix] = node

    def __repr__(self):
        return f'{type(self).__name__}(name={self.name},\n' + ''.join(' '*4 + f'{prefix} --> {node.name}\n' for prefix, node in self.routes.items()) + ')'

class NFD_Client(NFD_Forwarder):
    pass

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('expecting filename', file=sys.stderr)
        exit(1)

    filename = sys.argv[1]
    graphs = pydot.graph_from_dot_file(filename)
    G = graphs[0]
    print(NFD_Network(G))
