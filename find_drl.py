from src.device import Tokamak
from src.profile import Profile
from src.source import CDsource
from src.env import Enviornment
from src.rl.ppo import train_ppo, ActorCritic, ReplayBufferPPO
from src.rl.reward import RewardSender
from src.utility import plot_optimization_status, plot_policy_loss
from config.device_info import config_benchmark, config_liquid
import torch
import pickle
import argparse, os, warnings

warnings.filterwarnings(action = 'ignore')

def parsing():
    parser = argparse.ArgumentParser(description="Tokamak design optimization based on single-step RL")
    
    # Select blanket type: liquid / solid
    parser.add_argument("--blanket_type", type = str, default = "solid", choices = ['liquid','solid'])
    
    # GPU allocation
    parser.add_argument("--gpu_num", type = int, default = 0)
    
    # PPO setup
    parser.add_argument("--buffer_size", type = int, default = 8)
    parser.add_argument("--num_episode", type = int, default = 10000)
    parser.add_argument("--verbose", type = int, default = 1000)
    parser.add_argument("--lr", type = float, default = 2e-5)
    parser.add_argument("--gamma", type = float, default = 0.999)
    parser.add_argument("--eps_clip", type = float, default = 0.25)
    parser.add_argument("--entropy_coeff", type = float, default = 0.05)
    
    args = vars(parser.parse_args()) 

    return args

# torch device state
print("=============== Device setup ===============")
print("torch device avaliable : ", torch.cuda.is_available())
print("torch current device : ", torch.cuda.current_device())
print("torch device num : ", torch.cuda.device_count())
print("torch version : ", torch.__version__)
    
if __name__ == "__main__":
    
    args = parsing()
    
    # device allocation
    if(torch.cuda.device_count() >= 1):
        device = "cuda:{}".format(args['gpu_num'])
    else:
        device = 'cpu'
    
    if args['blanket_type'] == 'liquid':
        config = config_liquid
    else:
        config = config_benchmark

    profile = Profile(
        nu_T = config["nu_T"],
        nu_p = config["nu_p"],
        nu_n = config["nu_n"],
        n_avg = config["n_avg"], 
        T_avg = config["T_avg"], 
        p_avg = config['p_avg']
    )
    
    source = CDsource(
        conversion_efficiency = config['conversion_efficiency'],
        absorption_efficiency = config['absorption_efficiency'],
    )
    
    tokamak = Tokamak(
        profile,
        source,
        betan = config['betan'],
        Q = config['Q'],
        k = config['k'],
        epsilon = config['epsilon'],  
        tri = config['tri'],
        thermal_efficiency = config['thermal_efficiency'],
        electric_power = config['electric_power'],
        armour_thickness = config['armour_thickness'],
        armour_density = config['armour_density'],
        armour_cs = config['armour_cs'],
        maximum_wall_load = config['maximum_wall_load'],
        maximum_heat_load = config['maximum_heat_load'],
        shield_density = config['shield_density'],
        shield_depth = config['shield_depth'],
        shield_cs = config['shield_cs'],
        Li_6_density = config['Li_6_density'],
        Li_7_density = config['Li_7_density'],
        slowing_down_cs= config['slowing_down_cs'],
        breeding_cs= config['breeding_cs'],
        E_thres = config['E_thres'],
        pb_density = config['pb_density'],
        scatter_cs_pb=config['cs_pb_scatter'],
        multi_cs_pb=config['cs_pb_multi'],
        B0 = config['B0'],
        H = config['H'],
        maximum_allowable_J = config['maximum_allowable_J'],
        maximum_allowable_stress = config['maximum_allowable_stress'],
        RF_recirculating_rate= config['RF_recirculating_rate'],
        flux_ratio = config['flux_ratio']
    )
    
    reward_sender = RewardSender(
        w_cost = 1.0,
        w_tau = 1.0,
        w_beta = 5.0,
        w_density=5.0,
        w_q = 5.0,
        w_bs = 5.0,
        w_i = 5.0,
        cost_r = 1.0,
        tau_r = 1.0,
        beta_r = 4.0,
        q_r = 2.0,
        n_r = 3.0,
        f_r = 1.0,
        i_r = 1.0,
        a = 3.0
    )
    
    init_action = {
        'betan':config['betan'],
        'k':config['k'],
        'epsilon' : config['epsilon'],
        'electric_power' : config['electric_power'],
        'T_avg' : config['T_avg'],
        'B0' : config['B0'],
        'H' : config['H'],
        "armour_thickness" : config['armour_thickness'],
        "RF_recirculating_rate": config['RF_recirculating_rate'],
    }
    
    init_state = tokamak.get_design_performance()
    
    env = Enviornment(tokamak, reward_sender, init_state, init_action)
    
    # policy and value network
    policy_network = ActorCritic(input_dim = 19 + 9, mlp_dim = 32, n_actions = 9, std = 0.5)
    
    # gpu allocation
    policy_network.to(device)
    
    # optimizer    
    policy_optimizer = torch.optim.AdamW(policy_network.parameters(), lr = args['lr'])

    # loss function for critic network
    value_loss_fn = torch.nn.SmoothL1Loss(reduction = 'none')
    
    # memory
    memory = ReplayBufferPPO(args['buffer_size'])
    
    # directory
    if not os.path.exists("./weights"):
        os.makedirs("./weights")
    
    if not os.path.exists("./results"):
        os.makedirs("./results")
    
    tag = "PPO_{}".format(args['blanket_type'])
    save_best = "./weights/{}_best.pt".format(tag)
    save_last = "./weights/{}_last.pt".format(tag)
    save_result = "./results/params_search_{}.pkl".format(tag)
    
    # Design optimization
    print("============ Design optimization ============")
    result = train_ppo(
        env, 
        memory,
        policy_network,
        policy_optimizer,
        value_loss_fn,
        args['gamma'],
        args['eps_clip'],
        args['entropy_coeff'],
        device,
        args['num_episode'],
        args['verbose'],
        save_best,
        save_last,
    )
    
    print("======== Logging optimization process ========")
    optimization_status = env.optim_status
    plot_optimization_status(optimization_status, args['buffer_size'], "./results/ppo_optimization")
    
    plot_policy_loss(result['loss'], args['buffer_size'], "./results/ppo_optimization")
    
    with open(save_result, 'wb') as file:
        pickle.dump(result, file)
        
    env.close()