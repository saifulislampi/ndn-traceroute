#!/usr/bin/env python3

import argparse
import sys
import pydot
import itertools

from pathlib import Path
from os import system

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
                    src.faces.add(dest)
                    dest.faces.add(src)
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

    def build(self, template, build_dir=None):
        if build_dir is None:
            build_dir = Path('build')

        if not build_dir.is_dir():
            build_dir.mkdir()

        self.write_configs(build_dir, template)
        self.write_compose(build_dir)

    def write_configs(self, build_dir, template):
        if not template.is_file():
            raise RuntimeError(f'{template} not found')

        config_dir = Path(build_dir, 'configs')
        if not config_dir.is_dir():
            config_dir.mkdir()

        for node in self.nodes:
            target = Path(config_dir, node.name + '.conf')
            system(f'sed -e "52s|###NAME###|/nfd/{node.name}|" {template} > {target}')

    def write_compose(self, build_dir):
        lines = []
        lines.append('# this file was AUTO-GENERATED')
        lines.append('name: ndn-net')
        lines.append('')

        lines.append('services:')
        for node in self.nodes:
            for line in node.service_lines():
                lines.append('  ' + line)

        lines.append('')

        lines.append('networks:')
        lines.append('  ndn-net:')

        target = Path(build_dir, 'compose.yaml')
        with target.open('w') as fp:
            fp.write('\n'.join(lines))

class NFD_Node():
    def service_headers(self):
        return (
            '{}:'.format(self.name),
            '  image: nfd',
            '  container_name: {}'.format(self.name),
            '  networks:',
            '    ndn-net:',
            '  volumes:',
            '    - ./configs/{}.conf:/etc/ndn/nfd.conf:ro'.format(self.name),
            '  command: >',
            '    sh -c "/start-nfd.sh;',
            '           sleep 5;'
        )

    def face_commands(self):
        return {f'nfdc face create tcp://{face.name};' for face in self.faces}

class NFD_Producer(NFD_Node):
    def __init__(self, name, prefix):
        self.name = name
        self.prefix = prefix
        self.faces = set()

    def service_lines(self):
        return (
          *(self.service_headers()),
          *('           ' + command for command in self.face_commands()),
            '           /producer/build/simple-producer {} {}"'.format(self.name, self.prefix)
        )

class NFD_Forwarder(NFD_Node):
    def __init__(self, name):
        self.name = name
        self.faces = set()
        self.routes = {}

    def add_route(self, prefix: str, node: NFD_Node):
        if type(node) == NFD_Client:
            raise RuntimeError(f'cannot route towards client: {node.name}')

        self.routes[prefix] = node

    def service_lines(self):
        return (
          *(self.service_headers()),
          *('           ' + command for command in self.face_commands()),
          *('           ' + command for command in self.route_commands()),
            '           tail -f /dev/null"'
        )

    def route_commands(self):
        return {f'nfdc route add {prefix} tcp://{node.name};' for prefix, node in self.routes.items()}

class NFD_Client(NFD_Forwarder):
    pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='build-net.py',
        description='A program to build a docker compose file for an NDN network given a .dot file specifying the network',
    )

    parser.add_argument('GRAPH', help='.dot file of the network', type=Path)
    parser.add_argument('CONFIG_TEMPLATE', help='special NFD configuration template file', type=Path)

    args = parser.parse_args()

    graphs = pydot.graph_from_dot_file(args.GRAPH)

    network = NFD_Network(graphs[0])
    network.build(args.CONFIG_TEMPLATE)
