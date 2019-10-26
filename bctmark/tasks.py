from enoslib.api import play_on, generate_inventory, run_ansible, discover_networks
from enoslib.task import enostask
from enoslib.infra.enos_vagrant.configuration import Configuration as Vagrant_Configuration
from enoslib.infra.enos_g5k.configuration import Configuration as G5K_Configuration
from enoslib.infra.enos_g5k.provider import G5k
from enoslib.infra.enos_vagrant.provider import Enos_vagrant
from enoslib.service import Netem
from .services import EthGethClique, BCTMark_Locust, ReplayManager, BCTMarkWorker, Monitoring
from .utils import print_ex_time
import logging
import os
from bctmark.constants import ANSIBLE_DIR

logger = logging.getLogger(__name__)


@enostask(new=True)
@print_ex_time
def g5k(config, force, env=None, **kwargs):
    provider = G5k(G5K_Configuration.from_dictionnary(config["deployment"]["g5k"]))
    roles, networks = provider.init(force_deploy=force)
    env["config"] = config
    env["roles"] = roles
    env["networks"] = networks


@enostask(new=True)
@print_ex_time
def vagrant(config, force, env=None, **kwargs):
    provider = Enos_vagrant(Vagrant_Configuration.from_dictionnary(config["deployment"]["vagrant"]))
    roles, networks = provider.init(force_deploy=force)
    discover_networks(roles, networks)
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
    networks = env["networks"]

    if "bench_worker" in roles:
        peers = roles["peer"] + roles["bench_worker"]
        b = BCTMarkWorker(roles["bench_worker"])
        b.deploy()
    else:
        peers = roles["peer"]

    # Switch everyone to python3...
    with play_on(pattern_hosts="all", roles=roles) as p:
        p.apt(
            display_name="[Preinstall] Installing python3-pip",
            name=["python3", "python-pip", "python3-pip"],
            state="present",
            update_cache=True,
        )
        p.shell(
            "update-alternatives --install /usr/bin/python python /usr/bin/python3 1",
            display_name="Switching to python3"
        )
    if "dashboard" in roles:
        e = EthGethClique(bootnodes=roles["bootnode"], peers=peers, dashboard=roles["dashboard"])
    else:
        e = EthGethClique(bootnodes=roles["bootnode"], peers=peers)
    e.deploy()

    if "dashboard" in roles:
        m = Monitoring(collector=roles["dashboard"],
                       ui=roles["dashboard"],
                       agent=roles["bootnode"] + roles["peer"],
                       network='ntw_monitoring',
                       agent_conf=os.path.join(os.path.abspath(os.path.dirname(os.path.realpath(__file__))), 'files',
                                               'telegraf.conf.j2'))

        m.deploy()
        m.create_database('geth')
        ui_address = roles["dashboard"][0].extra["%s_ip" % m.network]

        print("GRAFANA : The Grafana UI is available at http://%s:3000" % ui_address)
        print("GRAFANA : user=admin, password=admin")
    else:
        print("No monitoring activated")


@enostask()
@print_ex_time
def backup(**kwargs):
    env = kwargs["env"]
    extra_vars = {
        "enos_action": "backup"
    }
    run_ansible([os.path.join(ANSIBLE_DIR, "site.yml")],
                env["inventory"], extra_vars=extra_vars)


@enostask()
@print_ex_time
def destroy(**kwargs):
    env = kwargs["env"]
    extra_vars = {
        "enos_action": "destroy"
    }
    run_ansible([os.path.join(ANSIBLE_DIR, "site.yml")],
                env["inventory"], extra_vars=extra_vars)


@enostask()
@print_ex_time
def benchmark(experiment_directory, main_file, env):
    roles = env["roles"]
    networks = env["networks"]

    l = BCTMark_Locust(master=roles["dashboard"],
                       agents=roles["bench_worker"],
                       network="ntw_monitoring",
                       influxdb=roles['dashboard'])

    l.deploy()
    l.run_with_ui(experiment_directory, main_file, targeted_hosts=(roles["bootnode"] + roles["peer"]))
    ui_address = roles["dashboard"][0].extra["%s_ip" % l.network]
    print("LOCUST : The Locust UI is available at http://%s:8089" % ui_address)


@enostask()
@print_ex_time
def replay(transactions_file, env):
    roles = env["roles"]
    networks = env["networks"]

    if "bench_worker" in roles:
        peers = roles["peer"] + roles["bench_worker"]
    else:
        peers = roles["peer"]

    e = EthGethClique(bootnodes=roles["bootnode"], peers=peers)
    b = BCTMarkWorker(roles["bench_worker"])
    r = ReplayManager(b, transactions_file, e)
    r.replay_transactions()


@enostask()
@print_ex_time
def debug(var, env):
    roles = env["roles"]
    with play_on(pattern_hosts="all", roles=roles) as p:
        p.debug(var=var)


PROVIDERS = {
    "g5k": g5k,
    "vagrant": vagrant,
    #    "static": static
    #    "chameleon": chameleon
}
