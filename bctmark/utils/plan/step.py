import bctmark.tasks as t
import time

class Step:
    def __init__(self, action, env):
        self.env = env
        self.action_name = next(iter(action.keys()))
        self.action_params = action[self.action_name]

    def run(self):
        if self.action_name == "wait_for":
            self._wait_for()
        if self.action_name == "benchmark_headless":
            self._benchmark_headless()

    def _wait_for(self):
        print(f"[-] WAITING FOR {self.action_params} seconds")
        time.sleep(int(self.action_params))

    def _benchmark_headless(self):
        print("[-] Runing an headless benchmark")
        t.benchmark_headless(
            self.action_params[0]['experiment_directory'],
            self.action_params[0]['main_file'],
            self.action_params[0]['nb_clients'],
            self.action_params[0]['hatch_rate'],
            self.action_params[0]['run_time'],
            self.action_params[0]['density'],
            env=self.env
        )
