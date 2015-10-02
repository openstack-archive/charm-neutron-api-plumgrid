from mock import MagicMock, patch, call
from test_utils import CharmTestCase

with patch('charmhelpers.core.hookenv.config') as config:
    config.return_value = 'neutron'
    import neutron_plumgrid_utils as utils

_reg = utils.register_configs
_map = utils.restart_map

utils.register_configs = MagicMock()
utils.restart_map = MagicMock()

import neutron_plumgrid_hooks as hooks

utils.register_configs = _reg
utils.restart_map = _map

TO_PATCH = [
    'configure_sources',
    'apt_update',
    'apt_purge',
    'apt_install',
    'CONFIGS',
    'ensure_files',
    'stop',
    'determine_packages',
]
NEUTRON_CONF_DIR = "/etc/neutron"

NEUTRON_CONF = '%s/neutron.conf' % NEUTRON_CONF_DIR


class NeutronPGHooksTests(CharmTestCase):

    def setUp(self):
        super(NeutronPGHooksTests, self).setUp(hooks, TO_PATCH)
        hooks.hooks._config_save = False

    def _call_hook(self, hookname):
        hooks.hooks.execute([
            'hooks/{}'.format(hookname)])

    def test_install_hook(self):
        _pkgs = ['plumgrid-pythonlib']
        self.determine_packages.return_value = [_pkgs]
        self._call_hook('install')
        self.configure_sources.assert_called_with()
        self.apt_update.assert_called_with()
        self.apt_install.assert_has_calls([
            call(_pkgs, fatal=True,
                 options=['--force-yes']),
        ])
        self.ensure_files.assert_called_with()

    def test_config_changed_hook(self):
        _pkgs = ['plumgrid-pythonlib']
        self.determine_packages.return_value = [_pkgs]
        self._call_hook('config-changed')
        self.stop.assert_called_with()
        self.configure_sources.assert_called_with()
        self.apt_update.assert_called_with()
        self.apt_install.assert_has_calls([
            call(_pkgs, fatal=True,
                 options=['--force-yes']),
        ])
        self.ensure_files.assert_called_with()
        self.CONFIGS.write_all.assert_called_with()

    def test_neutron_api_joined(self):
        self._call_hook('neutron-plugin-api-relation-joined')
        self.ensure_files.assert_called_with()
        self.CONFIGS.write_all.assert_called_with()

    def test_container_changed(self):
        self._call_hook('container-relation-changed')
        self.ensure_files.assert_called_with()
        self.CONFIGS.write_all.assert_called_with()

    def test_stop(self):
        _pkgs = ['plumgrid-pythonlib']
        self.determine_packages.return_value = [_pkgs]
        self._call_hook('stop')
        self.apt_purge.assert_has_calls([
            call(_pkgs, fatal=False)
        ])
