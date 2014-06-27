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
import psutil

from nova.openstack.common.gettextutils import _   # noqa
from nova.openstack.common import jsonutils
from nova.openstack.common import log as logging
from nova import utils

CONF = cfg.CONF

log = logging.getLogger(__name__)


def get_memory_info():
    out = open('/proc/meminfo')
    for line in out:
        if 'MemTotal:' == line.split()[0]:
            split = line.split()
            total  = float(split[1])
        if 'MemFree:' == line.split()[0]:
            split = line.split()
            free  = float(split[1])
        if 'Buffers:' == line.split()[0]:
            split = line.split()
            buffers = float(split[1])
        if 'Cached:' == line.split()[0]:
            split = line.split()
            cached = float(split[1])
    used = (total - (free + buffers + cached))
    return {'total': int(total/1024),
            'free': int(free/1024),
            'used': int(used/1024)}

def get_disk_info():
    hddinfo = os.statvfs(CONF.instances_path)
    total = hddinfo.f_frsize * hddinfo.f_blocks
    free = hddinfo.f_frsize * hddinfo.f_bavail
    used = hddinfo.f_frsize * (hddinfo.f_blocks - hddinfo.f_bfree)
    return {'total': total, 'free': free, 'used': used}

def get_cpu_count():
    try:
        return psutil.NUM_CPUS
    except (ImportError, AttributeError):
        return 1
