#!/usr/bin/python

# Copyright (c) 2015, PLUMgrid Inc, http://plumgrid.com

# The hooks of this charm have been symlinked to functions
# in this file.

import sys

from charmhelpers.core.hookenv import (
    Hooks,
    UnregisteredHookError,
    log,
    config,
)

from charmhelpers.core.host import (
    restart_on_change,
    service_restart
)

from charmhelpers.fetch import (
    apt_install,
    apt_update,
    configure_sources,
)

from neutron_plumgrid_utils import (
    determine_packages,
    register_configs,
    restart_map,
    ensure_files,
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
@restart_on_change(restart_map())
def config_changed():
    '''
    This hook is run when a config parameter is changed.
    It also runs on node reboot.
    '''
    charm_config = config()
    if (charm_config.changed('install_sources') or
        charm_config.changed('plumgrid-build') or
            charm_config.changed('install_keys')):
        configure_sources()
        apt_update()
        pkgs = determine_packages()
        for pkg in pkgs:
            apt_install(pkg, options=['--force-yes'], fatal=True)
        service_restart('neutron-server')
    if charm_config.changed('networking-plumgrid-version'):
        ensure_files()
        service_restart('neutron-server')
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


@hooks.hook('stop')
def stop():
    '''
    This hook is run when the charm is destroyed.
    '''
    log('Charm stopping without removal of packages')


def main():
    try:
        hooks.execute(sys.argv)
    except UnregisteredHookError as e:
        log('Unknown hook {} - skipping.'.format(e))


if __name__ == '__main__':
    main()
