# Copyright (C) 2013 VMware, Inc
# Copyright 2011 OpenStack Foundation
# Copyright (c) 2014 Canonical Ltd
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from nova import exception
from nova.network import linux_net
from nova.network import model as network_model
from nova.openstack.common.gettextutils import _
from nova.openstack.common import log as logging

LOG = logging.getLogger(__name__)


class LXCGenericDriver(object):
    def plug(self, container, instance, vif):
        vif_type = vif['type']

        LOG.debug('vif_type=%(vif_type)s instance=%(instance)s '
                  'vif=%(vif)s',
                  {'vif_type': vif_type, 'instance': instance,
                  'vif': vif})

        if vif_type is None:
            raise exception.NovaException(
                _("vif_type parameter must be present "
                  "for this vif_driver implementation"))

        if vif_type == network_model.VIF_TYPE_BRIDGE:
            self.plug_bridge(container, instance, vif)
        elif vif_type == network_model.VIF_TYPE_OVS:
            self.plug_ovs(container, instance, vif)
        else:
            raise exception.NovaException(
                _("Unexpected vif_type=%s") % vif_type)

    def plug_ovs(self, container, instance, vif):
        iface_id = self._get_ovs_interfaceid(vif)
        dev = self._get_vif_devname(vif)
        linux_net.create_tap_dev(dev)
        linux_net.create_ovs_vif_port(self._get_vif_bridge(vif),
                                      dev, iface_id, vif['address'],
                                      instance['uuid'])

        self.setup_lxc_network(container, instance, vif)

    def plug_bridge(self, container, instance, vif):
        self.setup_lxc_network(container, instance, vif)

    def setup_lxc_network(self, container, instance, vif):
        container.load_config()

        container.append_config_item('lxc.network.type', 'veth')
        container.append_config_item('lxc.network.flags', 'up')

        container.append_config_item('lxc.network.link',
                                     self._get_vif_bridge(vif))
        container.append_config_item('lxc.network.hwaddr', vif['address'])

        container.save_config()

    def _get_ovs_interfaceid(self, vif):
        return vif.get('ovs_interfaceid') or vif['id']

    def _get_vif_devname(self, vif):
        if 'devname' in vif:
            return vif['devname']
        return ("nic" + vif['id'])[:network_model.NIC_NAME_LEN]

    def _get_vif_bridge(self, vif):
        return vif['network']['bridge']

    def unplug(self, instance, vif):
        vif_type = vif['type']

        LOG.debug('vif_type=%(vif_type)s instance=%(instance)s '
                  'vif=%(vif)s',
                  {'vif_type': vif_type, 'instance': instance,
                   'vif': vif})

        if vif_type is None:
            raise exception.NovaException(
                _("vif_type parameter must be present "
                  "for this vif_driver implementation"))

        if vif_type == network_model.VIF_TYPE_BRIDGE:
            self.unplug_bridge(instance, vif)
        elif vif_type == network_model.VIF_TYPE_OVS:
            self.unplug_ovs(instance, vif)
        else:
            raise exception.NovaException(
                _("Unexpected vif_type=%s") % vif_type)

    def unplug_bridge(self, instance, vif):
        pass

    def unplug_ovs(self, instance, vif):
        pass
