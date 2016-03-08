#!/usr/bin/python

# Copyright (c) 2015, PLUMgrid Inc, http://plumgrid.com

# The hooks of this charm have been symlinked to functions
# in this file.

import sys
from charmhelpers.contrib.python.packages import pip_uninstall

from charmhelpers.core.hookenv import (
    Hooks,
    UnregisteredHookError,
    log,\
    relation_get
)

from charmhelpers.core.host import (
    restart_on_change,
)

from charmhelpers.fetch import (
    apt_install,
    apt_update,
    configure_sources,
    apt_purge,
)

from neutron_plumgrid_utils import (
    determine_packages,
    register_configs,
    restart_map,
    ensure_files,
    set_neutron_relation,
)

hooks = Hooks()
CONFIGS = register_configs()


@hooks.hook()
def install():
    '''
    Install hook is run when the charm is first deployed on a node.
    '''
    configure_sources()
    apt_update()
    pkgs = determine_packages()
    for pkg in pkgs:
        apt_install(pkg, options=['--force-yes'], fatal=True)
    ensure_files()


@hooks.hook('config-changed')
def config_changed():
    '''
    This hook is run when a config parameter is changed.
    It also runs on node reboot.
    '''
    stop()
    configure_sources()
    apt_update()
    pkgs = determine_packages()
    for pkg in pkgs:
        apt_install(pkg, options=['--force-yes'], fatal=True)
    ensure_files()
    CONFIGS.write_all()


@hooks.hook('neutron-plugin-api-relation-joined')
@hooks.hook('plumgrid-plugin-relation-changed')
@hooks.hook('container-relation-changed')
@restart_on_change(restart_map())
def relation_changed():
    '''
    This hook is run when relation between neutron-api-plumgrid and
    neutron-api or plumgrid-edge is made.
    '''
    ensure_files()
    CONFIGS.write_all()


@hooks.hook("neutron-plugin-api-subordinate-relation-joined")
def neutron_plugin_joined():
    set_neutron_relation()


@hooks.hook("identity-admin-relation-changed")
@hooks.hook("identity-admin-relation-departed")
@hooks.hook("identity-admin-relation-broken")
@restart_on_change(restart_map())
def identity_admin_relation():
    CONFIGS.write_all()


@hooks.hook('stop')
def stop():
    '''
    This hook is run when the charm is destroyed.
    '''
    print "exiting"
    #pkgs = determine_packages()
    #for pkg in pkgs:
    #    apt_purge(pkg, fatal=False)
    #pip_uninstall('networking-plumgrid')


def main():
    try:
        hooks.execute(sys.argv)
    except UnregisteredHookError as e:
        log('Unknown hook {} - skipping.'.format(e))


if __name__ == '__main__':
    main()
