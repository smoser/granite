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

class HostOps(object):
    def __init__(self):
        selt._stats = None

    def get_host_stats(self, refresh=False):
        if refresh or self._stats is None:
            self._update_status()
        return self._status

    def get_available_resource(self, nodename):
        pass

    def _update_status(self):
        pass
