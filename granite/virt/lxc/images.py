# Copyright (c) 2014 Canonical Ltd
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
import tarfile


from oslo.config import cfg

from granite.virt.lxc import utils as container_utils

from nova import exception
from nova.openstack.common import fileutils
from nova.openstack.common import log as logging
from nova import utils
from nova.virt import images

CONF = cfg.CONF
CONF.import_opt('use_cow_images', 'nova.virt.driver')
LOG = logging.getLogger(__name__)


def fetch_image(context, instance, image_meta, container_image):
    """Fetch the image from a glance image server."""
    LOG.debug("Downloading image from glance")

    base_dir = os.path.join(CONF.instances_path,
                            CONF.image_cache_subdirectory_name)
    if not os.path.exists(base_dir):
        fileutils.ensure_tree(base_dir)
    base = os.path.join(base_dir, container_image)
    if not os.path.exists(base):
        images.fetch_to_raw(context, instance['image_ref'], base,
                            instance['user_id'], instance['project_id'])
    if not tarfile.is_tarfile(base):
        os.unlink(base)
        raise exception.InvalidDiskFormat(
            disk_format=container_utils.get_disk_format(image_meta))


def create_container(instance):
    """Create an LXC rootfs directory for a given container."""
    LOG.debug('Creating LXC rootfs')

    container_rootfs = container_utils.get_container_rootfs(instance)
    if not os.path.exists(container_rootfs):
        fileutils.ensure_tree(container_rootfs)


def setup_container(instance, container_image):
    """Setup the LXC container."""
    LOG.debug('Creating LXC container')
    id_map = []
    base_dir = os.path.join(CONF.instances_path,
                            CONF.image_cache_subdirectory_name)
    base = os.path.join(base_dir, container_image)
    id_map = container_utils.parse_idmap(CONF.lxc.lxc_subuid)

    container_rootfs = container_utils.get_container_rootfs(instance)

    cwd = os.getcwd()
    try:
        os.chdir(container_rootfs)
        utils.execute('lxc-usernsexec', '-m',
                      'b:0:%s:%s' % (id_map[1], id_map[2]),
                      '-m', 'b:200000:1000:1', '--',
                      'tar', '--anchored', '--numeric-owner',
                      '-xvpzf', base, check_exit_code=[2])
    finally:
        os.chdir(cwd)
        utils.execute('chown', id_map[1], container_rootfs, run_as_root=True)
