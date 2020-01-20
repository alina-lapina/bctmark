from enoslib.api import play_on, run_ansible, __python3__, __default_python3__
from enoslib.host import Host
from enoslib.service.service import Service
from typing import List, AnyStr
import os

CURRENT_PATH = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))


class BCTMarkWorker(Service):
    def __init__(self, workers: List[Host], priors=[__python3__, __default_python3__]):
        self.workers = workers
        self.roles = {'workers': workers}
        self.priors = priors

    def deploy(self):
        with play_on(pattern_hosts="all", roles=self.roles, priors=self.priors) as p:
            p.apt(
                display_name="[Preinstall] Installing git",
                name="git",
                state="present",
                update_cache=True,
            )
            p.pip(
                display_name='Installing BCTMark_worker from Gitlab',
                name='git+https://gitlab.inria.fr/dsaingre/bctmark_worker',
                executable="pip3"
            )

    def destroy(self):
        pass

    def backup(self):
        pass

    def run(self, trxfile: AnyStr):
        with play_on(pattern_hosts="all", roles=self.roles) as p:
            p.shell(
                "nohup bctmark_worker replay %s &" % trxfile,
                display_name="Running BCTMark workers on file %s" % trxfile
            )