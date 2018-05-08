#!/usr/bin/env python
import yaml
import argparse
import os
import sys
import base64
import re

from os import listdir
from os.path import isfile, join

kube_path = "{}/.kube".format(os.getenv('HOME'))

class ConfigFile(object):

    def __init__(self, cluster_name, namespace_name):
        self.file="{}/config|{}|{}".format(kube_path, cluster_name, namespace_name)

    def delete(self):
        os.remove(self.file)

    def write(self, data):
        with open(self.file, 'w') as fd:
            fd.write(yaml.dump(data, default_flow_style=False))
    
    def load(self):
        with open(self.file, 'r') as fd:
            return yaml.load(fd)
    

    @staticmethod
    def list(cluster=None):
        if cluster is not None:
            rgx = '^config\|{}\|'.format(cluster)
        else:
            rgx = '^config\|'
        config_files = [f for f in listdir(kube_path) if isfile(join(kube_path, f)) and re.match(rgx, f)]

        ret = {}
        for c in config_files:
            data = c.split('|')
            if data[1] in ret:
                ret[data[1]].append(data[2])
            else:
                ret[data[1]]=[data[2]]

        return ret

class Context(object):
    def __init__(self, name, cluster, user, namespace='default'):
        self.name = name
        self.cluster = cluster
        self.namespace = namespace
        self.user = user
        self._configfile = ConfigFile(self.cluster.name, self.namespace)

    def add(self):
        self._configfile.write("data")

    def delete(self):
        self._configfile.delete()

    def get(self):
        return {
            'apiVersion': 'v1',
            'kind': 'Config',
            'preferences': {},
            'clusters': [self.cluster.get()],
            'users': [self.user.get()],
            'contexts': [
                {
                
                    'context': {'cluster': self.cluster.name, 'user': self.user.name, 'namespace': self.namespace},
                    'name': self.name,
                }
            ],
            'current-context': self.name,
        }

    def save(self):
        self._configfile.write(self.get())

    @classmethod
    def load(cls, cluster_name, namespace='default'):
        
        configfile = ConfigFile(cluster_name, namespace)
        data = configfile.load()
        name = data['contexts'][0]['name']
        cluster = Cluster(
            data['clusters'][0]['name'],
            data['clusters'][0]['cluster']['certificate-authority-data'],
            data['clusters'][0]['cluster']['server']
            )
        user = User(data['users'][0]['name'], data['users'][0]['user'])
        return cls(name, cluster, user, namespace)


class Cluster(object):
    def __init__(self, name, cacrt, server):
        self.name = name
        self.cacrt = cacrt
        self.server = server

    def get(self):
        return {'cluster': {'certificate-authority-data': self.cacrt, 'server': self.server}, 'name': self.name}

class User(object):
    def __init__(self, name, data):
        self.name = name
        self.data = data

    def get(self):
        return {'name': self.name, 'user': self.data}


def split_config(arguments):
    with open(args.config) as fd:
        data = yaml.load(fd)

    cluster={}
    user={}
    contexts=[]

    for c in data.get('clusters', []):
        if 'certificate-authority' in c['cluster']:
            with open(c['cluster']['certificate-authority']) as fd:
                c['cluster']['certificate-authority-data'] = base64.b64encode(bytes(fd.read())).decode()
        cluster[c['name']] = Cluster(c['name'], c['cluster']['certificate-authority-data'], c['cluster']['server'])

    for u in data.get('users', []):
        user[u['name']] = User(c['name'], u['user'])

    for c in data.get('contexts', []):
        namespace = c['context'].get('namespace', 'default')
        if not namespace == 'default':
            contexts.append(Context(c['name'], cluster[c['context']['cluster']], user[c['context']['user']], 'default'))
        contexts.append(Context(c['name'], cluster[c['context']['cluster']], user[c['context']['user']], namespace))

    for c in contexts:
        c.save()


def add_namespace(arguments):
    ctx = Context.load(arguments.cluster)
    newctx = Context(ctx.name, ctx.cluster, ctx.user, arguments.namespace)
    newctx.save()


def del_namespace(arguments):
    c = ConfigFile(arguments.cluster, arguments.namespace)
    c.delete()


def rename_cluster(arguments):
    l = ConfigFile.list(arguments.old)
    for n in l[arguments.old]:
        ctx = Context.load(arguments.old, n)
        ctx.cluster.name = arguments.new
        ctx.name = arguments.new
        newctx = Context(ctx.name, ctx.cluster, ctx.user, n)
        newctx.save()
        ctx.delete()


def delete_cluster(arguments):
    l = ConfigFile.list(arguments.cluster)
    for n in l[arguments.cluster]:
        c = ConfigFile(arguments.cluster, n)
        c.delete()
    pass


def list_clusters(arguments):
    cluster_list = ConfigFile.list()

    max_length = len(max(cluster_list.keys(), key=len))+3
    line = '%-{}s %-20s'.format(max_length)

    for c in cluster_list.keys():
        if arguments.full:
            for n in cluster_list[c]:
                print(line % (c, n))
        else:
                print(c)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Tool for managing multiple kubeconfig files')
    subparsers = parser.add_subparsers(title="action", dest="action" )

    sc_parser = subparsers.add_parser("split-config")
    sc_parser.add_argument('--config', '-c', dest='config', type=str, help='config file to use', default='{}/config'.format(kube_path))

    lc_parser = subparsers.add_parser("list-clusters")
    lc_parser.add_argument('--full', '-f', dest='full', action='store_true', help='full listing')

    an_parser = subparsers.add_parser("add-namespace")
    an_parser.add_argument('cluster', type=str, help='cluster name')
    an_parser.add_argument('namespace', type=str, help='namespace to create')

    dn_parser = subparsers.add_parser("del-namespace")
    dn_parser.add_argument('cluster', type=str, help='cluster name')
    dn_parser.add_argument('namespace', type=str, help='namespace to delete')

    dc_parser = subparsers.add_parser("delete-cluster")
    dc_parser.add_argument('cluster', type=str, help='cluster to delete')
    
    rc_parser = subparsers.add_parser("rename-cluster")
    rc_parser.add_argument('old', type=str, help='cluster to rename')
    rc_parser.add_argument('new', type=str, help='new cluster name')

    args = parser.parse_args()

    if args.action is None:
        parser.print_usage()
        sys.exit(1)

    action = args.action.replace("-","_")
    possibles = globals().copy()
    method = possibles.get(action, None)
    if method is None:
        raise Exception("unable to find method {}".format(action))
    
    method(args)

