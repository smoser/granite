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

from granite.virt.lxc import network
from nova import exception
from nova.network import linux_net
from nova.network import model as network_model
from nova.openstack.common.gettextutils import _
from nova.openstack.common import log as logging
from nova.openstack.common import processutils
from nova import utils

LOG = logging.getLogger(__name__)

class LXCGenericDriver(object):
    def plug(self, instance, vif):
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
            self.plug_bridge(instance, vif)
        elif vif_type == network_model.VIF_TYPE_OVS:
            self.plug_ovs(instance, vif)
        else:
            raise exception.NovaException(
                     _("Unexpected vif_type=%s") % vif_type)

    def plug_bridge(self, instance, vif):
        instance_name = instance['uuid']
        if_local_name = 'tap%s' % vif['id'][:11]
        if_remote_name = 'ns%s' % vif['id'][:11]
        bridge = vif['network']['bridge']
        gateway = network.find_gateway(instance, vif['network'])
        ip = network.find_fixed_ip(instance, vif['network'])

        if linux_net.device_exists(if_local_name):
            return
        undo_mgr = utils.UndoManager()

        try:
            utils.execute('ip', 'link', 'add', 'name', if_local_name, 'type',
                          'veth', 'peer', 'name', if_remote_name, run_as_root=True)
            undo_mgr.undo_with(lambda: utils.execute(
                    'ip', 'link', 'delete', if_local_name, run_as_root=True))
            # NOTE(samalba): Deleting the interface will delete all
            # associated resources (remove from the bridge, its pair, etc...)
            utils.execute('brctl', 'addif', bridge, if_local_name, run_as_root=True)
            utils.execute('ip', 'link', 'set', if_local_name, 'up', run_as_root=True)
            utils.execute('ip', 'link', 'set', if_remote_name, 'netns',
                         instance_name, run_as_root=True)
            utils.execute('ip', 'netns', 'exec', instance_name, 'ip', 'link',
                           'set', if_remote_name, 'address', vif['address'],
                           run_as_root=True)
            utils.execute('ip', 'netns', 'exec', instance_name, 'ifconfig',
                          if_remote_name, ip, run_as_root=True)
            utils.execute('ip', 'netns', 'exec', instance_name,
                          'ip', 'route', 'replace', 'default', 'via',
                          gateway, 'dev', if_remote_name, run_as_root=True)
        except Exception:
            LOG.exception("Failed to configure network")
            msg = _('Failed to setup the network, rolling back')
            undo_mgr.rollback_and_reraise(msg=msg, instance=instance)

    def plug_ovs(self, instance, vif):
        instance_name = instance['uuid']
        if_local_name = 'tap%s' % vif['id'][:11]
        if_remote_name = 'ns%s' % vif['id'][:11]
        bridge = vif['network']['bridge']
        gateway = network.find_gateway(instance, vif['network'])
        ip = network.find_fixed_ip(instance, vif['network'])

        # Device already exists so return.
        if linux_net.device_exists(if_local_name):
            return
        undo_mgr = utils.UndoManager()

        try:
            utils.execute('ip', 'link', 'add', 'name', if_local_name, 'type',
                          'veth', 'peer', 'name', if_remote_name,
                          run_as_root=True)
            linux_net.create_ovs_vif_port(bridge, if_local_name,
                                          network.get_ovs_interfaceid(vif),
                                          vif['address'],
                                          instance['uuid'])
            utils.execute('ip', 'link', 'set', if_local_name, 'up',
                          run_as_root=True)
            utils.execute('ip', 'link', 'set', if_remote_name, 'netns',
                          instance_name, run_as_root=True)
            utils.execute('ip', 'netns', 'exec', instance_name, 'ip', 'link',
                          'set', if_remote_name, 'address', vif['address'],
                          run_as_root=True)
            utils.execute('ip', 'netns', 'exec', instance_name, 'ifconfig',
                           if_remote_name, ip, run_as_root=True)
            utils.execute('ip', 'netns', 'exec', instance_name,
                          'ip', 'route', 'replace', 'default', 'via',
                          gateway, 'dev', if_remote_name, run_as_root=True)

        except Exception:
            LOG.exception("Failed to configure network")
            msg = _('Failed to setup the network, rolling back')
            undo_mgr.rollback_and_reraise(msg=msg, instance=instance)


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

    def unplug_bridge(self, instance, vif):
        instance_name = instance['uuid']
        if_remote_name = 'ns%s' % vif['id'][:11]

        try:
            utils.execute('ip', 'netns', 'exec', instance_name, 'ifconfig',
                          if_remove_name, 'down', run_as_root=True)
        except Exception:
            LOG.exception('Failed to unconfigure the network')

    def unplug_ovs(self, instance, vif):
        try:
            linux_net.delete_ovs_vif_port(vif['network']['bridge'],
                                          vif['devname'])
        except processutils.ProcessExecutionError:
            LOG.exception(_("Failed while unplugging vif"), instance=instance)
