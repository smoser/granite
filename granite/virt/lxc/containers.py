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
from granite.virt.lxc import images
from granite.virt.lxc import utils as container_utils
from granite.virt.lxc import vifs
from granite.virt.lxc import volumes

from nova.openstack.common import fileutils
from nova.openstack.common.gettextutils import _ # noqa
from nova.openstack.common import importutils
from nova.openstack.common import log as logging
from nova import exception
from nova import utils
from nova.virt.disk import api as disk

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
    cfg.StrOpt('lxc_subuid',
                default='1000:100000:65536',
                help='Default lxc sub uid'),
    cfg.StrOpt('lxc_subgid',
                default='1000:100000:65536',
                help='Default lxc sub gid'),
    cfg.StrOpt('vif_driver',
               default='granite.virt.lxc.vifs.LXCGenericDriver',
               help='Default vif driver'),
]

LOG = logging.getLogger(__name__)

CONF = cfg.CONF
CONF.import_opt('use_cow_images', 'nova.virt.driver')
CONF.register_opts(lxc_opts, 'lxc')

class Containers(object):
    def __init__(self):
        self.instance_path = None
        self.container_rootfs = None

        vif_class = importutils.import_class(CONF.lxc.vif_driver)
        self.vif_driver = vif_class()

	self.volumes = volumes.VolumeOps()


    def spawn(self, context, instance, image_meta, injected_files,
              admin_password, network_info, block_device_info=None):
        """ Creates a LXC container instance
            Steps that are followed:

        1. Create a container
        2. Fetches the image from glance
        3. Untars the image from glance
        4. Start the container
        """
        LOG.debug('Spawning containers')

        # Check for a vlid image:
        file_type = container_utils.get_disk_format(image_meta)
        if file_type == 'root-tar':
            container_image = '%s.tar.gz' % instance['image_ref']

        # Setup the LXC instance
        instance_name = instance['uuid']
        container = lxc.Container(instance_name)
        container.set_config_path(CONF.instances_path)

        # Create the LXC container from the image
        images.fetch_image(context, instance, image_meta, container_image)
        images.create_container(instance)

        # Write the LXC confgiuration file
        cfg = config.LXCConfig(container, instance, image_meta, network_info)
        cfg.get_config()

        images.setup_container(instance, container_image)

        # Startint the container
        if not container.running:
            if container.start():
               LOG.info(_('Container started'))
        self.setup_network(instance, network_info)

    def destroy_container(self, context, instance, network_info,
                          block_device_info, destroy_disks):
        LOG.debug('Destroying container')
        container = lxc.Container(instance['uuid'])
        container.set_config_path(CONF.instances_path)
        if container.running:
            container.stop()
            # segfault work around
            utils.execute('lxc-destroy', '-n', instance['uuid'], '-P', 
                            CONF.instances_path)

    def reboot_container(self, context, instance, network_info, reboot_type, block_device_info,
                         bad_volumes_callback):
        LOG.debug('Rebooting container')
        container = lxc.Container(instance['uuid'])
        container.set_config_path(CONF.instances_path)
        if container.running:
            if container.reboot():
                LOG.info(_('Container rebooted'))

    def stop_container(self, instance):
        LOG.debug('Stopping container')
        container = lxc.Container(instance['uuid'])
        container.set_config_path(CONF.instances_path)
        if container.running:
            if container.stop():
                LOG.info(_('Container stopped'))

    def start_container(self, context, instance, network_info, block_device_info):
        LOG.debug('Starting container')
        LOG.info(_('!!! %s') % instance['uuid'])
        container = lxc.Container(instance['uuid'])
        container.set_config_path(CONF.instances_path)
        if container.start():
            LOG.info(_('Container started'))
        
    def shutdown_container(self, instnace, network_info, block_device_info):
        LOG.debug('Shutdown container')
        container = lxc.Container(instance['uuid'])
        container.set_config_path(CONF.instances_path)
        if container.defined and container.controllable:
            container.shutdown()

    def suspend_container(self, instance):
        LOG.debug('Suspend container')
        container = lxc.Container(instance['uuid'])
        container.set_config_path(CONF.instances_path)
        if container.defined and container.controllable:
            container.freeze()

    def resume_container(self, context, instance, network_info, block_device_info):
        LOG.debug('Suspend container')
        container = lxc.Container(instance['uuid'])
        container.set_config_path(CONF.instances_path)
        if container.defined and container.controllable:
            container.unfreeze()

    def setup_network(self, instance, network_info):
        instance_name = instance['uuid']
        netns_path = '/var/run/netns'
        if not os.path.exists(netns_path):
            utils.execute('mkdir', '-p', netns_path, run_as_root=True)
        container_pid = self.get_container_pid(instance)
        if container_pid:
            netns_path = os.path.join(netns_path, instance_name)
            utils.execute('ln', '-sf', '/proc/{0}/ns/net'.format(container_pid),
                          '/var/run/netns/{0}'.format(instance_name),
                          run_as_root=True)

            for vif in network_info:
                self.vif_driver.plug(instance, vif)

    def attach_container_volume(self, context, connection_info, instance, mountpoint,
                      disk_bus=None, device_type=None, encryption=None):
        self.volumes.connect_volume(connection_info, instance, mountpoint)

    def detach_container_volume(self,  connection_info, instance, mountpoint, encryption):
        self.volumes.disconnect_volume(connection_info, instance, mountpoint)

    def container_exists(self, instance):
        container = lxc.Container(instance['uuid'])
        container.set_config_path(CONF.instances_path)

        if container.running:
            return True
        else:
            return False

    def get_container_pid(self, instance):
        container = lxc.Container(instance['uuid'])
        container.set_config_path(CONF.instances_path)
        if container.running:
            return container.init_pid
