import warnings
import os, pickle, random
import numpy as np
from collections import namedtuple, deque
from typing import List, Literal
from tqdm.auto import tqdm

from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern, WhiteKernel
from config.search_space_info import search_space, state_space
from src.bayesian.func import acq_max, UtilityFunction
from src.bayesian.action_space import ActionSpace
from src.env import Enviornment

# transition
Transition = namedtuple(
    "Transition", ("state", "action", "next_state", "reward", "done", "prob_a")
)

default_action_range = search_space
default_state_range = state_space

class ContextualBayesianOptimization:
    def __init__(self, all_actions_dict, contexts, kernel, noise:float=1e-6, points:List=[], rewards:List=[], init_random=3):

        self._space = ActionSpace(all_actions_dict, contexts)
        self.init_random = init_random

        if len(points) > 0:
            gp_hyp = GaussianProcessRegressor(
                kernel=kernel, alpha=noise, normalize_y=True, n_restarts_optimizer=5
            )

            print("Optimizing kernel hyperparameters....")
            
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                gp_hyp.fit(points, rewards)
                
            print("Done!")

            opt_hyp = gp_hyp.kernel_.get_params()
            kernel.set_params(**opt_hyp)
            optimizer = None
        else:
            warnings.warn(
                "Kernel hyperparameters will be computed during the optimization."
            )
            optimizer = "fmin_l_bfgs_b"

        self._gp = GaussianProcessRegressor(
            kernel=kernel, alpha=noise, normalize_y=True, optimizer=optimizer
        )

    @property
    def space(self):
        return self._space

    @property
    def res(self):
        return self._space.res()

    def register(self, context, action, reward):
        """Expect observation with known reward"""
        self._space.register(context, action, reward)

    def array_to_context(self, context):
        return self._space.array_to_context(context)

    def action_to_array(self, action):
        return self._space.action_to_array(action)

    def context_to_array(self, context):
        return self._space.context_to_array(context)

    def suggest(self, context, utility_function):
        """Most promissing point to probe next"""
        assert len(context) == self._space.context_dim
        context = self._space.context_to_array(context)
        if len(self._space) < self.init_random:
            return self._space.array_to_action(self._space.random_sample())

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self._gp.fit(self._space.context_action, self._space.reward)

        # Finding argmax of the acquisition function.
        suggestion = acq_max(
            ac=utility_function.utility,
            gp=self._gp,
            all_discr_actions=self._space._allActions,
            context=context,
        )

        return self._space.array_to_action(suggestion)


def search_param_space(
    env: Enviornment, 
    num_episode: int = 10000, 
    verbose: int = 1000,
    noise : float = 1e-6,
    nu:float = 1.5,
    noise_level:int = 1,
    beta_function:Literal['cost']='const',
    beta_const_val:float=2.5,
    init_random : int = 3
    ):

    # define kernel
    kernel = WhiteKernel(noise_level=noise_level) + Matern(nu=nu, length_scale=np.ones(context_dim+action_dim))
    
    # define offline bayesian optimizer
    optimizer = ContextualBayesianOptimization(all_actions_dict, contexts, kernel, noise = noise, points =[], rewards =[], init_random=init_random)

    utility = UtilityFunction(
        kind="ucb", beta_kind=beta_function, beta_const=beta_const_val
    )

    for i_episode in tqdm(range(num_episode), desc = 'Contextual bayesian optimization algorithm for design optimization'):

        if env.current_state is None:
            state = env.init_state
            ctrl = env.init_action
        else:
            state = env.current_state
            ctrl = env.current_action

        context = np.array([state[key] for key in state.keys()] + [ctrl[key] for key in ctrl.keys()])
        context = optimizer.array_to_context(context)

        ctrl_new = optimizer.suggest(context, utility)
        state_new, reward, done, _ = env.step(ctrl_new)

        if state_new is None:
            continue

        # register info to optimizer
        optimizer.register(state_new, ctrl_new, reward)

        # update state
        env.current_state = state_new
        env.current_action = ctrl_new

        if i_episode % verbose == 0:
            print(
                r"| episode:{} | reward : {} | tau : {:.3f} | beta limit : {} | q limit : {} | n limit {} | f_bs limit : {} | ignition : {} | cost : {:.3f}".format(
                    i_episode + 1,
                    env.rewards[-1],
                    env.taus[-1],
                    env.beta_limits[-1],
                    env.q_limits[-1],
                    env.n_limits[-1],
                    env.f_limits[-1],
                    env.i_limits[-1],
                    env.costs[-1],
                )
            )
            env.tokamak.print_info(None)

        if i_episode >= num_episode:
            break

    print("Contextual bayesian optimization process clear....!")

    result = {
        "control": env.actions,
        "state": env.states,
        "reward": env.rewards,
        "tau": env.taus,
        "beta_limit": env.beta_limits,
        "q_limit": env.q_limits,
        "n_limit": env.n_limits,
        "f_limit": env.f_limits,
        "i_limit": env.i_limits,
        "cost": env.costs,
    }

    return result
