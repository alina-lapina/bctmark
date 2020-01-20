from enoslib.api import play_on, __python2__, __python3__, __default_python3__
from enoslib.service import Locust
import os

CURRENT_PATH = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))


class BCTMarkLocust(Locust):

    def __init__(
            self,
            master={},
            agents={},
            network=None,
            influxdb=None,
            priors=[__python2__, __python3__, __default_python3__],
            **kwargs
    ):
        Locust.__init__(self, master, agents, network, priors=priors, **kwargs)
        self.influxdb = influxdb
        self.network = network

    def run_with_ui(self, expe_dir, file_name, targeted_hosts=None):
        self.__write_targeted_hosts_file(targeted_hosts if targeted_hosts else self.roles)
        super().run_with_ui(expe_dir, file_name)

    def run_headless(self, expe_dir, file_name, nb_clients, hatch_rate, time, targeted_hosts=None):
        self.__write_targeted_hosts_file(targeted_hosts if targeted_hosts else self.roles)
        super().run_headless(expe_dir, file_name, nb_clients, hatch_rate, time)

    def backup(self):
        super()
        pass

    def __generate_hosts_list(self, roles):
        return map(lambda x: x.extra['%s_ip' % self.network], roles)

    def __write_targeted_hosts_file(self, targeted_hosts):
        with play_on(pattern_hosts="agent", roles=self.roles) as p:
            if self.influxdb is not None:
                p.set_fact(influxdb_addresses=self.__generate_hosts_list(self.influxdb))
            p.set_fact(target_roles=map(lambda x: self.__generate_hosts_list(x), targeted_hosts))
            p.template(
                display_name="Copying targeted hosts file",
                src="%s/templates/targeted_hosts.toml.j2" % (os.path.join(CURRENT_PATH)),
                dest="/tmp/targeted_hosts.toml",
                mode="u=rwx,g=rwx,o=rwx",
            )
