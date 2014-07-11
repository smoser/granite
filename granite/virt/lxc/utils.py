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

def chown_uid_mappings(uid_mapping, container_dir):
    utils.execute('idmapshift', '-u', uid_mapping, container_dir, run_as_root=True)
