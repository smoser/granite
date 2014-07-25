import mox

from granite.virt.lxc import driver as lxc_driver

from nova import test

class GraniteDriverTestCase(test.TestCase):
    def setUp(self):
        super(GraniteDriverTestCase, self).setUp()
