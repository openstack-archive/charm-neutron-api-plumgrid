# Overview

This charm enables PLUMgrid Neutron plugin in an OpenStack environment.

Once deployed, the charm enables the necessary actions in the neutron-server container that allows the PLUMgrid plugin to take over networking for the OpenStack environment.

It is a subordinate charm to neutron-api charm.

# Usage

Instructions on using the charm:

    juju deploy neutron-api
    juju deploy neutron-api-plumgrid
    juju add-relation neutron-api neutron-api-plumgrid

To enable PLUMgrid in neutron make the configuration in the neutron-api charm as specified in the configuration section below.

# Known Limitations and Issues

The charm currently only supports Kilo Openstack Release.

# Configuration

Example Config

    neutron-api-plumgrid:
        install_sources: 'ppa:plumgrid-team/stable'
        install_keys: 'null'
        enable-metadata: False
    neutron-api:
        neutron-plugin: "plumgrid"
        plumgrid-virtual-ip: "192.168.100.250"

Provide the source repo path for PLUMgrid Debs in 'install_sources' and the corresponding keys in 'install_keys'
The "neutron-plugin" config parameter is required to be "plumgrid" in the neutron-api charm to enable PLUMgrid.
Also the virtual IP on which PLUMgrid Console is going to be accessible should be specified in the "plumgrid-virtual-ip" config parameter.

# Contact Information

Bilal Baqar <bbaqar@plumgrid.com>
Bilal Ahmad <bilal@plumgrid.com>
