# Copyright 2016 Canonical Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import amulet
import os
import yaml

from charmhelpers.contrib.openstack.amulet.deployment import (
    OpenStackAmuletDeployment
)

from charmhelpers.contrib.openstack.amulet.utils import (
    OpenStackAmuletUtils,
    DEBUG,
    # ERROR
)

# Use DEBUG to turn on debug logging
u = OpenStackAmuletUtils(DEBUG)


class NeutronAPIBasicDeployment(OpenStackAmuletDeployment):
    """Amulet tests on a basic neutron-api deployment."""

    def __init__(self, series, openstack=None, source=None, git=False,
                 stable=False):
        """Deploy the entire test environment."""
        super(NeutronAPIBasicDeployment, self).__init__(series, openstack,
                                                        source, stable)
        self.git = git
        self._add_services()
        self._add_relations()
        self._configure_services()
        self._deploy()

        u.log.info('Waiting on extended status checks...')
        exclude_services = []
        self._auto_wait_for_status(exclude_services=exclude_services)

        self.d.sentry.wait()
        self._initialize_tests()

    def _assert_services(self, should_run):
        services = ("neutron-server", "apache2", "haproxy")
        u.get_unit_process_ids(
            {self.neutron_api_sentry: services},
            expect_success=should_run)

    def _add_services(self):
        """Add services

           Add the services that we're testing, where neutron-api is local,
           and the rest of the service are from lp branches that are
           compatible with the local charm (e.g. stable or next).
           """
        this_service = {'name': 'neutron-api'}
        other_services = [
            {'name': 'percona-cluster', 'constraints': {'mem': '3072M'}},
            {'name': 'rabbitmq-server'},
            {'name': 'keystone'},
            {'name': 'glance'},  # to satisfy workload status
            {'name': 'neutron-openvswitch'},
            {'name': 'nova-cloud-controller'},
            {'name': 'neutron-gateway'},
            {'name': 'nova-compute'}
        ]
        super(NeutronAPIBasicDeployment, self)._add_services(this_service,
                                                             other_services)

    def _add_relations(self):
        """Add all of the relations for the services."""
        relations = {
            'neutron-api:shared-db': 'percona-cluster:shared-db',
            'neutron-api:amqp': 'rabbitmq-server:amqp',
            'neutron-api:neutron-api': 'nova-cloud-controller:neutron-api',
            'neutron-api:neutron-plugin-api': 'neutron-gateway:'
                                              'neutron-plugin-api',
            'neutron-api:identity-service': 'keystone:identity-service',
            'keystone:shared-db': 'percona-cluster:shared-db',
            'nova-compute:neutron-plugin': 'neutron-openvswitch:'
                                           'neutron-plugin',
            'nova-cloud-controller:shared-db': 'percona-cluster:shared-db',
            'neutron-gateway:amqp': 'rabbitmq-server:amqp',
            'nova-cloud-controller:amqp': 'rabbitmq-server:amqp',
            'nova-compute:amqp': 'rabbitmq-server:amqp',
            'neutron-openvswitch:amqp': 'rabbitmq-server:amqp',
            'nova-cloud-controller:identity-service': 'keystone:'
                                                      'identity-service',
            'nova-cloud-controller:cloud-compute': 'nova-compute:'
                                                   'cloud-compute',
            'glance:identity-service': 'keystone:identity-service',
            'glance:shared-db': 'percona-cluster:shared-db',
            'glance:amqp': 'rabbitmq-server:amqp',
            'nova-compute:image-service': 'glance:image-service',
            'nova-cloud-controller:image-service': 'glance:image-service',
        }

        # NOTE(beisner): relate this separately due to the resulting
        # duplicate dictionary key if included in the relations dict.
        relations_more = {
            'neutron-api:neutron-plugin-api': 'neutron-openvswitch:'
                                              'neutron-plugin-api',
        }
        super(NeutronAPIBasicDeployment, self)._add_relations(relations)
        super(NeutronAPIBasicDeployment, self)._add_relations(relations_more)

    def _configure_services(self):
        """Configure all of the services."""
        neutron_api_config = {}
        if self.git:
            amulet_http_proxy = os.environ.get('AMULET_HTTP_PROXY')

            branch = 'stable/' + self._get_openstack_release_string()

            if self._get_openstack_release() >= self.trusty_kilo:
                openstack_origin_git = {
                    'repositories': [
                        {'name': 'requirements',
                         'repository': 'git://github.com/openstack/requirements',  # noqa
                         'branch': branch},
                        {'name': 'neutron-fwaas',
                         'repository': 'git://github.com/openstack/neutron-fwaas',  # noqa
                         'branch': branch},
                        {'name': 'neutron-lbaas',
                         'repository': 'git://github.com/openstack/neutron-lbaas',  # noqa
                         'branch': branch},
                        {'name': 'neutron-vpnaas',
                         'repository': 'git://github.com/openstack/neutron-vpnaas',  # noqa
                         'branch': branch},
                        {'name': 'neutron',
                         'repository': 'git://github.com/openstack/neutron',
                         'branch': branch},
                    ],
                    'directory': '/mnt/openstack-git',
                    'http_proxy': amulet_http_proxy,
                    'https_proxy': amulet_http_proxy,
                }
            else:
                reqs_repo = 'git://github.com/openstack/requirements'
                neutron_repo = 'git://github.com/openstack/neutron'
                if self._get_openstack_release() == self.trusty_icehouse:
                    reqs_repo = 'git://github.com/coreycb/requirements'
                    neutron_repo = 'git://github.com/coreycb/neutron'

                openstack_origin_git = {
                    'repositories': [
                        {'name': 'requirements',
                         'repository': reqs_repo,
                         'branch': branch},
                        {'name': 'neutron',
                         'repository': neutron_repo,
                         'branch': branch},
                    ],
                    'directory': '/mnt/openstack-git',
                    'http_proxy': amulet_http_proxy,
                    'https_proxy': amulet_http_proxy,
                }
            neutron_api_config['openstack-origin-git'] = \
                yaml.dump(openstack_origin_git)

        keystone_config = {'admin-password': 'openstack',
                           'admin-token': 'ubuntutesting'}
        nova_cc_config = {'network-manager': 'Neutron'}
        pxc_config = {
            'dataset-size': '25%',
            'max-connections': 1000,
            'root-password': 'ChangeMe123',
            'sst-password': 'ChangeMe123',
        }

        configs = {
            'neutron-api': neutron_api_config,
            'keystone': keystone_config,
            'percona-cluster': pxc_config,
            'nova-cloud-controller': nova_cc_config,
        }
        super(NeutronAPIBasicDeployment, self)._configure_services(configs)

    def _initialize_tests(self):
        """Perform final initialization before tests get run."""
        # Access the sentries for inspecting service units
        self.pxc_sentry = self.d.sentry['percona-cluster'][0]
        self.keystone_sentry = self.d.sentry['keystone'][0]
        self.rabbitmq_sentry = self.d.sentry['rabbitmq-server'][0]
        self.nova_cc_sentry = self.d.sentry['nova-cloud-controller'][0]
        self.neutron_gw_sentry = self.d.sentry['neutron-gateway'][0]
        self.neutron_api_sentry = self.d.sentry['neutron-api'][0]
        self.neutron_ovs_sentry = self.d.sentry['neutron-openvswitch'][0]
        self.nova_compute_sentry = self.d.sentry['nova-compute'][0]

        u.log.debug('openstack release val: {}'.format(
            self._get_openstack_release()))
        u.log.debug('openstack release str: {}'.format(
            self._get_openstack_release_string()))

    def test_100_services(self):
        """Verify the expected services are running on the corresponding
           service units."""
        u.log.debug('Checking status of system services...')
        neutron_api_services = ['neutron-server']
        if self._get_openstack_release() >= self.xenial_newton:
            neutron_services = ['neutron-dhcp-agent',
                                'neutron-lbaasv2-agent',
                                'neutron-metadata-agent',
                                'neutron-openvswitch-agent']
        elif self._get_openstack_release() >= self.trusty_mitaka and \
                self._get_openstack_release() < self.xenial_newton:
            neutron_services = ['neutron-dhcp-agent',
                                'neutron-lbaas-agent',
                                'neutron-metadata-agent',
                                'neutron-openvswitch-agent']
        else:
            neutron_services = ['neutron-dhcp-agent',
                                'neutron-lbaas-agent',
                                'neutron-metadata-agent',
                                'neutron-plugin-openvswitch-agent']

        if self._get_openstack_release() <= self.trusty_juno:
            neutron_services.append('neutron-vpn-agent')

        if self._get_openstack_release() < self.trusty_kilo:
            neutron_services.append('neutron-metering-agent')

        nova_cc_services = ['nova-api-os-compute',
                            'nova-cert',
                            'nova-scheduler',
                            'nova-conductor']

        services = {
            self.keystone_sentry: ['keystone'],
            self.nova_cc_sentry: nova_cc_services,
            self.neutron_gw_sentry: neutron_services,
            self.neutron_api_sentry: neutron_api_services,
        }

        if self._get_openstack_release() >= self.trusty_liberty:
            services[self.keystone_sentry] = ['apache2']

        ret = u.validate_services_by_name(services)
        if ret:
            amulet.raise_status(amulet.FAIL, msg=ret)

    def test_200_neutron_api_shared_db_relation(self):
        """Verify the neutron-api to mysql shared-db relation data"""
        u.log.debug('Checking neutron-api:mysql db relation data...')
        unit = self.neutron_api_sentry
        relation = ['shared-db', 'percona-cluster:shared-db']
        expected = {
            'private-address': u.valid_ip,
            'database': 'neutron',
            'username': 'neutron',
            'hostname': u.valid_ip
        }

        ret = u.validate_relation_data(unit, relation, expected)
        if ret:
            message = u.relation_error('neutron-api shared-db', ret)
            amulet.raise_status(amulet.FAIL, msg=message)

    def test_201_shared_db_neutron_api_relation(self):
        """Verify the mysql to neutron-api shared-db relation data"""
        u.log.debug('Checking mysql:neutron-api db relation data...')
        unit = self.pxc_sentry
        relation = ['shared-db', 'neutron-api:shared-db']
        expected = {
            'db_host': u.valid_ip,
            'private-address': u.valid_ip,
            'password': u.not_null
        }

        ret = u.validate_relation_data(unit, relation, expected)
        if ret:
            message = u.relation_error('mysql shared-db', ret)
            amulet.raise_status(amulet.FAIL, msg=message)

    def test_202_neutron_api_amqp_relation(self):
        """Verify the neutron-api to rabbitmq-server amqp relation data"""
        u.log.debug('Checking neutron-api:amqp relation data...')
        unit = self.neutron_api_sentry
        relation = ['amqp', 'rabbitmq-server:amqp']
        expected = {
            'username': 'neutron',
            'private-address': u.valid_ip,
            'vhost': 'openstack'
        }

        ret = u.validate_relation_data(unit, relation, expected)
        if ret:
            message = u.relation_error('neutron-api amqp', ret)
            amulet.raise_status(amulet.FAIL, msg=message)

    def test_203_amqp_neutron_api_relation(self):
        """Verify the rabbitmq-server to neutron-api amqp relation data"""
        u.log.debug('Checking amqp:neutron-api relation data...')
        unit = self.rabbitmq_sentry
        relation = ['amqp', 'neutron-api:amqp']
        expected = {
            'hostname': u.valid_ip,
            'private-address': u.valid_ip,
            'password': u.not_null
        }

        ret = u.validate_relation_data(unit, relation, expected)
        if ret:
            message = u.relation_error('rabbitmq amqp', ret)
            amulet.raise_status(amulet.FAIL, msg=message)

    def test_204_neutron_api_keystone_identity_relation(self):
        """Verify the neutron-api to keystone identity-service relation data"""
        u.log.debug('Checking neutron-api:keystone id relation data...')
        unit = self.neutron_api_sentry
        relation = ['identity-service', 'keystone:identity-service']
        api_ip = unit.relation('identity-service',
                               'keystone:identity-service')['private-address']
        api_endpoint = 'http://{}:9696'.format(api_ip)
        expected = {
            'private-address': u.valid_ip,
            'neutron_region': 'RegionOne',
            'neutron_service': 'neutron',
            'neutron_admin_url': api_endpoint,
            'neutron_internal_url': api_endpoint,
            'neutron_public_url': api_endpoint,
        }

        ret = u.validate_relation_data(unit, relation, expected)
        if ret:
            message = u.relation_error('neutron-api identity-service', ret)
            amulet.raise_status(amulet.FAIL, msg=message)

    def test_205_keystone_neutron_api_identity_relation(self):
        """Verify the keystone to neutron-api identity-service relation data"""
        u.log.debug('Checking keystone:neutron-api id relation data...')
        unit = self.keystone_sentry
        relation = ['identity-service', 'neutron-api:identity-service']
        rel_ks_id = unit.relation('identity-service',
                                  'neutron-api:identity-service')
        id_ip = rel_ks_id['private-address']
        expected = {
            'admin_token': 'ubuntutesting',
            'auth_host': id_ip,
            'auth_port': "35357",
            'auth_protocol': 'http',
            'private-address': id_ip,
            'service_host': id_ip,
        }
        ret = u.validate_relation_data(unit, relation, expected)
        if ret:
            message = u.relation_error('neutron-api identity-service', ret)
            amulet.raise_status(amulet.FAIL, msg=message)

    def test_206_neutron_api_neutron_ovs_plugin_api_relation(self):
        """Verify neutron-api to neutron-openvswitch neutron-plugin-api"""
        u.log.debug('Checking neutron-api:neutron-ovs plugin-api '
                    'relation data...')
        unit = self.neutron_api_sentry
        relation = ['neutron-plugin-api',
                    'neutron-openvswitch:neutron-plugin-api']

        u.log.debug(unit.relation(relation[0], relation[1]))
        expected = {
            'auth_host': u.valid_ip,
            'auth_port': '35357',
            'auth_protocol': 'http',
            'enable-dvr': 'False',
            'enable-l3ha': 'False',
            'l2-population': 'True',
            'neutron-security-groups': 'False',
            'overlay-network-type': 'gre',
            'private-address': u.valid_ip,
            'region': 'RegionOne',
            'service_host': u.valid_ip,
            'service_password': u.not_null,
            'service_port': '5000',
            'service_protocol': 'http',
            'service_tenant': 'services',
            'service_username': 'neutron',
        }
        ret = u.validate_relation_data(unit, relation, expected)
        if ret:
            message = u.relation_error(
                'neutron-api neutron-ovs neutronplugin-api', ret)
            amulet.raise_status(amulet.FAIL, msg=message)

    def test_207_neutron_ovs_neutron_api_plugin_api_relation(self):
        """Verify neutron-openvswitch to neutron-api neutron-plugin-api"""
        u.log.debug('Checking neutron-ovs:neutron-api plugin-api '
                    'relation data...')
        unit = self.neutron_ovs_sentry
        relation = ['neutron-plugin-api',
                    'neutron-api:neutron-plugin-api']
        expected = {
            'private-address': u.valid_ip,
        }
        ret = u.validate_relation_data(unit, relation, expected)
        if ret:
            message = u.relation_error('neutron-api neutron-plugin-api', ret)
            amulet.raise_status(amulet.FAIL, msg=message)

    def test_208_neutron_api_novacc_relation(self):
        """Verify the neutron-api to nova-cloud-controller relation data"""
        u.log.debug('Checking neutron-api:novacc relation data...')
        unit = self.neutron_api_sentry
        relation = ['neutron-api', 'nova-cloud-controller:neutron-api']
        api_ip = unit.relation('identity-service',
                               'keystone:identity-service')['private-address']
        api_endpoint = 'http://{}:9696'.format(api_ip)
        expected = {
            'private-address': api_ip,
            'neutron-plugin': 'ovs',
            'neutron-security-groups': "no",
            'neutron-url': api_endpoint,
        }
        ret = u.validate_relation_data(unit, relation, expected)
        if ret:
            message = u.relation_error('neutron-api neutron-api', ret)
            amulet.raise_status(amulet.FAIL, msg=message)

    def test_209_novacc_neutron_api_relation(self):
        """Verify the nova-cloud-controller to neutron-api relation data"""
        u.log.debug('Checking novacc:neutron-api relation data...')
        unit = self.nova_cc_sentry
        relation = ['neutron-api', 'neutron-api:neutron-api']
        cc_ip = unit.relation('neutron-api',
                              'neutron-api:neutron-api')['private-address']
        cc_endpoint = 'http://{}:8774/v2'.format(cc_ip)
        expected = {
            'private-address': cc_ip,
            'nova_url': cc_endpoint,
        }
        ret = u.validate_relation_data(unit, relation, expected)
        if ret:
            message = u.relation_error('nova-cc neutron-api', ret)
            amulet.raise_status(amulet.FAIL, msg=message)

    def test_300_neutron_config(self):
        """Verify the data in the neutron config file."""
        u.log.debug('Checking neutron.conf config file data...')
        unit = self.neutron_api_sentry
        cc_relation = self.nova_cc_sentry.relation('neutron-api',
                                                   'neutron-api:neutron-api')
        rabbitmq_relation = self.rabbitmq_sentry.relation('amqp',
                                                          'neutron-api:amqp')
        rel_napi_ks = self.keystone_sentry.relation(
            'identity-service', 'neutron-api:identity-service')

        nova_auth_url = '{}://{}:{}/v2.0'.format(rel_napi_ks['auth_protocol'],
                                                 rel_napi_ks['auth_host'],
                                                 rel_napi_ks['auth_port'])
        rel_napi_db = self.pxc_sentry.relation('shared-db',
                                               'neutron-api:shared-db')
        db_conn = 'mysql://neutron:{}@{}/neutron'.format(
            rel_napi_db['password'], rel_napi_db['db_host'])

        conf = '/etc/neutron/neutron.conf'
        expected = {
            'DEFAULT': {
                'verbose': 'False',
                'debug': 'False',
                'bind_port': '9686',
            },
            'database': {
                'connection': db_conn,
            },
        }

        auth_uri = '{}://{}:{}'.format(
            rel_napi_ks['service_protocol'],
            rel_napi_ks['service_host'],
            rel_napi_ks['service_port']
        )
        auth_url = '{}://{}:{}'.format(
            rel_napi_ks['auth_protocol'],
            rel_napi_ks['auth_host'],
            rel_napi_ks['auth_port']
        )

        if self._get_openstack_release() >= self.trusty_mitaka:
            expected['nova'] = {
                'auth_section': 'keystone_authtoken',
            }
            expected['keystone_authtoken'] = {
                'auth_uri': auth_uri.rstrip('/'),
                'auth_url': auth_url.rstrip('/'),
                'auth_type': 'password',
                'project_domain_name': 'default',
                'user_domain_name': 'default',
                'project_name': 'services',
                'username': rel_napi_ks['service_username'],
                'password': rel_napi_ks['service_password'],
                'signing_dir': '/var/cache/neutron'
            }
        elif self._get_openstack_release() >= self.trusty_liberty:
            expected['nova'] = {
                'auth_section': 'keystone_authtoken',
            }
            expected['keystone_authtoken'] = {
                'auth_uri': auth_uri,
                'auth_url': auth_url,
                'auth_plugin': 'password',
                'project_domain_id': 'default',
                'user_domain_id': 'default',
                'project_name': rel_napi_ks['service_tenant'],
                'username': 'neutron',
                'password': rel_napi_ks['service_password'],
                'signing_dir': '/var/cache/neutron',
            }
        elif self._get_openstack_release() == self.trusty_kilo:
            expected['keystone_authtoken'] = {
                'auth_uri': auth_uri + '/',
                'identity_uri': auth_url,
                'admin_tenant_name': rel_napi_ks['service_tenant'],
                'admin_user': 'neutron',
                'admin_password': rel_napi_ks['service_password'],
                'signing_dir': '/var/cache/neutron',
            }
        else:
            expected['keystone_authtoken'] = {
                'admin_tenant_name': rel_napi_ks['service_tenant'],
                'admin_user': 'neutron',
                'admin_password': rel_napi_ks['service_password'],
                'signing_dir': '/var/cache/neutron',
                'service_protocol': rel_napi_ks['service_protocol'],
                'service_host': rel_napi_ks['service_host'],
                'service_port': rel_napi_ks['service_port'],
                'auth_host': rel_napi_ks['auth_host'],
                'auth_port': rel_napi_ks['auth_port'],
                'auth_protocol': rel_napi_ks['auth_protocol']
            }

            expected['DEFAULT'].update({
                'nova_url': cc_relation['nova_url'],
                'nova_region_name': 'RegionOne',
                'nova_admin_username': rel_napi_ks['service_username'],
                'nova_admin_tenant_id': rel_napi_ks['service_tenant_id'],
                'nova_admin_password': rel_napi_ks['service_password'],
                'nova_admin_auth_url': nova_auth_url,
            })

        if self._get_openstack_release() >= self.trusty_kilo:
            # Kilo or later - rabbit bits
            expected['oslo_messaging_rabbit'] = {
                'rabbit_userid': 'neutron',
                'rabbit_virtual_host': 'openstack',
                'rabbit_password': rabbitmq_relation['password'],
                'rabbit_host': rabbitmq_relation['hostname']
            }
        else:
            # Juno or earlier - rabbit bits
            expected['DEFAULT'].update({
                'rabbit_userid': 'neutron',
                'rabbit_virtual_host': 'openstack',
                'rabbit_password': rabbitmq_relation['password'],
                'rabbit_host': rabbitmq_relation['hostname']
            })

        for section, pairs in expected.iteritems():
            ret = u.validate_config_data(unit, conf, section, pairs)
            if ret:
                message = "neutron config error: {}".format(ret)
                amulet.raise_status(amulet.FAIL, msg=message)

    def test_301_ml2_config(self):
        """Verify the data in the ml2 config file. This is only available
           since icehouse."""
        u.log.debug('Checking ml2 config file data...')
        unit = self.neutron_api_sentry
        conf = '/etc/neutron/plugins/ml2/ml2_conf.ini'
        neutron_api_relation = unit.relation(
            'shared-db', 'percona-cluster:shared-db')

        expected = {
            'ml2': {
                'type_drivers': 'gre,vlan,flat,local',
                'tenant_network_types': 'gre,vlan,flat,local',
            },
            'ml2_type_gre': {
                'tunnel_id_ranges': '1:1000'
            },
            'ml2_type_vxlan': {
                'vni_ranges': '1001:2000'
            },
            'ovs': {
                'enable_tunneling': 'True',
                'local_ip': neutron_api_relation['private-address']
            },
            'agent': {
                'tunnel_types': 'gre',
            },
            'securitygroup': {
                'enable_security_group': 'False',
            }
        }

        if (self._get_openstack_release() in
           [self.trusty_liberty, self.wily_liberty]):
            # Liberty
            expected['ml2'].update({
                'mechanism_drivers': 'openvswitch,l2population'
            })
        else:
            # Earlier or later than Liberty
            expected['ml2'].update({
                'mechanism_drivers': 'openvswitch,hyperv,l2population'
            })

        for section, pairs in expected.iteritems():
            ret = u.validate_config_data(unit, conf, section, pairs)
            if ret:
                message = "ml2 config error: {}".format(ret)
                amulet.raise_status(amulet.FAIL, msg=message)

    def test_900_restart_on_config_change(self):
        """Verify that the specified services are restarted when the
        config is changed."""

        sentry = self.neutron_api_sentry
        juju_service = 'neutron-api'

        # Expected default and alternate values
        set_default = {'debug': 'False'}
        set_alternate = {'debug': 'True'}

        # Services which are expected to restart upon config change,
        # and corresponding config files affected by the change
        services = {'neutron-server': '/etc/neutron/neutron.conf'}

        # Make config change, check for service restarts
        u.log.debug('Making config change on {}...'.format(juju_service))
        mtime = u.get_sentry_time(sentry)
        self.d.configure(juju_service, set_alternate)

        for s, conf_file in services.iteritems():
            u.log.debug("Checking that service restarted: {}".format(s))
            if not u.validate_service_config_changed(sentry, mtime, s,
                                                     conf_file,
                                                     retry_count=4,
                                                     retry_sleep_time=20,
                                                     sleep_time=20):
                self.d.configure(juju_service, set_default)
                msg = "service {} didn't restart after config change".format(s)
                amulet.raise_status(amulet.FAIL, msg=msg)

        self.d.configure(juju_service, set_default)
        u.log.debug('OK')

    def test_901_pause_resume(self):
        """Test pause and resume actions."""
        self._assert_services(should_run=True)
        action_id = u.run_action(self.neutron_api_sentry, "pause")
        assert u.wait_on_action(action_id), "Pause action failed."

        self._assert_services(should_run=False)

        action_id = u.run_action(self.neutron_api_sentry, "resume")
        assert u.wait_on_action(action_id), "Resume action failed"
        self._assert_services(should_run=True)
