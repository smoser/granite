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

import grp
import pwd
import os


from oslo.config import cfg

from nova.openstack.common.gettextutils import _  # noqa
from nova.openstack.common import log as logging

LOG = logging.getLogger(__name__)


CONF = cfg.CONF


def get_container_rootfs(instance):
    return os.path.join(CONF.instances_path, instance['uuid'], 'rootfs')


def get_container_config(instance):
    return os.path.join(CONF.instances_path, instance['uuid'], 'config')


def get_container_console(instance):
    return os.path.join(CONF.instances_path, instance['uuid'],
                        'container.console')


def get_container_logfile(instance):
    return os.path.join(CONF.instances_path, instance['uuid'],
                        'container.logfile')


def get_instance_path(instance):
    return os.path.join(CONF.instances_path, instance['uuid'])


def get_disk_format(image_meta):
    return image_meta.get('disk_format')


class LXCIdMap(object):
    def __init__(self, ustart, unum, gstart, gnum):
        self.ustart = int(ustart)
        self.unum = int(unum)
        self.gstart = int(gstart)
        self.gnum = int(gnum)

    def usernsexec_margs(self, with_read=None):
        if with_read:
            if with_read == "user":
                with_read = os.getuid()
            unum = self.unum - 1
            rflag = ['-m', 'u:%s:%s:1' % (self.ustart + self.unum, with_read)]
            print("================ rflag: %s ==================" % (str(rflag)))
        else:
            unum = self.unum
            rflag = []

        return ['-m', 'u:0:%s:%s' % (self.ustart, unum),
                '-m', 'g:0:%s:%s' % (self.gstart, self.gnum)] + rflag

    def lxc_conf_lines(self):
        return (('lxc.id_map', 'u 0 %s %s' % (self.ustart, self.unum)),
                ('lxc.id_map', 'g 0 %s %s' % (self.gstart, self.gnum)))


class LXCUserIdMap(LXCIdMap):
    def __init__(self, user=None, group=None, subuid_f="/etc/subuid",
                 subgid_f="/etc/subgid"):
        if user is None:
            user = pwd.getpwuid(os.getuid())[0]
        if group is None:
            group = grp.getgrgid(os.getgid()).gr_name

        def parse_sfile(fname, name):
            line = None
            with open(fname, "r") as fp:
                for cline in fp:
                    if cline.startswith(name + ":"):
                        line = cline
                        break
            if line is None:
                raise ValueError("%s not found in %s" % (name, fname))
            toks = line.split(":")
            return (toks[1], toks[2])

        ustart, unum = parse_sfile(subuid_f, user)
        gstart, gnum = parse_sfile(subgid_f, group)

        self.user = user
        self.group = group
        super(LXCUserIdMap, self).__init__(ustart, unum, gstart, gnum)
