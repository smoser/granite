#!/bin/bash

set -xe

env

NOVAGRANITEDIR=$(realpath $(dirname $0)/../..)
INSTALLDIR=${INSTALLDIR:-/opt/stack}

cp $NOVAGRANITEDIR/contrib/devstack/extras.d/70-granite.sh $INSTALLDIR/devstack/extras.d
cp $NOVAGRANITEDIR/contrib/devstack/lib/nova_plugins/hypervisor-granite $INSTALLDIR/devstack/lib/nova_plugins/
cp $NOVAGRANITEDIR/contrib/devstack/lib/granite $INSTALLDIR/devstack/lib/granite
cat - <<-EOF >> $INSTALLDIR/devstack/localrc
export VIRT_DRIVER=granite
EOF
