#!/bin/bash

set -xe

env

NOVAGRANITEDIR=$(realpath $(dirname $0)/../..)
INSTALLDIR=${INSTALLDIR:-/opt/stack}

cp $NOVAGRANTIEDIR/contrib/devstack/extras.d/70-granite.sh $INSTALLDIR/devstack/extras.d
cp $NOVAGRANTIEDIR/contrib/devstack/lib/nova_plugins/hypervisor-granite $INSTALLDIR/devstack/lib/nova_plugins/
