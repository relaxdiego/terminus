from os import path

from pyinfra import host
from pyinfra.api import deploy, DeployError
from pyinfra.operations import files

@deploy('Prepare Host', data_defaults={})
def prepare_host(state, host):
    # netplan_path = host.fact.find_files('/etc/netplan/*.y*ml')[0]
    # print(host.data.ip_address)
    # print(host.data.gateway)
    # print(host.data.nameservers)
    files.template(
        name='Render netplan configuration',
        src=path.join(
            path.dirname(__file__), 'templates', 'netplan.yaml.j2'
        ),
        dest='/tmp/netplan.yaml',

        state=state,
        host=host,
    )
