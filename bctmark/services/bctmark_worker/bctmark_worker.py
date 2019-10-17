from enoslib.api import play_on
from enoslib.host import Host
from enoslib.service.service import Service
from typing import List, AnyStr


class BCTMarkWorker(Service):
    def __init__(self, workers: List[Host]):
        self.workers = workers
        self.roles = {'workers': workers}

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
                display_name="Switching to python3 if needed"
            )
            p.pip(
                display_name='Installing BCTMark_worker from Gitlab',
                name='git+https://gitlab.inria.fr/dsaingre/bctmark_worker'
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
