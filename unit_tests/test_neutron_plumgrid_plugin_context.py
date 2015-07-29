from test_utils import CharmTestCase
from mock import patch
import neutron_plumgrid_context as context
import charmhelpers

TO_PATCH = [
    'config',
]


def fake_context(settings):
    def outer():
        def inner():
            return settings
        return inner
    return outer


class NeutronPGContextTest(CharmTestCase):

    def setUp(self):
        super(NeutronPGContextTest, self).setUp(context, TO_PATCH)
        self.config.side_effect = self.test_config.get
        self.test_config.set('enable-metadata', False)

    def tearDown(self):
        super(NeutronPGContextTest, self).tearDown()

    @patch.object(context, '_container_settings')
    @patch.object(charmhelpers.contrib.openstack.context, 'config',
                  lambda *args: None)
    @patch.object(charmhelpers.contrib.openstack.context, 'relation_get')
    @patch.object(charmhelpers.contrib.openstack.context, 'relation_ids')
    @patch.object(charmhelpers.contrib.openstack.context, 'related_units')
    @patch.object(charmhelpers.contrib.openstack.context, 'config')
    @patch.object(charmhelpers.contrib.openstack.context, 'unit_get')
    @patch.object(charmhelpers.contrib.openstack.context, 'is_clustered')
    @patch.object(charmhelpers.contrib.openstack.context, 'https')
    @patch.object(context.NeutronPGPluginContext, '_save_flag_file')
    @patch.object(context.NeutronPGPluginContext, '_ensure_packages')
    @patch.object(charmhelpers.contrib.openstack.context,
                  'neutron_plugin_attribute')
    @patch.object(charmhelpers.contrib.openstack.context, 'unit_private_ip')
    def test_neutroncc_context_api_rel(self, _unit_priv_ip, _npa, _ens_pkgs,
                                       _save_ff, _https, _is_clus, _unit_get,
                                       _config, _runits, _rids, _rget, _con_settings):
        def mock_npa(plugin, section, manager):
            if section == "driver":
                return "neutron.randomdriver"
            if section == "config":
                return "neutron.randomconfig"

        config = {'enable-metadata': False}

        def mock_config(key=None):
            if key:
                return config.get(key)

            return config

        self.maxDiff = None
        self.config.side_effect = mock_config
        _npa.side_effect = mock_npa
        _con_settings.return_value = {
            'auth_host': '10.0.0.1',
            'auth_port': '35357',
            'auth_protocol': 'http',
            'service_tenant': 'admin',
            'service_username': 'admin',
            'service_password': 'admin',
        }
        _unit_get.return_value = '192.168.100.201'
        _unit_priv_ip.return_value = '192.168.100.201'
        napi_ctxt = context.NeutronPGPluginContext()
        expect = {
            'enable_metadata': False,
            'config': 'neutron.randomconfig',
            'core_plugin': 'neutron.randomdriver',
            'local_ip': '192.168.100.201',
            'network_manager': 'neutron',
            'neutron_plugin': 'plumgrid',
            'neutron_security_groups': None,
            'neutron_url': 'https://None:9696',
            'admin_user': 'admin',
            'admin_password': 'admin',
            'admin_tenant_name': 'admin',
            'service_protocol': 'http',
            'auth_port': '35357',
            'auth_host': '10.0.0.1',
        }
        self.assertEquals(expect, napi_ctxt())
