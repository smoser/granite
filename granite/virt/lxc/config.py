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

import lxc

from oslo.config import cfg

from nova.openstack.common import fileutils
from nova.openstack.common.gettextutils import _ # noqa
from nova.openstack.common import importutils
from nova.openstack.common import log as logging
from nova import exception
from nova import utils
from nova.virt.disk import api as disk
from nova.virt import images

LOG = logging.getLogger(__name__)

CONF = cfg.CONF

class LXCConfig(object):
    def __init__(self, container, instance, image_meta, network_info,
                instance_dir, image_path, config_file):
        self.container = container
        self.instance = instance
        self.image_meta = image_meta
        self.network_info = network_info
        self.instance_dir = instance_dir
        self.image_path = image_path
        self.config_file = config_file

        vif_class = importutils.import_class(CONF.lxc.vif_driver)
        self.vif_driver = vif_class()

    def get_config(self):
        LOG.debug('Building LXC container configuration file')

        lxc_template = self._get_lxc_template()
        if lxc_template:
            self._write_lxc_template(lxc_template)

            self.container.load_config()
            self.config_lxc_name()
            self.config_lxc_rootfs()
            self.config_lxc_console()
            self.config_lxc_network()
            self.config_lxc_logging()
            self.container.save_config()

    def _get_lxc_template(self):
        LOG.debug('Fetching LXC template')

        templates = []
        if (self.image_meta and
            self.image_meta.get('properties', {}).get('template')):
                lxc_template = self.image_meta['propeties'].get('template')
        else:
                lxc_template = CONF.lxc.lxc_default_template
        path = os.listdir(CONF.lxc.lxc_template_dir)
        for line in path:
            templates.append(line.replace('lxc-', ''))
        if lxc_template in templates:
            return lxc_template

    def _write_lxc_template(self, template_name):
        f = open(self.config_file, 'w')
        f.write('lxc.include = %s/%s.common.conf' % (CONF.lxc.lxc_config_dir,
                                                     template_name))
        f.close()

    def config_lxc_name(self):
        self.container.append_config_item('lxc.utsname', self.instance['uuid'])

    def config_lxc_rootfs(self):
        self.container.append_config_item('lxc.rootfs', 'nbd:%s:1' % self.image_path)

    def config_lxc_console(self):
        self.container.append_config_item('lxc.console', os.path.join(self.instance_dir,
                                                            'console.log'))

    def config_lxc_network(self):
        self.container.append_config_item('lxc.network.type', 'veth')
        self.container.append_config_item('lxc.network.flags', 'up')

        vif_info = self.vif_driver.plug(self.instance, self.network_info)
        self.container.append_config_item('lxc.network.link', vif_info['bridge'])
        self.container.append_config_item('lxc.network.hwaddr', vif_info['mac'])

    def config_lxc_logging(self):
        self.container.append_config_item('lxc.logfile', os.path.join(self.instance_dir,
                                                            'console.logfile'))
