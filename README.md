tools for managing multiple k8s clusters

source funcs.sh in your .bashrc or .profile

kubeconfig files expect to have config#clustername#namespace format, so when
you need to configure a new cluster you should point KUBECONFIG there (yep,
rudimentary ^^)

autocomplete file may be added to your bash_completion.d
