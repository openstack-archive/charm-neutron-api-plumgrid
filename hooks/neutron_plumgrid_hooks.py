#!/usr/bin/python

# Copyright (c) 2015, PLUMgrid Inc, http://plumgrid.com

# The hooks of this charm have been symlinked to functions
# in this file.

import sys

from charmhelpers.core.hookenv import (
    Hooks,
    UnregisteredHookError,
    log,
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
    apt_install(determine_packages(), options=['--force-yes'], fatal=True)
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
    apt_install(determine_packages(), options=['--force-yes'], fatal=True)
    ensure_files()
    CONFIGS.write_all()


@hooks.hook('neutron-plugin-api-relation-joined')
def neutron_plugin_api_joined():
    '''
    This hook is run when relation between neutron-api and
    neutron-api-plumgrid is made.
    '''
    ensure_files()
    CONFIGS.write_all()


@hooks.hook('container-relation-changed')
@restart_on_change(restart_map())
def container_changed():
    '''
    This hook is run when relation between neutron-api and
    neutron-api-plumgrid is changed.
    '''
    ensure_files()
    CONFIGS.write_all()


@hooks.hook('stop')
def stop():
    '''
    This hook is run when the charm is destroyed.
    '''
    pkgs = determine_packages()
    for pkg in pkgs:
        apt_purge(pkg, fatal=False)


@hooks.hook('start')
def start():
    '''
    This hook is run after all relations are joined.
    '''
    ensure_files()


def main():
    try:
        hooks.execute(sys.argv)
    except UnregisteredHookError as e:
        log('Unknown hook {} - skipping.'.format(e))


if __name__ == '__main__':
    main()
