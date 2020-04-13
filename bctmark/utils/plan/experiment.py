from .step import Step
from enoslib.api import play_on
import bctmark.tasks as t
import time
import yaml

class Experiment:
    def __init__(self, name, description, typology, steps, global_variables):
        self.name = name
        self.description = description
        self.typology = typology
        self.steps = []
        for step in steps:
            self.steps.append(Step(step, self.name))
        self.global_variables = global_variables

    def deploy(self, provider, force):
        with open(self.typology, 'r') as f:
            typology_conf = yaml.safe_load(f)
        env = t.PROVIDERS[provider](typology_conf, force, env=self.name)
        t.inventory()
        t.prepare(env=self.name)
        return env

    def run(self, provider, force):
        print(f"[-] Running experiment {self.name}")
        print("[-] Deployment")
        
        env = None

        for i in range(0,3):
            try:
                env = self.deploy(provider, force)
            except Exception as e:
                print(f"[!] Deployment failed - {e}")
                continue
            break

        if env is None:
            raise Exception("Could not deploy")

        if self.global_variables is not None:
            with play_on(pattern_hosts="bench_worker", roles=env["roles"]) as p:
                for variable in self.global_variables:
                    variable_name = next(iter(variable.keys()))
                    variable_content = variable[variable_name]
                    p.lineinfile(
                        display_name=f"Declaring global var {variable_name}",
                        path="/etc/environment",
                        create="yes",
                        state="present",
                        regexp=f"^{variable_name}",
                        line=f"{variable_name}={variable_content}"
                    )

        print("[-] Running experiment")
        for step in self.steps:
            step.run()

        print("[-] Results backup")
        t.backup(env=self.name) 

        print("[-] Destroy environment")
        t.destroy(env=self.name)
