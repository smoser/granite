import os
import tempfile


from oslo.config import cfg

from nova import exception
from nova.openstack.common import excutils
from nova.openstack.common import fileutils
from nova.openstack.common.gettextutils import _
from nova.openstack.common import log as logging
from nova import utils
from nova.virt.disk import api as disk
from nova.virt import images

CONF = cfg.CONF
CONF.import_opt('use_cow_images', 'nova.virt.driver')
LOG = logging.getLogger(__name__)

class ImageBackend(object):
    def __init__(self):
        self.image_path = None

    def create_image(self, context, instance):
        base_dir = os.path.join(CONF.instances_path,
                                CONF.image_cache_subdirectory_name)
        if not os.path.exists(base_dir):
            fileutils.ensure_tree(base_dir)
        filename = instance['image_ref']
        base = os.path.join(base_dir, filename)
        container_rootfs = os.path.join(CONF.instances_path, instance['uuid'], 
                                        'rootfs')
        if not os.path.exists(base):
            images.fetch_to_raw(context, instance['image_ref'], base,
                                instance['user_id'], instance['project_id'])
        if not os.path.exists(container_rootfs):
            fileutils.ensure_tree(container_rootfs)
        tmpfolder = tempfile.mkdtemp(instance['uuid'])

        disk.setup_container(base,
                             container_dir=tmpfolder,
                             use_cow=CONF.use_cow_images)
        tmproot = '%s/' % tmpfolder
        utils.execute('rsync', '-H', '-a', tmproot, container_rootfs,
                      run_as_root=True)
        utils.execute('chown', '-R', '%s:%s' % (CONF.lxc.lxc_subuid, CONF.lxc.lxc_subgid),
                      container_rootfs, run_as_root=True)
        disk.teardown_container(container_dir=tmpfolder)
        os.rmdir(tmpfolder)

        return container_rootfs
