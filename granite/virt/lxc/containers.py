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
import shutil

import lxc

from oslo.config import cfg

from granite.virt.lxc import config
from granite.virt.lxc import vifs

from nova.openstack.common import fileutils
from nova.openstack.common.gettextutils import _ # noqa
from nova.openstack.common import importutils
from nova.openstack.common import log as logging
from nova import exception
from nova import utils
from nova.virt.disk import api as disk
from nova.virt import images

lxc_opts = [
    cfg.StrOpt('lxc_default_template',
               default='ubuntu-cloud',
               help='Default LXC template'),
    cfg.StrOpt('lxc_template_dir',
               default='/usr/share/lxc/templates',
               help='Default template directory'),
    cfg.StrOpt('lxc_config_dir',
                default='/usr/share/lxc/config',
                help='Default lxc config dir'),
    cfg.StrOpt('vif_driver',
               default='granite.virt.lxc.vifs.LXCGenericDriver',
               help='Default vif driver'),
]

LOG = logging.getLogger(__name__)

CONF = cfg.CONF
CONF.register_opts(lxc_opts, 'lxc')

class Containers(object):
    def __init__(self):
        self.instance_path = None
        self.image_path = None

    def spawn(self, context, instance, image_meta, injected_files,
              admin_password, network_info, block_device_info=None):
        LOG.debug('Spawning containers')

        try:
            self.instance_path = os.path.join(CONF.instances_path, instance['uuid'])
            fileutils.ensure_tree(self.instance_path)
            self.config_file = os.path.join(self.instance_path, 'config')

            def _fetch_image():
                LOG.debug('Fetching image from glance')
                self.image_path = os.path.join(self.instance_path, 'disk')
                images.fetch(context, instance['image_ref'], self.image_path,
                            instance['user_id'], instance['project_id'])

            _fetch_image()

            container = lxc.Container(instance['uuid'])
            container.set_config_path(CONF.instances_path)

            cfg = config.LXCConfig(container, instance, image_meta, network_info,
                                   self.instance_path, self.image_path, self.config_file)
            cfg.get_config()

            def _start_container():
                LOG.debug(_('Starting container'))
                if not container.defined:
                    raise Exception(_('LXC container is not defined'))

                utils.execute('lxc-start', '-d', '-f',  self.config_file,
                              '-o', '/tmp/out', '-l', 'ERROR', '--name', instance['uuid'], run_as_root=True)

            _start_container()
        except Exception as ex:
            LOG.exception(ex)

    def destroy_container(self, context, instance, network_info,
                          block_device_info, destroy_disks):
        LOG.debug('Destroying container')
        container = lxc.Container(instance['uuid'])
        if container.defined:
            utils.execute('lxc-destroy', '-n', instance['uuid'],
                          run_as_root=True)
            shutil.rmtree(self.instance_path)

    def container_exists(self, instance):
        container = lxc.Container(instance['uuid'])
        container.set_config_path(CONF.instances_path)

        if container.running:
            return True
        else:
            return False
