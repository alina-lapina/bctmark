from .plan.experiment import Experiment
import yaml

class Planner:
    def __init__(self, experiments):
        self.experiments = []
        for experiment in experiments:
            global_variables = None
            if "global_variables" in experiment:
                global_variables = experiment["global_variables"]
            self.experiments.append(
                Experiment(
                    name=experiment["name"],
                    description=experiment["description"],
                    typology=experiment["typology"],
                    steps=experiment["steps"],
                    global_variables=global_variables
                )
            )

    def run(self, provider, force):
        print("[-] Running experiments")
        for experiment in self.experiments:
            experiment.run(provider, force)
