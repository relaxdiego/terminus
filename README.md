> Terminus is a planet in Isaac Asimov's Foundation series. It is the
> capital planet of the First Foundation. It is located at the edge of
> the Galaxy. --[Asimov Fandom Page](https://asimov.fandom.com/wiki/Terminus)

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

> NOTE: We can't use `netplan try` here since we are defining a bridge and
> reverting that config isn't supported. In that case, make sure you got
> everything right or you'll have to walk over to the machine and fix it via
> its console! Optionally, if you have a second ethernet or maybe even a
> WiFi interface, keep that on. That's outside the scope of this guide though.

What we just did is create a host bridge (really a software-defined L2
switch) that's connected to the underlying L2 network. This will allow us
to instantiate VMs and connect them to this bridge thereby making them visible
to all machines in the underlying L2 network.


Install libvirt and Friends
---------------------------

To manage KVM, we will use libvirt as our main management interface. Let's
install it now:

```
sudo apt update
sudo apt install qemu-kvm libvirt-daemon-system
```

Log out and log back in to ensure that your membership to the libvirt
group is in effect.

The above installation will automatically create `virbr0` for us but we want
to use `br0` instead. Let's remove `virbr0` and make `br0` the default.

```
virsh net-destroy default
virsh net-edit default
```

Update the contents to:

```
<network>
  <name>br0</name>
  <forward mode='bridge'/>
  <bridge name='br0'/>
</network>
```

```
virsh net-start br0
systemctl restart systemd-networkd
virsh net-undefine default
virsh net-list --all
brctl show
ip a
```


Instantiate the MAAS VMs
------------------------

Copy the [Ubuntu 20.04 iso](https://releases.ubuntu.com/20.04/ubuntu-20.04.1-live-server-amd64.iso)
to the baremetal machine that will host the MAAS VMs. Make sure to locate it
in a directory that's accessible to KVM services. Preferably `/opt/terminus/`.

We will need another CLI tool to easily create a VM on KVM. Install:

```
sudo apt install virtinst
```

Then:

```
virt-install \
    --name=maas1 \
    --vcpus=2 \
    --memory=6144 \
    --disk size=40 \
    --cdrom=/opt/terminus/ubuntu-20.04-live-server-amd64.iso \
    --os-variant=ubuntu18.04 \
    --graphics vnc,listen=0.0.0.0 --noautoconsole
```

Note that `--memory` uses `MiB` as units and `--disk` uses `GiB`

To get the VNC port number that the above VM is connected to, run:

```
virsh vncdisplay maas1
```

You may need to run `sshuttle` in your localhost if the baremetals
are accessible via a jumpbox:

```
sshuttle -v -H -r <jumpbox-hostname-or-ip> 192.168.100.0/24
```

Now run your VNC viewer and point it to `<baremetal-ip>:<vnc-port>` to
continue with the installation process.

Remember that MAAS VMs must have static IPs in the 192.168.100.51/24
to .53 range

Once Ubuntu has finished installation, the VM will shutdown. To start
it and make it autostart when the baremetal machine boots up, run:

```
virsh autostart maas1
virsh start maas1
```


References
----------

* [libvirt](https://ubuntu.com/server/docs/virtualization-libvirt)
* [netplan](https://netplan.io/)
