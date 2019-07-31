export KUBECONFIG="none"
alias k=kubectl

kcs() {
  local CLUSTER=$1
  local NAMESPACE=${2:-default}
  [ -z "$CLUSTER" ] && echo "cluster name needed" && return 1
  if [ "$CLUSTER" = "none" ]; then
    unset KUBECONFIG
    return
  fi
  local FILE="$HOME/.kube/config#$CLUSTER#$NAMESPACE"
  if [ ! -e "$FILE" ]; then
    local DEFAULT="$HOME/.kube/config#$CLUSTER#default"
    if [ ! -e "$DEFAULT" ]; then
      echo "Unknown cluster $CLUSTER"
      return 1
    fi
    echo "first time $NAMESPACE usage. Adding it"
    _add_namespace "${CLUSTER}" "${NAMESPACE}"
  fi
  export K8SCLUSTER="$CLUSTER"
  export K8SNAMESPACE="$NAMESPACE"
  export KUBECONFIG="$FILE"
}

kns() {
  local NAMESPACE=$1
  [ -z "$NAMESPACE" ] && echo "namespace name needed" && return 1
  local CLUSTER=`echo $KUBECONFIG|cut -f2 -d'#'`
  local FILE="$HOME/.kube/config#$CLUSTER#$NAMESPACE"
  if [ ! -e "$FILE" ]; then
    echo "first time $NAMESPACE usage. Adding it"
    _add_namespace "${CLUSTER}" "${NAMESPACE}"
  fi
  export K8SNAMESPACE="$NAMESPACE"
  export KUBECONFIG="$FILE"
}

_add_namespace() {
  local CLUSTER=$1
  local NAMESPACE=$2
  [ -z "$CLUSTER" ] && return 1
  [ -z "$NAMESPACE" ] && return 1
  local DEFAULT="$HOME/.kube/config#$CLUSTER#default"
  local FILE="$HOME/.kube/config#$CLUSTER#$NAMESPACE"
  cp "${DEFAULT}" "${FILE}"
  export KUBECONFIG="${FILE}"
  kubectl config set-context $CLUSTER --namespace=$NAMESPACE
  if [ $? -ne 0 ]; then
    echo "error adding namespace"
    return 1
  fi
}
