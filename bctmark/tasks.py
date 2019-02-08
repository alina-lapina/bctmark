from enoslib.api import generate_inventory, run_ansible
from enoslib.task import enostask
from enoslib.infra.enos_g5k.provider import G5k
from enoslib.infra.enos_vagrant.provider import Enos_vagrant
import logging
import os

from bctmark.constants import ANSIBLE_DIR

logger = logging.getLogger(__name__)


@enostask(new=True)
def g5k(config, force, env=None, **kwargs):
    provider = G5k(config["g5k"])
    roles, networks = provider.init(force_deploy=force)
    env["config"] = config
    env["roles"] = roles
    env["networks"] = networks


@enostask(new=True)
def vagrant(config, force, env=None, **kwargs):
    provider = Enos_vagrant(config["vagrant"])
    roles, networks = provider.init(force_deploy=force)
    env["config"] = config
    env["roles"] = roles
    env["networks"] = networks


@enostask()
def inventory(**kwargs):
    env = kwargs["env"]
    roles = env["roles"]
    networks = env["networks"]
    env["inventory"] = os.path.join(env["resultdir"], "hosts")
    generate_inventory(roles, networks, env["inventory"], check_networks=True)


@enostask()
def prepare(**kwargs):
    env = kwargs["env"]
    extra_vars = {
        "enos_action": "deploy"
    }
    run_ansible([os.path.join(ANSIBLE_DIR, "site.yml")],
                env["inventory"], extra_vars=extra_vars)


@enostask()
def backup(**kwargs):
    env = kwargs["env"]
    extra_vars = {
        "enos_action": "backup"
    }
    run_ansible([os.path.join(ANSIBLE_DIR, "site.yml")],
                env["inventory"], extra_vars=extra_vars)


@enostask()
def destroy(**kwargs):
    env = kwargs["env"]
    extra_vars = {
        "enos_action": "destroy"
    }
    run_ansible([os.path.join(ANSIBLE_DIR, "site.yml")],
                env["inventory"], extra_vars=extra_vars)


PROVIDERS = {
    "g5k": g5k,
    "vagrant": vagrant,
    #    "static": static
    #    "chameleon": chameleon
}


