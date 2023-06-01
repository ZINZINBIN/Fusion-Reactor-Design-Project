from src.device import Tokamak
from src.profile import Profile

if __name__ == "__main__":
    
    profile = Profile(
        nu_T = 1,
        nu_p = 1.5,
        nu_n = 0.5,
        n_avg = 1.43 * 10 ** 20, 
        T_avg = 14, 
        p_avg = 8.0 * 1.01 * 10 ** 5
    )
    
    tokamak = Tokamak(
        profile,
        k = 1.7,
        epsilon = 4,  
        tri = 0,
        thermal_efficiency = 0.4,
        electric_power = 1000 * 10 ** 6,
        armour_thickness = 0.1,
        armour_density = 4.6 * 10 ** 28,
        armour_cs = 2 * 10 ** (-18),
        maximum_wall_load = 4.0 * 10 ** 6,
        maximum_heat_load = 0,
        shield_density = 4.6 * 10 ** 28,
        shield_depth = 0.1,
        shield_cs = 2 * 10 ** (-18),
        Li_6_density = 0.34 * 10 ** 28,
        Li_7_density = 4.6 * 10 ** 28,
        slowing_down_cs= 2 * 10 ** (-28),
        breeding_cs= 950 * 10 ** (-28),
        E_thres = 0.025 * 10 ** (-6),
        B0 = 13,
        H = 1,
        maximum_allowable_J = 20 * 10 ** 6,
        maximum_allowable_stress = 600 * 10 ** 6
    )
    
    tokamak.print_info()
    tokamak.check_operation_limit()