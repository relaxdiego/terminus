Terminus Setup
==============

Install Ubuntu 20.04 on all baremetal machines. Give them all a static IP,
preferably in the range of 192.168.100.41 to .45. All baremetals get a static
IP so that we can connect to them during setup. The VMs that will host MAAS
will also get static IPs, preferably in the range of 192.168.100.51 to .53.
All other VMs will get their network config via the MAAS DHCP server.


Baremetal Network Config
------------------------

Create a backup of your `/etc/netplan/xxxxxxxxx.yaml` file and then edit
it like so:

```
network:
  version: 2
  ethernets:
    <your-ethernet-port-name-here>:
      dhcp4: false
      dhcp6: false
  bridges:
    br0:
      interfaces: [<your-ethernet-port-name-here>]
      addresses:  [<this-machine's-static-ip-address>/24]
      gateway4:   192.168.100.1
      mtu:        1500
      nameservers:
        addresses: [1.1.1.1,8.8.8.8]
      parameters:
        stp:           true
        forward-delay: 4
      dhcp4: false
      dhcp6: false
```

Then apply the changes:

```
sudo netplan --debug generate
sudo netplan --debug apply
```

NOTE: We can't use `netplan try` here since we are defining a bridge and
reverting that config isn't supported. In that case, make sure you got
everything right or you'll have to walk over to the machine and fix via
its console! Optionally, if you have a second ethernet or maybe even a
WiFi interface, keep that on. That's outside the scope of this guide though.
