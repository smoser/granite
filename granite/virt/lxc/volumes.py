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

CONF.import_opt('host', 'nova.netconf')
CONF.import_opt('use_ipv6', 'nova.netconf')

class VolumeDriver(object):
    def __init__(self, virtapi):
        super(VolumeDriver, self).__init__()
        self.virtapi = virtapi
        self._initiator = None

    def get_volume_connector(self, instance):
        if not self._initiator:
            self._initiator = volumeutils.get_iscsi_inititor()
            if not self._initiator:
                LOG.warn(_('Could not determine iscsi initiator name'),
                           instance=instance)

        return {
            'ip': CONF.my_ip,
            'initiator': self._initiator,
            'host': CONF.host
        }

    def attach_volume(self, connection_info, instance, mountpoint):
        raise NotImplementedError()

    def detach_volume(self, connection_info, instance, mountpoint):
        raise NotImplementedError()

class LXCISCSIDriver(VolumeDriver):
    def __init__(self, virtapi):
        super(LXCISCSIDriver, self).__init__(virtapi)
    
    def attach_volume(self, connection_info, instance, mountpoint):
        pass

    def detach_volume(self, connection_info, instance, mountpoint):
        pass
