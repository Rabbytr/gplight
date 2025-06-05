import os
import argparse
import agent
from gp_utils import std_pset, std_toolbox, Evolution
from world.world_cityflow import World
from environment import TSCEnv
import numpy as np
from common.registry import Registry
from deap import gp
from common import interface
from utils.logger import build_config


class Evaluation(object):
    def __init__(self, network_name, agent, thread_num=1):

        file_name = f'{network_name}.cfg'
        path = os.path.join('configs/sim/', file_name)

        world = World(path, thread_num=thread_num)

        self.agents = [agent(world, i) for i in range(len(world.intersections))]

        self.env = TSCEnv(world, self.agents, None)

    def _run(self):
        last_obs = self.env.reset()
        for _ in range(0, 3600, 10):
            actions = []
            last_phase = np.stack([ag.get_phase() for ag in self.agents])  # [agent, intersections]
            for idx, ag in enumerate(self.agents):
                actions.append(ag.get_action(last_obs[idx], last_phase[idx], test=False))
            actions = np.stack(actions)
            for i in range(10):
                obs, rewards, dones, _ = self.env.step(actions.flatten())

        return self.env.eng.get_average_travel_time()

    def evaluate(self, func):
        for ag in self.agents:
            ag.rule = func
            ag.reset()
        return self._run()


parser = argparse.ArgumentParser(description='Run Experiment')
parser.add_argument('--thread_num', type=int, default=1, help='number of threads')  # used in cityflow
parser.add_argument('-t', '--task', type=str, default="tsc", help="task type to run")
parser.add_argument('--seed', type=int, default=1, help="seed algorithem")
parser.add_argument('--agent', type=str, default='gplight_plus', help="seed algorithem")
parser.add_argument('-n', '--network', type=str, default='cityflow4x4', help="network name")

args = parser.parse_args()

config, _ = build_config(args)
interface.ModelAgent_param_Interface(config)

ag_cls = Registry.mapping['model_mapping'][args.agent]
model = Evaluation(args.network, agent=ag_cls, thread_num=args.thread_num)


def evaluate(individual, pset):
    func = gp.compile(expr=individual, pset=pset)
    return model.evaluate(func),


if __name__ == '__main__':
    from pathos.multiprocessing import ProcessPool

    pset = std_pset(ag_cls.ARITY)
    toolbox = std_toolbox(pset)

    toolbox.register('evaluate', evaluate, pset=pset)
    pool = ProcessPool(5)
    toolbox.register('map', pool.map)

    pop = toolbox.population(n=5)
    Evolution(population=pop, ngen=5, toolbox=toolbox, pset=pset, seed=args.seed, save_path=None).run()
