import re

from oslo.config import cfg

from nova import context as nova_context
from nova import exception
from nova import network
from nova.openstack.common.gettextutils import _
from nova.openstack.common import importutils
from nova.openstack.common import log as logging
from nova.openstack.common import processutils
from nova import utils
from nova.virt import volumeutils

CONF = cfg.CONF


LOG = logging.getLogger(__name__)

class VolumeOps(object):
    def connect_volume(self, connection_info, instance, mountpoint):
        LOG.debug(_('connecting volume')

    def disconnect_volume(self, connection_info, instance, mountpoint):
	    LOG.debug('disconnecting volume')
