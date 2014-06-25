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

from nova import exception
from nova.network import linux_net
from nova.network import model as network_model
from nova.openstack.common.gettextutils import _
from nova.openstack.common import log as logging
from nova.openstack.common import processutils
from nova import utils

LOG = logging.getLogger(__name__)

class LXCGenericDriver(object):
    def plug(self, instance, vif):
        vif_info = {}
        if not vif:
            return vif_info
        for vifs in vif:
            mac_address = vifs['address']
            network_bridge = vifs['network']['bridge']

        vif_info['mac'] = mac_address
        vif_info['bridge'] = network_bridge
        return vif_info

    def unplug(self, isntance, vif):
        pass
