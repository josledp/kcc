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
            fd.write(yaml.dump(data))

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
            'kind': 'config',
            'preferences': {},
            'clusters': self.cluster.get(),
            'users': self.user.get(),
            'contexts': {
                'context': {'cluster': self.cluster.name, 'user': self.user.name, 'namespace': self.namespace},
                'name': self.name},
            'current-context': self.name,
        }

    def save(self):
        self._configfile.write(self.get())


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
                c['cluster']['certificate-authority-data'] = base64.b64encode(bytes(fd.read(),'utf-8')).decode()
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
    print(arguments)
    pass


def del_namespace(arguments):
    print(arguments)
    pass


def rename_cluster(arguments):
    print(arguments)
    pass


def delete_cluster(arguments):
    print(arguments)
    pass


def list_clusters(arguments):
    config_files = [f for f in listdir(kube_path) if isfile(join(kube_path, f)) and re.match('^config\|', f)]
    last=''
    for c in config_files:
        data=c.split('|')
        if arguments.full:
            print('%50s %20s' % (data[1],data[2]))
        else:
            if data[1] != last:
                print('{}'.format(data[1]))
                last=data[1]

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

