# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
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

"""
A fake (in-memory) hypervisor+api.

Allows nova testing w/o a hypervisor.  This module also documents the
semantics of real hypervisor connections.

"""

import contextlib

from oslo.config import cfg
import lxc

from granite.virt.lxc import containers
from granite.virt.lxc import hostops

from nova.compute import power_state
from nova.compute import task_states
from nova import db
from nova import exception
from nova.openstack.common.gettextutils import _
from nova.openstack.common import jsonutils
from nova.openstack.common import log as logging
from nova import utils
from nova.virt import driver
from nova.virt import virtapi

CONF = cfg.CONF
CONF.import_opt('host', 'nova.netconf')

LOG = logging.getLogger(__name__)


_FAKE_NODES = None


def set_nodes(nodes):
    """Sets LXCDriver's node.list.

    It has effect on the following methods:
        get_available_nodes()
        get_available_resource
        get_host_stats()

    To restore the change, call restore_nodes()
    """
    global _FAKE_NODES
    _FAKE_NODES = nodes


def restore_nodes():
    """Resets LXCDriver's node list modified by set_nodes().

    Usually called from tearDown().
    """
    global _FAKE_NODES
    _FAKE_NODES = [CONF.host]


class FakeInstance(object):

    def __init__(self, name, state, uuid):
        self.name = name
        self.state = state
        self.uuid = uuid

    def __getitem__(self, key):
        return getattr(self, key)


class LXCDriver(driver.ComputeDriver):
    capabilities = {
        "has_imagecache": True,
        "supports_recreate": True,
        }

    """Fake hypervisor driver."""

    def __init__(self, virtapi, read_only=False):
        super(LXCDriver, self).__init__(virtapi)
        self.instances = {}
        self.host_status_base = {
          'vcpus': 100000,
          'memory_mb': 8000000000,
          'local_gb': 600000000000,
          'vcpus_used': 0,
          'memory_mb_used': 0,
          'local_gb_used': 100000000000,
          'hypervisor_type': 'fake',
          'hypervisor_version': utils.convert_version_to_int('1.0'),
          'hypervisor_hostname': CONF.host,
          'cpu_info': {},
          'disk_available_least': 500000000000,
          'supported_instances': [(None, 'fake', None)],
          }
        self._mounts = {}
        self._interfaces = {}
        if not _FAKE_NODES:
            set_nodes([CONF.host])
        self.containers = containers.Containers()
        self.hostops = hostops.HostOps()

    def init_host(self, host):
        if not lxc.version:
            raise Exception('LXC is not installed')

    def list_instances(self):
        return lxc.list_containers()

    def spawn(self, context, instance, image_meta, injected_files,
              admin_password, network_info=None, block_device_info=None):
        self.containers.spawn(context, instance, image_meta, injected_files,
                              admin_password, network_info, block_device_info)

    def snapshot(self, context, instance, name, update_task_state):
        if instance['name'] not in self.instances:
            raise exception.InstanceNotRunning(instance_id=instance['uuid'])
        update_task_state(task_state=task_states.IMAGE_UPLOADING)

    def reboot(self, context, instance, network_info, reboot_type,
               block_device_info=None, bad_volumes_callback=None):
        pass

    @staticmethod
    def get_host_ip_addr():
        return '192.168.0.1'

    def rescue(self, context, instance, network_info, image_meta,
               rescue_password):
        pass

    def unrescue(self, instance, network_info):
        pass

    def power_off(self, instance):
        pass

    def power_on(self, context, instance, network_info, block_device_info):
        pass

    def suspend(self, instance):
        pass

    def resume(self, context, instance, network_info, block_device_info=None):
        pass

    def destroy(self, context, instance, network_info, block_device_info=None,
                destroy_disks=True):
        self.containers.destroy_container(context, instance, network_info,
                                          block_device_info, destroy_disks)

    def attach_volume(self, context, connection_info, instance, mountpoint,
                      disk_bus=None, device_type=None, encryption=None):
        """Attach the disk to the instance at mountpoint using info."""
        instance_name = instance['name']
        if instance_name not in self._mounts:
            self._mounts[instance_name] = {}
        self._mounts[instance_name][mountpoint] = connection_info
        return True

    def detach_volume(self, connection_info, instance, mountpoint,
                      encryption=None):
        """Detach the disk attached to the instance."""
        try:
            del self._mounts[instance['name']][mountpoint]
        except KeyError:
            pass
        return True

    def attach_interface(self, instance, image_meta, vif):
        if vif['id'] in self._interfaces:
            raise exception.InterfaceAttachFailed('duplicate')
        self._interfaces[vif['id']] = vif

    def detach_interface(self, instance, vif):
        try:
            del self._interfaces[vif['id']]
        except KeyError:
            raise exception.InterfaceDetachFailed('not attached')

    def get_info(self, instance):
        state = self.containers.container_exists(instance)
        if state:
            pstate = power_state.RUNNING
        elif state is False:
            pstate = power_state.SHUTDOWN
        else:
            pstate = power_state.NOSTATE
        return {'state': pstate,
                'max_mem': 0,
                'mem': 0,
                'num_cpu': 2,
                'cpu_time': 0}

    def get_console_output(self, context, instance):
        return 'FAKE CONSOLE OUTPUT\nANOTHER\nLAST LINE'

    def get_available_resource(self, nodename):
        """Updates compute manager resource info on ComputeNode table.

           Since we don't have a real hypervisor, pretend we have lots of
           disk and ram.
        """
        if nodename not in _FAKE_NODES:
            return {}

        dic = {'vcpus': 1,
               'memory_mb': 8192,
               'local_gb': 1028,
               'vcpus_used': 0,
               'memory_mb_used': 0,
               'local_gb_used': 0,
               'hypervisor_type': 'fake',
               'hypervisor_version': '1.0',
               'hypervisor_hostname': nodename,
               'disk_available_least': 0,
               'cpu_info': '?',
               'supported_instances': jsonutils.dumps([(None, 'fake', None)])
              }
        return dic

    def get_host_stats(self, refresh=False):
        """Return fake Host Status of ram, disk, network."""
        stats = []
        for nodename in _FAKE_NODES:
            host_status = self.host_status_base.copy()
            host_status['hypervisor_hostname'] = nodename
            host_status['host_hostname'] = nodename
            host_status['host_name_label'] = nodename
            stats.append(host_status)
        if len(stats) == 0:
            raise exception.NovaException("LXCDriver has no node")
        elif len(stats) == 1:
            return stats[0]
        else:
            return stats
