import os
import operator
from functools import partial
from deap import gp, base, tools, algorithms
import numpy as np
import contextlib
import random


def div(x1, x2):
    if abs(x2) < 1e-6:
        return 1
    return x1 / x2


@contextlib.contextmanager
def seeded_random_state(seed):
    pre_rd_state = random.getstate()
    pre_np_state = np.random.get_state()

    random.seed(seed)
    np.random.seed(seed)
    try:
        yield
    finally:
        random.setstate(pre_rd_state)
        np.random.set_state(pre_np_state)


class IndividualMin(gp.PrimitiveTree):
    def __init__(self, gene_gen):
        super().__init__(gene_gen)
        self.fitness = type('', (base.Fitness,), {'weights': (-1.0,)})()


def std_pset(input_dim: int):
    pset = gp.PrimitiveSet("MAIN", arity=input_dim, prefix='x')
    pset.addPrimitive(operator.add, 2)
    pset.addPrimitive(operator.sub, 2)
    pset.addPrimitive(operator.mul, 2)
    pset.addPrimitive(div, 2)
    # pset.addPrimitive(operator.neg, 1)

    pset.addEphemeralConstant('c', partial(np.random.uniform, -1, 1))
    return pset


def std_toolbox(pset):
    toolbox = base.Toolbox()
    toolbox.register("expr", gp.genHalfAndHalf, pset=pset, min_=1, max_=3)
    toolbox.register("individual", tools.initIterate, IndividualMin, toolbox.expr)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("compile", gp.compile, pset=pset)
    toolbox.register("select", tools.selTournament, tournsize=3)
    toolbox.register("mate", gp.cxOnePoint)
    toolbox.register("mutate", gp.mutUniform, expr=toolbox.expr, pset=pset)

    toolbox.decorate("mate", gp.staticLimit(key=operator.attrgetter("height"), max_value=5))
    toolbox.decorate("mutate", gp.staticLimit(key=operator.attrgetter("height"), max_value=5))
    return toolbox


def std_stats():
    stats = tools.Statistics(lambda ind: ind.fitness.values[0])
    stats.register("avg", np.mean)
    stats.register("std", np.std)
    stats.register("min", np.min)
    stats.register("max", np.max)
    return stats


class Evolution(object):
    def __init__(self, population, ngen, toolbox, pset, seed: int = 42, save_path=None, stats=None):
        if not hasattr(toolbox, 'evaluate'):
            raise AttributeError("Toolbox should have attribute 'evaluate'")

        self.save_path = save_path
        self.seed = seed
        self.save_path = os.path.join(save_path, f'log_{self.seed}') if save_path else None

        self.population = population
        self.toolbox = toolbox
        self.pset = pset
        self.n_gen = ngen
        self.n_pop = len(population)

        self.hof = tools.HallOfFame(1)

        self.stats = std_stats() if stats is None else stats
        self.logbook = tools.Logbook()
        self.logbook.header = ['gen', 'nevals'] + self.stats.fields

    def run(self):
        if self.save_path:
            os.makedirs(self.save_path, exist_ok=True)
            # os.makedirs(self.history_path, exist_ok=True)
        with seeded_random_state(seed=self.seed):
            for gen in range(self.n_gen):
                self.step(gen)

        self._save_final_state()

    @property
    def history_path(self):
        return os.path.join(self.save_path, 'history') if self.save_path else None

    def _save_final_state(self):
        if self.save_path is None:
            return
        raise NotImplementedError

    def step(self, gen: int):
        fitnesses, invalid_ind = self._eval()

        self._log(gen, len(invalid_ind))
        if gen == self.n_gen - 1: return

        elites = tools.selBest(self.population, k=1)
        offspring = self.toolbox.select(self.population, self.n_pop - 1)
        offspring = algorithms.varAnd(offspring, self.toolbox, 0.9, 0.1)

        self.population = elites + offspring

    def _eval(self):
        invalid_ind = [ind for ind in self.population if not ind.fitness.valid]
        fitnesses = self.toolbox.map(self.toolbox.evaluate, invalid_ind)

        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit
        return fitnesses, invalid_ind

    def _log(self, gen: int, n_eval: int):
        self.hof.update(self.population)
        record = self.stats.compile(self.population)
        self.logbook.record(gen=gen, nevals=n_eval, **record)
        print(self.logbook.stream, flush=True)
