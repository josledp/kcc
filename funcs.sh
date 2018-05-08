export KUBECONFIG="none"

kcs() {
  CLUSTER=$1
  NAMESPACE=${2:-default}
  [ -z "$CLUSTER" ] && echo "cluster name needed" && return 1
  FILE="$HOME/.kube/config|$CLUSTER|$NAMESPACE"
  [ ! -e "$FILE" ] && echo "unknown $CLUSTER($NAMESPACE)" && return 1
  export KUBECONFIG="$FILE"
}

kns() {
  NAMESPACE=$1
  [ -z "$NAMESPACE" ] && echo "namespace name needed" && return 1
  CLUSTER=`echo $KUBECONFIG|cut -f2 -d'|'`
  FILE="$HOME/.kube/config|$CLUSTER|$NAMESPACE"
  [ ! -e "$FILE" ] && echo "unknown $CLUSTER($NAMESPACE)" && return 1
  export KUBECONFIG="$FILE"
}
