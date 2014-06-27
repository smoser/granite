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

import os

from oslo.config import cfg
import lxc

from granite.virt.lxc import host_utils as host_utils
from nova.openstack.common.gettextutils import _   # noqa
from nova.openstack.common import jsonutils
from nova.openstack.common import log as logging
from nova.openstack.common import units
from nova import utils

CONF = cfg.CONF

log = logging.getLogger(__name__)


class HostOps(object):
    def __init__(self):
        self._stats = None

    def get_host_stats(self, refresh=False):
        if refresh or self._stats is None:
            self._update_status()
        return self._stats

    def get_available_resource(self, nodename):
        memory = host_utils.get_memory_info()
        disk = host_utils.get_disk_info()

        dic = {'vcpus': host_utils.get_cpu_count(),
               'memory_mb': memory['total'],
               'local_gb': disk['total'] / units.Gi,
               'vcpus_used': 0,
               'memory_mb_used': memory['used'],
               'local_gb_used': disk['used'] / units.Gi,
               'hypervisor_type': 'lxc',
               'hypervisor_verison': utils.convert_version_to_string(lxc.version),
               'hypervisor_hostname': CONF.host,
               'cpu_info': '?',
               'supported_instances': jsonutils.dumps([
                                     ('i686', 'lxc', 'lxc'),
                                     ('x86_64', 'lxc', 'lxc'),
                                     ])
        return dic

    def _update_status(self):
        memory = host_utils.get_memory_info()
        disk = host_utils.get_disk_info()

        dic = {'vcpus': host_utils.get_cpu_count(),
               'memory_mb': memory['total'],
               'local_gb': disk['total'] / units.Gi,
               'vcpus_used': 0,
               'memory_mb_used': memory['used'],
               'local_gb_used': disk['used'] / units.Gi,
               'hypervisor_type': 'lxc',
               'hypervisor_verison': utils.convert_version_to_string(lxc.version),
               'hypervisor_hostname': CONF.host,
               'cpu_info': '?',
               'supported_instances': jsonutils.dumps([
                                      ('i686', 'lxc', 'lxc'),
                                      ('x86_64', 'lxc', 'lxc'),
                                      ])

        self._stats = dic
        return self._stats
