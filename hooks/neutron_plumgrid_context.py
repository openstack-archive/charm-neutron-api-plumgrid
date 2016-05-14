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


def _edge_context():
    '''
    Inspects plumgrid-plugin relation to get metadata shared secret.
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


def _plumgrid_context():
    '''
    Inspects plumgrid-configs relation to get plumgrid virtual ip,
    username and password.
    '''
    ctxt = {}
    for rid in relation_ids('plumgrid-configs'):
        for unit in related_units(rid):
            rdata = relation_get(rid=rid, unit=unit)
            if 'plumgrid_virtual_ip' in rdata:
                ctxt['plumgrid_virtual_ip'] = \
                    rdata['plumgrid_virtual_ip']
                ctxt['plumgrid_username'] = \
                    rdata['plumgrid_username']
                ctxt['plumgrid_password'] = \
                    rdata['plumgrid_password']
    return ctxt


def _identity_context():
    '''
    Inspects identity-admin relation to get keystone credentials.
    '''
    ctxs = [{
        'auth_host': gethostbyname(hostname),
        'auth_port': relation_get('service_port', unit, rid),
        'admin_user': relation_get('service_username', unit, rid),
        'admin_password': relation_get('service_password', unit, rid),
        'service_protocol': relation_get('auth_protocol', unit, rid) or 'http',
        'admin_tenant_name': relation_get('service_tenant_name', unit,
                                          rid),
    } for rid in relation_ids('identity-admin') for (unit, hostname) in
        ((unit, relation_get('service_hostname', unit, rid))
            for unit in related_units(rid)) if hostname]
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
        pg_ctxt['hardware_vendor_name'] = config('hardware-vendor-name')
        pg_ctxt['switch_username'] = config('switch-username')
        pg_ctxt['switch_password'] = config('switch-password')
        pg_ctxt['enable_metadata'] = enable_metadata
        pg_ctxt['pg_metadata_ip'] = '169.254.169.254'
        pg_ctxt['pg_metadata_subnet'] = '169.254.169.254/30'
        pg_ctxt['pg_metadata_port'] = '8775'
        pg_ctxt['metadata_mode'] = 'tunnel'
        pg_ctxt['connector_type'] = config('connector-type')
        if enable_metadata:
            plumgrid_edge_ctxt = _edge_context()
            pg_ctxt['nova_metadata_proxy_secret'] = \
                plumgrid_edge_ctxt['metadata_shared_secret']
        else:
            pg_ctxt['nova_metadata_proxy_secret'] = 'plumgrid'
        identity_context = _identity_context()
        if identity_context:
            pg_ctxt['admin_user'] = identity_context['admin_user']
            pg_ctxt['admin_password'] = identity_context['admin_password']
            pg_ctxt['admin_tenant_name'] = \
                identity_context['admin_tenant_name']
            pg_ctxt['service_protocol'] = identity_context['service_protocol']
            pg_ctxt['auth_port'] = identity_context['auth_port']
            pg_ctxt['auth_host'] = identity_context['auth_host']
        plumgrid_context = _plumgrid_context()
        if plumgrid_context:
            pg_ctxt['pg_username'] = plumgrid_context['plumgrid_username']
            pg_ctxt['pg_password'] = plumgrid_context['plumgrid_password']
            pg_ctxt['virtual_ip'] = plumgrid_context['plumgrid_virtual_ip']
            print pg_ctxt
        return pg_ctxt
