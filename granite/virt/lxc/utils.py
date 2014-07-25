# Copyright (c) 2014 Canonical ltd
# All Rights Reserved.
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

from nova.openstack.common.gettextutils import _ # noqa
from nova.openstack.common import  log as logging
from nova import utils

LOG = logging.getLogger(__name__)


CONF = cfg.CONF

def get_container_rootfs(instance):
    return os.path.join(CONF.instances_path, instance['uuid'], 'rootfs')

def get_container_config(instance):
    return os.path.join(CONF.instances_path, instance['uuid'], 'config')

def get_container_console(instance):
    return os.path.join(CONF.instances_path, instance['uuid'], 'container.console')

def get_container_logfile(instance):
    return os.path.join(CONF.instances_path, instance['uuid'], 'container.logifle')

def get_instance_path(instance):
    return os.path.join(CONF.instances_path, instance['uuid'])

def get_disk_format(image_meta):
    return image_meta.get('disk_format')

def parse_idmap(map_string):
    mappings = []
    mappings = map_string.split(':')
    return mappings
