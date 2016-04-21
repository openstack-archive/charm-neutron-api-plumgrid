# Copyright (c) 2015, PLUMgrid Inc, http://plumgrid.com

# This file contains the class that generates context for
# PLUMgrid template files.

from charmhelpers.core.hookenv import (
    config,
    relation_ids,
    related_units,
    relation_get,
)
from charmhelpers.contrib.openstack import context
from socket import gethostbyname


def _edge_settings():
    '''
    Inspects plumgrid-edge relation to get metadata shared secret.
    '''
    ctxt = {
        'metadata_shared_secret': 'plumgrid',
    }
    for rid in relation_ids('plumgrid-plugin'):
        for unit in related_units(rid):
            rdata = relation_get(rid=rid, unit=unit)
            if 'metadata-shared-secret' in rdata:
                ctxt['metadata_shared_secret'] = \
                    rdata['metadata-shared-secret']
    return ctxt


def _identity_context():
    ctxs = [ { "auth_host": gethostbyname(hostname),
               "auth_port": relation_get("service_port", unit, rid),
               "admin_user": relation_get("service_username", unit, rid),
               "admin_password": relation_get("service_password", unit, rid),
               "service_protocol": relation_get("auth_protocol", unit, rid) or 'http',
               "admin_tenant_name": relation_get("service_tenant_name", unit, rid) }
             for rid in relation_ids("identity-admin")
             for unit, hostname in
             ((unit, relation_get("service_hostname", unit, rid)) for unit in related_units(rid))
             if hostname ]
    return ctxs[0] if ctxs else {}


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
        Generated Config for all PLUMgrid templates inside the
        templates folder.
        '''
        pg_ctxt = super(NeutronPGPluginContext, self).pg_ctxt()
        if not pg_ctxt:
            return {}

        conf = config()
        enable_metadata = conf['enable-metadata']
        # (TODO) get this information from director
        pg_ctxt['pg_username'] = conf['plumgrid-username']
        pg_ctxt['pg_password'] = conf['plumgrid-password']
        pg_ctxt['virtual_ip'] = conf['plumgrid-virtual-ip']
        pg_ctxt['enable_metadata'] = enable_metadata
        pg_ctxt['pg_metadata_ip'] = '169.254.169.254'
        pg_ctxt['pg_metadata_port'] = '8775'
        pg_ctxt['metadata_mode'] = 'tunnel'
        if enable_metadata:
            plumgrid_edge_settings = _edge_settings()
            pg_ctxt['nova_metadata_proxy_secret'] = \
                plumgrid_edge_settings['metadata_shared_secret']
        else:
            pg_ctxt['nova_metadata_proxy_secret'] = 'plumgrid'
        if relation_get("service_hostname"):
            identity_context = _identity_context()
            pg_ctxt['admin_user'] = identity_context['admin_user']
            pg_ctxt['admin_password'] = identity_context['admin_password']
            pg_ctxt['admin_tenant_name'] = identity_context['admin_tenant_name']
            pg_ctxt['service_protocol'] = identity_context['service_protocol']
            pg_ctxt['auth_port'] = identity_context['auth_port']
            pg_ctxt['auth_host'] = identity_context['auth_host']
            print pg_ctxt

        return pg_ctxt
