> Terminus is a planet in Isaac Asimov's Foundation series. It is the
> capital planet of the First Foundation. It is located at the edge of
> the Galaxy. --[Asimov Fandom Page](https://asimov.fandom.com/wiki/Terminus)


Terminus v2
===========

These are notes that I'm writing specifically for myself so that I don't
forget how to set up a test HA MAAS environment using what little baremetal
machines may be available. The logical network design this README is based
on may be found [here](https://docs.google.com/drawings/d/1IYXyQ_sG0gMksttrtztyzmbRIbm7ZwDBmN6bXXkeS-Y/edit).


Install Ubuntu on the Baremetals
--------------------------------

Install Ubuntu Server LTS on all baremetals and configure them with
static IPs as indicated in the logical network diagram above. We use
static IPs here because MAAS, which serves as the DHCP server, is not
yet set up in the Lab Net.


Baremetal Network Config
------------------------

For each baremetal KVM host, create a backup of its `/etc/netplan/xxxxxxxxx.yaml`
file and then edit it like so:

```
network:
  version: 2
  ethernets:
    <interface-name-here>:
      dhcp4: false
      dhcp6: false

  bridges:
    br0:
      interfaces:
      - <interface-name-here>
      addresses:
      - 192.168.100.XX/24
      gateway4: 192.168.100.1
      nameservers:
        addresses:
        - 1.1.1.1
        - 8.8.8.8
        - 8.8.4.4
      dhcp4: false
      dhcp6: false
      parameters:
        forward-delay: 4
        stp:           true
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

Note that we have not configured VLANs at this point. We will do that once
all baremetal and virtual machines have been set up and verified to ping each
other on the `192.168.100.x` subnet.


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
sudo-systemctl restart systemd-networkd
virsh net-undefine default
virsh net-list --all
brctl show
ip a
```


Instantiate the Infra VMs
-------------------------

Copy the [Ubuntu 20.04](https://releases.ubuntu.com/20.04/ubuntu-20.04.1-live-server-amd64.iso)
(or [18.04](https://releases.ubuntu.com/18.04/ubuntu-18.04.5-live-server-amd64.iso))
iso to the baremetal machine that will serve as the infra machines.

We will need another CLI tool to easily create a VM on KVM. Install:

```
sudo apt install virtinst
```

Then:

```
virt-install \
    --name=infra-1 \
    --vcpus=2 \
    --memory=6144 \
    --disk size=40 \
    --cdrom=ubuntu-18.04.5-live-server-amd64.iso \
    --os-variant=ubuntu18.04 \
    --graphics vnc,listen=0.0.0.0 --noautoconsole
```

Note that `--memory` uses `MiB` as units and `--disk` uses `GiB`

To get the VNC port number that the above VM is connected to, run:

```
virsh vncdisplay infra-1
```

You may need to run `sshuttle` in your localhost if the baremetals
are accessible via a jumpbox:

```
sshuttle -v -H -r <jumpbox-hostname-or-ip> 192.168.100.0/24
```

Now run your VNC viewer and point it to `<baremetal-ip>:<vnc-port>` to
continue with the installation process.

Make sure to assign the correct static IPs to the infra VMs as shown
in Level 1 of the logical network diagram.

Once Ubuntu has finished installation, the VM will shutdown. To start
it and make it autostart when the baremetal machine boots up, run:

```
virsh autostart infra-1
virsh start infra-1
```

Repeat the above steps for:

1. infra-2
2. infra-3
3. configurator


Configure Your SSH to Use the Jumpbox
-------------------------------------

Ensure you have something like this in your local `~/.ssh/config`

```
Host terminus-jb
    ForwardAgent yes
    HostName 192.168.86.21
    User ubuntu

Host kvm-1
    ForwardAgent yes
    HostName 192.168.100.11
    User ubuntu
    ProxyCommand ssh -W %h:%p terminus-jb

Host kvm-2
    ForwardAgent yes
    HostName 192.168.100.12
    User ubuntu
    ProxyCommand ssh -W %h:%p terminus-jb

Host config
    ForwardAgent yes
    HostName 192.168.100.20
    User ubuntu
    ProxyCommand ssh -W %h:%p terminus-jb

Host infra-1
    ForwardAgent yes
    HostName 192.168.100.21
    User ubuntu
    ProxyCommand ssh -W %h:%p terminus-jb

Host infra-2
    ForwardAgent yes
    HostName 192.168.100.22
    User ubuntu
    ProxyCommand ssh -W %h:%p terminus-jb

Host infra-3
    ForwardAgent yes
    HostName 192.168.100.23
    User ubuntu
    ProxyCommand ssh -W %h:%p terminus-jb
```

Create an entry for each baremetal and virtual machine that we connect
to the `192.168.100.x` network so that it's easier to ssh to them.


Setting up VLANs
----------------

At this point, your baremetals should be able to ping each other on the
`192.168.100.x` subnet. Likewise, the baremetals and virtual machines should
also be able to ping each other on said subnet. If that's not the case,
double check your netplan config for all baremetal and virtual machines
before proceeding.

As per [this blog](https://web.archive.org/web/20200211182440/http://blog.davidvassallo.me/2012/05/05/kvm-brctl-in-linux-bringing-vlans-to-the-guests/),
if we want to have our infra nodes be VLAN-aware, we must first make sure our
baremetal hosts are aware of the VLAN. It's also important to define and attach
our VLANs to `br0` rather than the baremetal host's physical interface, otherwise
the packets will be untagged before they reach our infra nodes. Thus, make sure
to append the following to your baremetal host's `/etc/netplan/xxxxxxx.yaml` file:

```
  vlans:
    vlan10:
      id:        10
      addresses: [192.168.110.XX/24]
      link:      br0
    vlan11:
      id:        11
      addresses: [192.168.111.XX/24]
      link:      br0
    vlan12:
      id:        12
      addresses: [192.168.112.XX/24]
      link:      br0
```

Save the netplan file and then run:

```
sudo netplan --debug generate
sudo netplan --debug apply
```

Now the baremetal machines should be able to ping each other on all four
subnets that are indicated in our netplan config.

At this point, our baremetal machines are VLAN aware, but our infra nodes
have no idea of these yet. Let's add the following to their own netplan
config:

```
  vlans:
    vlan10:
      id:        10
      addresses: [192.168.110.XX/24]
      link:      <machine's-interface-name>
    vlan11:
      id:        11
      addresses: [192.168.111.XX/24]
      link:      <machine's-interface-name>
    vlan12:
      id:        12
      addresses: [192.168.112.XX/24]
      link:      <machine's-interface-name>
```

Note how we link the VLAN to the interface that's connected to br0. Save
the updated configuration and then run:

```
sudo netplan --debug generate
sudo netplan --debug apply
```

Now all 6 machines (baremetal and virtual) should be able to ping each
other on all 4 subnets.


Starting Over
-------------

Want to stand up a new MAAS cluster or you just messed up and need to
start over? Or maybe you want to try out a different version of MAAS?
No problem.

```
virsh list --all
for i in $(seq 1 3); do virsh destroy maas$i && virsh undefine maas$i; done
virsh destroy configurator && virsh undefine configurator
```

Now re-create the VMs as stated above



References
----------

* [libvirt](https://ubuntu.com/server/docs/virtualization-libvirt)
* [netplan](https://netplan.io/)
