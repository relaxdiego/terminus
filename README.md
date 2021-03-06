> Terminus is a planet in Isaac Asimov's Foundation series. It is the
> capital planet of the First Foundation. It is located at the edge of
> the Galaxy. --[Asimov Fandom Page](https://asimov.fandom.com/wiki/Terminus)


Terminus
========

This repo documents the steps that I took to implement a test bed for exploring
[Metal-as-a-Service](https://maas.io/) (MAAS) in HA mode. The overall design is illustrated in
[this diagram](https://docs.google.com/drawings/d/1IYXyQ_sG0gMksttrtztyzmbRIbm7ZwDBmN6bXXkeS-Y/edit).

The objective here is to have a workable environment using just spare hardware
in my home office. Thus, this environment is built more for exploration, rather
than performance and reliability. In other words, don't depend on this design
for production, folks!


Install Ubuntu on the Baremetals
--------------------------------

Install Ubuntu Server LTS on all baremetals and configure them with static
IPs as indicated in the logical network diagram above. We use static IPs here
because MAAS, which will be the DHCP (and PXE) server, is not yet set up in
the network.


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

What we just did is create a Linux bridge (think of it as a software-defined L2
switch on steroids) that's connected to the underlying L2 network. This will
allow us to instantiate VMs and connect them to this bridge thereby making them
visible to all machines in the underlying L2 network.

> Note that we have not configured VLANs at this point. We will do that once
> all baremetal and virtual machines have been set up and verified to ping each
> other on the `192.168.100.x` subnet.


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
sudo systemctl restart systemd-networkd
virsh net-undefine default
virsh net-list --all
brctl show
ip a
```


Instantiate the Infra VMs
-------------------------

Copy the [Ubuntu 20.04](https://releases.ubuntu.com/20.04/ubuntu-20.04.1-live-server-amd64.iso)
(or [18.04](https://releases.ubuntu.com/18.04/ubuntu-18.04.5-live-server-amd64.iso))
iso to the baremetal machines.

We will need another CLI tool to easily create a VM on KVM. Install:

```
sudo apt install virtinst
```

Then:

```
for i in $(seq 1 3); do
    virt-install \
        --name=infra-$i \
        --vcpus=2 \
        --memory=6144 \
        --disk size=64 \
        --cdrom=ubuntu-18.04.5-live-server-amd64.iso \
        --os-variant=ubuntu18.04 \
        --graphics vnc,listen=0.0.0.0 --noautoconsole
done
```

Note that `--memory` uses `MiB` as units and `--disk` uses `GiB`

To get the VNC port number that the above VMs are connected to, run:

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

Repeat the above steps for the config (configurator) VM.


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

Ensure Passwordless sudo
------------------------

This will save you a lot of typing down the line. Run the following
commands in all the machines (baremetals and VMs)

First, test that it does the write thing:

```
sudo sed -E 's/^(%sudo.*) ALL$/\1 NOPASSWD:ALL/g' /etc/sudoers
```

Then commit to it!

```
sudo sed -i -E 's/^(%sudo.*) ALL$/\1 NOPASSWD:ALL/g' /etc/sudoers
```


Setting up VLANs
----------------

At this point, your baremetal and virtual machines should be able to ping each
other on the `192.168.100.x` subnet. If that's not the case, double check your
netplan config for all baremetal and virtual machines before proceeding.

As per [this blog](https://web.archive.org/web/20200211182440/http://blog.davidvassallo.me/2012/05/05/kvm-brctl-in-linux-bringing-vlans-to-the-guests/),
if we want to have our infra nodes be VLAN-aware, we must first make sure our
baremetal hosts are aware of the VLAN. It's also important to define and attach
our VLANs to `br0` rather than the baremetal host's physical interface, otherwise
the packets will be untagged before they even reach `br0`. Thus, make sure to
append the following to your baremetal host's `/etc/netplan/xxxxxxx.yaml` file:

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

Change the last octets above to match the baremetal's last octet in the
`192.168.100.x` subnet. Save the netplan file and then run:

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

Change the last octets above to match the virtual machine's last octet
in the `192.168.100.x` subnet.

Note how we link the VLAN to the interface that's connected to `br0`. Save
the updated configuration and then run:

```
sudo netplan --debug generate
sudo netplan --debug apply
```

Now all 6 machines (baremetal and virtual) should be able to ping each
other on all 4 subnets.


Prepare a Local Image Mirror
----------------------------

If you plan on re-installing MAAS multiple times (as one does in a
lab environment), consider setting up a local image mirror in kvm-1
so that your image syncs go faster. The following steps is adapted
from [this guide](https://maas.io/docs/local-image-mirror#heading--set-up-local-mirror).

```
ssh kvm-1
sudo apt install simplestreams
KEYRING_FILE=/usr/share/keyrings/ubuntu-cloudimage-keyring.gpg
IMAGE_SRC=https://images.maas.io/ephemeral-v3/stable
IMAGE_DIR=/var/www/html/maas/images/ephemeral-v3/stable
```

`KEYRING_FILE` points to the GPG keyring file that `sstream-mirror` will
use to verify the integrity of the downloaded images.


```
sudo sstream-mirror --keyring=$KEYRING_FILE $IMAGE_SRC $IMAGE_DIR \
    'arch=amd64' 'release~(bionic|focal)' --max=1 --progress
sudo sstream-mirror --keyring=$KEYRING_FILE $IMAGE_SRC $IMAGE_DIR \
    'os~(grub*|pxelinux)' --max=1 --progress
```

The last two commands above will take some time depending on your bandwidth.

Once the initial sync has completed, run a simple HTTP server using Python:

```
cd /var/www/html
python3 -m http.server 3003
```

Then from each of the infra nodes, run:

```
curl http://192.168.100.11:3003/maas/images/ephemeral-v3/stable/
```

You should see something like:

```
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<title>Directory listing for /maas/images/ephemeral-v3/stable/</title>
</head>
<body>
<h1>Directory listing for /maas/images/ephemeral-v3/stable/</h1>
<hr>
<ul>
<li><a href=".data/">.data/</a></li>
<li><a href="bionic/">bionic/</a></li>
<li><a href="focal/">focal/</a></li>
<li><a href="streams/">streams/</a></li>
</ul>
<hr>
</body>
</html>
```

Now let's make the HTTP server permanent via a systemd service. Write the
following in `/etc/systemd/system/maas-local-image-mirror.service`:

```
[Unit]
Description=Dumb HTTP server for MAAS local image mirror
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
Restart=always
RestartSec=3
User=ubuntu
WorkingDirectory=/var/www/html
ExecStart=/usr/bin/env python3 -m http.server 3003

[Install]
WantedBy=multi-user.target
```

Then enable and start it:

```
sudo systemctl daemon-reload
sudo systemctl enable maas-local-image-mirror
sudo systemctl start maas-local-image-mirror
```

You should now have a local image mirror that MAAS can connect to via
`http://192.168.100.11:3003/maas/images/ephemeral-v3/stable/`

Optionally keep your local mirror in-sync by running the above `sstream-mirror`
commands using a cronjob or a systemd timer.


Starting Over
-------------

Want to stand up a new MAAS cluster or you just messed up and need to
start over? Or maybe you want to try out a different version of MAAS?
No problem.

First, check which VMs are running in the baremetal:

```
virsh list --all
```

Next destroy and undefine each VM:

```
for i in $(seq 1 3); do
    virsh destroy infra-$i
    virsh undefine infra-$i
    virsh vol-delete infra-$i.qcow2 --pool=default
done
```

Now re-create the VMs as stated above



References
----------

* [libvirt](https://ubuntu.com/server/docs/virtualization-libvirt)
* [netplan](https://netplan.io/)
