from enoslib.api import play_on
from enoslib.service import Locust
import os

CURRENT_PATH = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))


class BCTMark_Locust(Locust):
    def __init__(self, master={}, agents={}, network=None, influxdb=None, **kwargs):
        Locust.__init__(self, master, agents, network, **kwargs)
        self.influxdb = influxdb

    def deploy(self):
        with play_on(pattern_hosts="all", roles=self.roles) as p:
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
        super().deploy()

    def run_with_ui(self, expe_dir, file_name, port="8089", targeted_hosts=None):
        self.__write_targeted_hosts_file(targeted_hosts if targeted_hosts else self.roles)
        super().run_with_ui(expe_dir, file_name, port)

    def run_headless(self, expe_dir, file_name, nb_clients, hatch_rate, time, targeted_hosts=None):
        self.__write_targeted_hosts_file(targeted_hosts if targeted_hosts else self.roles)
        super().run_headless(expe_dir, file_name, nb_clients, hatch_rate, time)

    def __generate_hosts_list(self, roles):
        hosts = []
        for role in roles:
            hosts.append(role.extra['%s_ip' % self.network])
        return hosts

    def __write_targeted_hosts_file(self, targeted_hosts):
        with play_on(pattern_hosts="agent", roles=self.roles) as p:
            if self.influxdb is not None:
                p.set_fact(influxdb_addresses=self.__generate_hosts_list(self.influxdb))
            p.set_fact(target_addresses=self.__generate_hosts_list(targeted_hosts))
            p.template(
                display_name="Copying targeted hosts file",
                src="%s/templates/targeted_hosts.toml.j2" % (os.path.join(CURRENT_PATH)),
                dest="/tmp/targeted_hosts.toml",
                mode="u=rwx,g=rwx,o=rwx",
            )
