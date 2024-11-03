#!/usr/bin/env python3

import sys
import os
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

        qs = pydot.dot_parser.QuotedString('"')
        try:
            role = qs.search_string(node.obj_dict['attributes']['class'])[0][0]
        except KeyError:
            raise RuntimeError(f'must define class for node {name}')

        if role == 'client':
            self.nodes.add(NFD_Client(name))
        elif role == 'producer':
            prefix = qs.search_string(node.obj_dict['attributes']['data'])[0][0]
            self.nodes.add(NFD_Producer(name, prefix))
        elif role == 'forwarder':
            self.nodes.add(NFD_Forwarder(name))
        else:
            raise RuntimeError(f'unknown class: {role}')

    def build(self):
        self.build_configs()
        self.build_compose()

    def build_configs(self):
        for node in self.nodes:
            if type(node) is NFD_Producer:
                continue

            lines = []
            for prefix, dest in node.routes.items():
                lines.append(f'route add {prefix} tcp://{dest.name}')

            if not os.path.isdir('build/configs'):
                os.mkdir('build/configs')

            with open(f'build/configs/{node.name}.conf', 'w') as fp:
                fp.write('\n'.join(lines))

    def build_compose(self):
        lines = []
        lines.append('# this file was AUTO-GENERATED')
        lines.append('name: nfdnet')
        lines.append('')

        lines.append('services:')
        for node in self.nodes:
            for line in node.service_lines().split('\n'):
                lines.append('  ' + line)

        lines.append('')

        lines.append('configs:')
        for node in self.nodes:
            for line in node.config_lines().split('\n'):
                if line:
                    lines.append('  ' + line)

        lines.append('')
        lines.append('networks:')
        lines.append('  nfdnet:')

        with open('build/compose.yaml', 'w') as fp:
            fp.write('\n'.join(lines))

    def __repr__(self):
        nodes_str = '\n'.join('\n'.join(' '*4 + line for line in repr(node).split('\n')) for node in self.nodes)
        return f'NFD_Network(\n{nodes_str}\n)'

class NFD_Producer():
    def __init__(self, name, prefix):
        self.name = name
        self.prefix = prefix
        self.cmd = f'/simple-producer {self.name} {self.prefix}'

    def service_lines(self):
        return f'''{self.name}:
  container_name: "{self.name}"
  image: nfd
  networks:
    - nfdnet
  healthcheck:
    test: "[ -e /run/nfd/nfd.sock ]"
    interval: 50ms 
    timeout: 10ms
    retries: 200
  command: ["/usr/bin/nfd --config /config/nfd.conf & while [ ! -e /run/nfd/nfd.sock ]; do :; done; {self.cmd}"]'''

    def config_lines(self):
        return ''

    def __repr__(self):
        return f'{type(self).__name__}(name={self.name}, prefix={self.prefix})'

class NFD_Forwarder():
    cmd = 'sleep infinity'

    def __init__(self, name):
        self.name = name
        self.routes = {}

    def service_lines(self):
        return f'''{self.name}:
  container_name: "{self.name}"
  image: nfd
  networks:
    - nfdnet
  configs:
    - {self.name}.conf
  healthcheck:
    test: "[ -e /run/nfd/nfd.sock ]"
    interval: 50ms 
    timeout: 10ms
    retries: 200
  depends_on:
''' + ''.join(f'''    {dest.name}:
      condition: service_healthy
''' for dest in self.routes.values()) + f'''  command: ["/usr/bin/nfd --config /config/nfd.conf & while [ ! -e /run/nfd/nfd.sock ]; do :; done; /usr/bin/nfdc -f /{self.name}.conf; {self.cmd}"]'''

    def config_lines(self):
        return f'''{self.name}.conf:
  file: configs/{self.name}.conf'''
    
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
    
    NFD_Network(G).build()
