import click
import logging
import yaml

import bctmark.tasks as t
from bctmark.constants import CONF

logging.basicConfig(level=logging.INFO)


@click.group()
def cli():
    pass


def load_config(file_path):
    """
    Read configuration from a file in YAML format.
    :param file_path: Path of the configuration file.
    :return:
    """
    with open(file_path) as f:
        configuration = yaml.safe_load(f)
    return configuration


@cli.command(help="Claim resources on Grid'5000 (frontend).")
@click.option("--force",
              is_flag=True,
              help="force redeployment")
@click.option("--conf",
              default=CONF,
              help="alternative configuration file")
@click.option("--env",
              help="alternative environment directory")
def g5k(force, conf, env):
    config = load_config(conf)
    t.g5k(config, force, env=env)


@cli.command(help="Claim resources on vagrant (localhost).")
@click.option("--force",
              is_flag=True,
              help="force redeployment")
@click.option("--conf",
              default=CONF,
              help="alternative configuration file")
@click.option("--env",
              help="alternative environment directory")
def vagrant(force, conf, env):
    config = load_config(conf)
    t.vagrant(config, force, env=env)


@cli.command(help="Claim resources on a static provider.")
@click.option("--force",
              is_flag=True,
              help="force redeployment")
@click.option("--conf",
              default=CONF,
              help="alternative configuration file")
@click.option("--env",
              help="alternative environment directory")
def static(force, conf, env):
    config = load_config(conf)
    t.static(config, force, env=env)


@cli.command(help="Emulate network constraints")
@click.option("--conf",
              default=CONF,
              help="alternative configuration file")
@click.option("--env",
              help="alternative environment directory")
def emulate(conf, env):
    config = load_config(conf)
    t.emulate(config, env=env)


@cli.command(help="Generate the Ansible inventory [after g5k or vagrant].")
@click.option("--env",
              help="alternative environment directory")
def inventory(env):
    t.inventory(env=env)


@cli.command(help="Configure available resources [after deploy, inventory or\
             destroy].")
@click.option("--env",
              help="alternative environment directory")
def prepare(env):
    t.prepare(env=env)


@cli.command(help="Backup the deployed environment")
@click.option("--env",
              help="alternative environment directory")
def backup(env):
    t.backup(env=env)


@cli.command(help="Destroy the deployed environment")
@click.option("--env",
              help="alternative environment directory")
def destroy(env):
    t.destroy(env=env)


@cli.command(help="Claim resources from a PROVIDER and configure them.")
@click.argument("provider")
@click.option("--force",
              is_flag=True,
              help="force redeployment")
@click.option("--conf",
              default=CONF,
              help="alternative configuration file")
@click.option("--env",
              help="alternative environment directory")
def deploy(provider, force, conf, env):
    config = load_config(conf)
    t.PROVIDERS[provider](config, force, env=env)
    t.inventory()
    t.prepare(env=env)

@cli.command(help="Run several experiments following a plan")
@click.argument("provider")
@click.argument("plan")
@click.option("--force",
        is_flag=True,
        help="force redeployment")
def run(provider, plan, force):
    with open(plan, 'r') as f:
        t.run(provider, yaml.safe_load(f), force)

@cli.command(help="Run benchmark from bctmark_locust script")
@click.argument("experiment_directory")
@click.argument("main_file")
@click.option("--env",
              help="alternative environment directory")
def benchmark(experiment_directory, main_file, env):
    t.benchmark(experiment_directory, main_file, env=env)


@cli.command(help="Run benchmark from bctmark_locust script (headless)")
@click.argument("experiment_directory")
@click.argument("main_file")
@click.argument("nb_clients")
@click.argument("hatch_rate")
@click.argument("run_time")
@click.argument("density")
@click.option("--env",
              help="alternative environment directory")
def benchmark_headless(experiment_directory, main_file, nb_clients, hatch_rate, run_time, density, env):
    t.benchmark_headless(experiment_directory, main_file, nb_clients, hatch_rate, run_time, density, env=env)


@cli.command(help="Replay transactions based on YAML file")
@click.argument("transactions_file")
@click.option("--env",
              help="alternative environment directory")
def replay(transactions_file, env):
    t.replay(transactions_file, env=env)


@cli.command(help="Debug")
@click.argument("var")
@click.option("--env",
              help="alternative environment directory")
def debug(var, env):
    t.debug(var, env=env)


@cli.command(help="Print environment info")
@click.option("--role",
              help="filter on a given role")
@click.option("--env",
              help="alternative environment directory")
def status(role, env):
    t.status(env=env, role_asked=role)
