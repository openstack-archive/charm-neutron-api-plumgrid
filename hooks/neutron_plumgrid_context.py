# Copyright (c) 2015, PLUMgrid Inc, http://plumgrid.com

# This file contains the class that generates context for PLUMgrid template files.

from charmhelpers.core.hookenv import (
    config,
    relation_ids,
    related_units,
    relation_get,
)
from charmhelpers.contrib.openstack import context


def _container_settings():
    '''
    Inspects current container relation to get keystone context.
    '''
    container_settings = {
        'auth_host': '10.0.0.1',
        'auth_port': '35357',
        'auth_protocol': 'http',
        'service_protocol': 'http',
        'service_host': '10.0.0.1',
        'service_port': '35357',
        'service_tenant': 'admin',
        'service_username': 'admin',
        'service_password': 'admin',
    }
    for rid in relation_ids('container'):
        for unit in related_units(rid):
            rdata = relation_get(rid=rid, unit=unit)
            if 'auth_host' not in rdata:
                continue
            container_settings = {
                'auth_host': rdata['auth_host'],
                'auth_port': rdata['auth_port'],
                'auth_protocol': rdata['auth_protocol'],
                'service_protocol': rdata['service_protocol'],
                'service_host': rdata['service_host'],
                'service_port': rdata['service_port'],
                'service_tenant': rdata['service_tenant'],
                'service_username': rdata['service_username'],
                'service_password': rdata['service_password'],
            }
            return container_settings
    return container_settings


class NeutronPGPluginContext(context.NeutronContext):

    @property
    def plugin(self):
        '''
        Over-riding function in NeutronContext Class to return 'plumgrid'
        as the neutron plugin.
        '''
        return 'plumgrid'

    @property
    def network_manager(self):
        '''
        Over-riding function in NeutronContext Class to return 'neutron'
        as the network manager.
        '''
        return 'neutron'

    def _ensure_packages(self):
        '''
        Over-riding function in NeutronContext Class.
        Function only runs on compute nodes.
        '''
        pass

    def _save_flag_file(self):
        '''
        Over-riding function in NeutronContext Class.
        Function only needed for OVS.
        '''
        pass

    def pg_ctxt(self):
        '''
        Generated Config for all PLUMgrid templates inside the templates folder.
        '''
        pg_ctxt = super(NeutronPGPluginContext, self).pg_ctxt()
        if not pg_ctxt:
            return {}

        conf = config()
        pg_ctxt['enable_metadata'] = conf['enable-metadata']
        pg_ctxt['pg_metadata_ip'] = '169.254.169.254'
        pg_ctxt['pg_metadata_port'] = '8775'
        pg_ctxt['nova_metadata_proxy_secret'] = 'plumgrid'
        pg_ctxt['metadata_mode'] = 'tunnel'

        neutron_api_settings = _container_settings()
        pg_ctxt['admin_user'] = neutron_api_settings['service_username']
        pg_ctxt['admin_password'] = neutron_api_settings['service_password']
        pg_ctxt['admin_tenant_name'] = neutron_api_settings['service_tenant']
        pg_ctxt['service_protocol'] = neutron_api_settings['auth_protocol']
        pg_ctxt['auth_port'] = neutron_api_settings['auth_port']
        pg_ctxt['auth_host'] = neutron_api_settings['auth_host']

        return pg_ctxt
