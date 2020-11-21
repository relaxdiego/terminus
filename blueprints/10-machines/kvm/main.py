from pyinfra import host

netplan_path = host.fact.find_files('/etc/netplan/*.y*ml')[0]
print(host.data.gateway)
print(host.data.ip_address)
