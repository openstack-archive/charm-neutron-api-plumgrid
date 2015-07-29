# Copyright (c) 2015, PLUMgrid Inc, http://plumgrid.com

# This file contains functions used by the hooks to enable PLUMgrid
# in Openstack.

from collections import OrderedDict
from copy import deepcopy
import os
from charmhelpers.contrib.openstack import templating
from charmhelpers.contrib.python.packages import pip_install

from charmhelpers.contrib.openstack.utils import (
    os_release,
)

import neutron_plumgrid_context

TEMPLATES = 'templates/'

PG_PACKAGES = [
    'plumgrid-pythonlib',
]

NEUTRON_CONF_DIR = "/etc/neutron"

SU_FILE = '/etc/sudoers.d/neutron_sudoers'
PGLIB_CONF = '%s/plugins/plumgrid/plumlib.ini' % NEUTRON_CONF_DIR

BASE_RESOURCE_MAP = OrderedDict([
    (SU_FILE, {
        'services': [],
        'contexts': [neutron_plumgrid_context.NeutronPGPluginContext()],
    }),
    (PGLIB_CONF, {
        'services': ['neutron-server'],
        'contexts': [neutron_plumgrid_context.NeutronPGPluginContext()],
    }),
])


def determine_packages():
    '''
    Returns list of packages required to be installed alongside neutron to
    enable PLUMgrid in Openstack.
    '''
    return list(set(PG_PACKAGES))


def resource_map():
    '''
    Dynamically generate a map of resources that will be managed for a single
    hook execution.
    '''
    resource_map = deepcopy(BASE_RESOURCE_MAP)
    return resource_map


def register_configs(release=None):
    '''
    Returns an object of the Openstack Tempating Class which contains the
    the context required for all templates of this charm.
    '''
    release = release or os_release('neutron-server', base='kilo')
    configs = templating.OSConfigRenderer(templates_dir=TEMPLATES,
                                          openstack_release=release)
    for cfg, rscs in resource_map().iteritems():
        configs.register(cfg, rscs['contexts'])
    return configs


def restart_map():
    '''
    Constructs a restart map based on charm config settings and relation
    state.
    '''
    return OrderedDict([(cfg, v['services'])
                        for cfg, v in resource_map().iteritems()
                        if v['services']])


def ensure_files():
    '''
    Ensures PLUMgrid specific files exist before templates are written.
    '''
    pip_install('networking-plumgrid', fatal=True)
    os.chmod('/etc/sudoers.d/neutron_sudoers', 0o440)
