import yaml
import argparse
import os
import sys
import base64


class ConfigFile(object):

    def __init__(self, cluster_name, namespace_name):
        self.file="{}/.kube/config|{}|{}".format(os.getenv('HOME'), cluster_name, namespace_name)

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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Tool for managing multiple kubeconfig files')
   #parser.add_argument('action', metavar='action', type=str, 
    #                    help='action to perform (parse-default-config, add-namespace, delete-namespace, add-cluster, delete-cluster)',
     #                   choices = ['parse-default-config', 'add-namespace', 'delete-namespace', 'add-cluster', 'delete-cluster'])

    subparsers = parser.add_subparsers(title="action", dest="action" )
    pdc_parser = subparsers.add_parser("split-config")
    an_parser = subparsers.add_parser("add-namespace")
    pdc_parser.add_argument('--config', '-c', metavar='config', type=str, help='config file to use', default='{}/.kube/config'.format(os.getenv('HOME')))
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

