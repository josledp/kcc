import yaml
import argparse
import os


class ConfigFile(object):

    def __init__(self, cluster_name, namespace_name):
        self.file="~/.kube/config-{}-{}".format(cluster_name, namespace_name)

    def delete(self):
        os.remove(self.file)

    def write(self, data):
        with open(self.file, 'w') as fd:
            os.write(fd, data)

class Context(object):
    def __init__(self, cluster_name, namespace_name, user_data, cacrt=None, server=None):
        self.cluster_name = cluster_name
        self.namespace_name = namespace_name
        self.user_data = user_data
        self.cacrt = cacrt
        self.server = server
        self._configfile = ConfigFile(self.cluster_name, self.namespace_name)

    def add(self):
        self._configfile.write("data")
    
    def delete(self):
        self._configfile.delete()


def parse_default_config(arguments):
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", "-c", metavar="config", type=str, help='config file. default ~/.kube/config', default='~/.kube/config')
    args = parser.parse_args(arguments)
    with open(args.config) as fd:
        data = yaml.parse(os.read(fd))
    print(data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Tool for managing multiple kubeconfig files')
    parser.add_argument('action', metavar='action', type=str, 
                        help='action to perform (parse-default-config, add-namespace, delete-namespace, add-cluster, delete-cluster)',
                        choices = ['parse-default-config', 'add-namespace', 'delete-namespace', 'add-cluster', 'delete-cluster'])


    args, extra = parser.parse_known_args()
    action = args.action.replace("-","_")
    possibles = globals().copy()
    method = possibles.get(action, None)
    if method is None:
        raise Exception("unable to find method {}".format(action))
    
    method(extra)

