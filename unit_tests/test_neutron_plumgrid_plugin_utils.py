from mock import MagicMock
from collections import OrderedDict
import charmhelpers.contrib.openstack.templating as templating

templating.OSConfigRenderer = MagicMock()

import neutron_plumgrid_utils as nutils

from test_utils import (
    CharmTestCase,
)
import charmhelpers.core.hookenv as hookenv


TO_PATCH = [
    'os_release',
    'pip_install',
]


class DummyContext():

    def __init__(self, return_value):
        self.return_value = return_value

    def __call__(self):
        return self.return_value


class TestNeutronPGUtils(CharmTestCase):

    def setUp(self):
        super(TestNeutronPGUtils, self).setUp(nutils, TO_PATCH)

    def tearDown(self):
        # Reset cached cache
        hookenv.cache = {}

    def test_register_configs(self):
        class _mock_OSConfigRenderer():
            def __init__(self, templates_dir=None, openstack_release=None):
                self.configs = []
                self.ctxts = []

            def register(self, config, ctxt):
                self.configs.append(config)
                self.ctxts.append(ctxt)

        self.os_release.return_value = 'kilo'
        templating.OSConfigRenderer.side_effect = _mock_OSConfigRenderer
        _regconfs = nutils.register_configs()
        confs = ['/etc/sudoers.d/neutron_sudoers',
                 '/etc/neutron/plugins/plumgrid/plumlib.ini',
                 '/etc/neutron/plugins/plumgrid/pgrc']
        self.assertItemsEqual(_regconfs.configs, confs)

    def test_resource_map(self):
        _map = nutils.resource_map()
        svcs = ['neutron-server']
        confs = [nutils.PGLIB_CONF]
        [self.assertIn(q_conf, _map.keys()) for q_conf in confs]
        self.assertEqual(_map[nutils.PGLIB_CONF]['services'], svcs)

    def test_restart_map(self):
        _restart_map = nutils.restart_map()
        expect = OrderedDict([
            (nutils.PGLIB_CONF, ['neutron-server']),
            (nutils.PGRC, ['neutron-server']),
        ])
        self.assertEqual(expect, _restart_map)
        for item in _restart_map:
            self.assertTrue(item in _restart_map)
            self.assertTrue(expect[item] == _restart_map[item])
