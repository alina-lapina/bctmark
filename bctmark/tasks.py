from enoslib.api import play_on, generate_inventory, run_ansible, discover_networks
from enoslib.task import enostask
from enoslib.infra.enos_vagrant.configuration import Configuration as Vagrant_Configuration
from enoslib.infra.enos_g5k.configuration import Configuration as G5K_Configuration
from enoslib.infra.enos_static.configuration import Configuration as Static_Configuration
from enoslib.infra.enos_g5k.provider import G5k
from enoslib.infra.enos_vagrant.provider import Enos_vagrant
from enoslib.infra.enos_static.provider import Static
from enoslib.service import Netem, Locust

from .services import Hyperledger, EthGethClique, EthGethCliqueArm7, BCTMarkLocust, ReplayManager, BCTMarkWorker, Monitoring
from .utils import print_ex_time
import logging
import os
import yaml
from bctmark.constants import ANSIBLE_DIR

logger = logging.getLogger(__name__)
CURRENT_PATH = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))


@enostask(new=True)
@print_ex_time
def g5k(config, force, env=None, **kwargs):
    provider = G5k(G5K_Configuration.from_dictionnary(config["deployment"]["g5k"]))
    roles, networks = provider.init(force_deploy=force)
    roles = discover_networks(roles, networks)
    env["config"] = config
    env["roles"] = roles
    env["networks"] = networks


@enostask(new=True)
@print_ex_time
def vagrant(config, force, env=None, **kwargs):
    provider = Enos_vagrant(Vagrant_Configuration.from_dictionnary(config["deployment"]["vagrant"]))
    roles, networks = provider.init(force_deploy=force)
    roles = discover_networks(roles, networks)
    env["config"] = config
    env["roles"] = roles
    env["networks"] = networks

@enostask(new=True)
@print_ex_time
def static(config, force, env=None, **kwargs):
    provider = Static(Static_Configuration.from_dictionnary(config["deployment"]["static"]))
    roles, networks = provider.init(force_deploy=force)
    roles = discover_networks(roles, networks)
    env["config"] = config
    env["roles"] = roles
    env["networks"] = networks

@enostask()
@print_ex_time
def emulate(config, **kwargs):
    env = kwargs["env"]
    constraints = config["network-constraints"]
    roles = env["roles"]
    netem = Netem(constraints, roles=roles)
    netem.deploy()
    netem.validate()


@enostask()
@print_ex_time
def inventory(**kwargs):
    env = kwargs["env"]
    roles = env["roles"]
    networks = env["networks"]
    env["inventory"] = os.path.join(env["resultdir"], "hosts")
    generate_inventory(roles, networks, env["inventory"], check_networks=True)


@enostask()
@print_ex_time
def prepare(**kwargs):
    env = kwargs["env"]
    roles = env["roles"]

    if "dashboard" in roles:
        telegraf_conf = ""
        telegraf_agents = []
        if any("ethgethcliquearm7" in r for r in roles):
            s = EthGethCliqueArm7(
                bootnodes=roles["ethgethcliquearm7_bootnode"],
                peers=roles["ethgethcliquearm7_peer"],
                dashboard=roles["dashboard"]
            )
            telegraf_conf = os.path.join(CURRENT_PATH, 'services', 'eth_geth_clique_arm7', 'eth_geth_clique', 'roles',
                                         'eth_geth_clique', 'templates', 'telegraf.conf.j2')
            telegraf_agents = roles["ethgethcliquearm7_bootnode"] + roles["ethgethcliquearm7_peer"]
        elif any("ethgethclique" in r for r in roles):
            s = EthGethClique(
                bootnodes=roles["ethgethclique_bootnode"],
                peers=roles["ethgethclique_peer"],
                dashboard=roles["dashboard"]
            )
            telegraf_conf = os.path.join(CURRENT_PATH, 'services', 'eth_geth_clique', 'eth_geth_clique', 'roles',
                                         'eth_geth_clique', 'templates', 'telegraf.conf.j2')
            telegraf_agents = roles["ethgethclique_bootnode"] + roles["ethgethclique_peer"]
        elif any("hyperledger" in r for r in roles):
            s = Hyperledger(
                orderers=roles["hyperledger_orderer"],
                peers=roles["hyperledger_peer"]
            )
            telegraf_conf = os.path.join(CURRENT_PATH, 'services', 'hyperledger',
                                         'templates', 'telegraf.conf.j2')
            telegraf_agents = roles["hyperledger_orderer"] + roles["hyperledger_peer"]

        m = Monitoring(collector=roles["dashboard"],
                       ui=roles["dashboard"],
                       agent=telegraf_agents,
                       network='ntw_monitoring',
                       agent_conf=telegraf_conf)

        m.deploy()
        m.create_database('geth')
        ui_address = roles["dashboard"][0].extra["%s_ip" % m.network]

        print("GRAFANA : The Grafana UI is available at http://%s:3000" % ui_address)
        print("GRAFANA : user=admin, password=admin")
    else:
        if any("ethgethcliquearm7" in r for r in roles):
            s = EthGethCliqueArm7(
                bootnodes=roles["ethgethcliquearm7_bootnode"],
                peers=roles["ethgethcliquearm7_peer"]
            )
        elif any("ethgethclique" in r for r in roles):
            s = EthGethClique(
                bootnodes=roles["ethgethclique_bootnode"],
                peers=roles["ethgethclique_peer"]
            )
        elif any("hyperledger" in r for r in roles):
            s = Hyperledger(
                orderers=roles["hyperledger_orderer"],
                peers=roles["hyperledger_peer"]
            )
        print("No monitoring activated")

    if "bench_worker" in roles:
        s.peers += roles["bench_worker"]
        b = BCTMarkWorker(roles["bench_worker"])
        b.deploy()

    s.deploy()


@enostask()
@print_ex_time
def backup(env):
    roles = env["roles"]
    telegraf_agents = []

    if any("ethgethclique" in r for r in roles):
        s = EthGethClique(
            bootnodes=roles["ethgethclique_bootnode"],
            peers=roles["ethgethclique_peer"]
        )
        s.backup()

    if "dashboard" in roles:
        m = Monitoring(collector=roles["dashboard"],
                       ui=roles["dashboard"],
                       agent=telegraf_agents,
                       network='ntw_monitoring')
        m.backup()


@enostask()
@print_ex_time
def destroy(**kwargs):
    env = kwargs["env"]
    roles = env["roles"]

    telegraf_agents = []

    if any("hyperledger" in r for r in roles):
        s = Hyperledger(
            orderers=roles["hyperledger_orderer"],
            peers=roles["hyperledger_peer"]
        )
        s.destroy()
        telegraf_agents = roles["hyperledger_orderer"] + roles["hyperledger_peer"]
    if any("ethgethclique" in r for r in roles):
        s = EthGethClique(
            bootnodes=roles["ethgethclique_bootnode"],
            peers=roles["ethgethclique_peer"]
        )
        s.destroy()
    if "dashboard" in roles:
        m = Monitoring(collector=roles["dashboard"],
                       ui=roles["dashboard"],
                       agent=telegraf_agents,
                       network='ntw_monitoring')
        m.destroy()


def _deploy_locust(roles):
    locust = Locust(master=roles["dashboard"],
                    agents=roles["bench_worker"],
                    network="ntw_monitoring")
    locust.deploy()
    return locust

@enostask()
@print_ex_time
def benchmark(experiment_directory, main_file, env):
    roles = env["roles"]

    locust = _deploy_locust(roles)

    target_lists = {r: ';'.join(map(lambda x: x.extra["ntw_monitoring_ip"], l)) for r, l in roles.items()}
    print(target_lists)
    locust.run_with_ui(
        expe_dir=experiment_directory,
        locustfile=main_file,
        environment=target_lists)
    ui_address = roles["dashboard"][0].extra["ntw_monitoring_ip"]
    print("LOCUST : The Locust UI is available at http://%s:8089" % ui_address)


@enostask()
@print_ex_time
def benchmark_headless(experiment_directory, main_file, nb_clients, hatch_rate, run_time, density, env):
    roles = env["roles"]

    locust = _deploy_locust(roles)

    target_lists = {r: ';'.join(map(lambda x: x.extra["ntw_monitoring_ip"], l)) for r, l in roles.items()}
    print(target_lists)
    locust.run_headless(
        expe_dir=experiment_directory,
        locustfile=main_file,
        environment=target_lists,
        nb_clients=nb_clients,
        hatch_rate=hatch_rate,
        run_time=run_time,
        density=density
    )


@enostask()
@print_ex_time
def replay(transactions_file, env):
    roles = env["roles"]
    networks = env["networks"]

    if "bench_worker" in roles:
        peers = roles["ethgethclique_peer"] + roles["bench_worker"]
    else:
        peers = roles["ethgethclique_peer"]

    e = EthGethClique(bootnodes=roles["ethgethclique_bootnode"], peers=peers)
    b = BCTMarkWorker(roles["bench_worker"])
    r = ReplayManager(b, transactions_file, e)
    r.replay_transactions()


@enostask()
@print_ex_time
def debug(var, env):
    roles = env["roles"]
    with play_on(pattern_hosts="all", roles=roles) as p:
        p.debug(var=var)


@enostask()
def status(env, role_asked):
    def print_hosts(role):
        for host in list(set(roles[role])):
            print(f"# {host.alias}")
            print(yaml.dump(host.extra, default_flow_style=False))
    roles = env["roles"]
    print("STATUS")

    if role_asked is not None:
        if role_asked in roles:
            print_hosts(role_asked)
        else:
            print(f"Role '{role_asked}' is unknown. Known roles: {list(set(roles.keys()))}")
    else:
        for role in list(set(roles.keys())):
            print("+----------------------+")
            print(f"{role}:")
            print_hosts(role)


PROVIDERS = {
    "g5k": g5k,
    "vagrant": vagrant,
    "static": static,
    #    "chameleon": chameleon
}
