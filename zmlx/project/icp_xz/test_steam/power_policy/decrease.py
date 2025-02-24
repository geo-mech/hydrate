from icp_xz.steam_injection import steam_injection
from icp_xz.test_steam.opath import opath

if __name__ == '__main__':
    time_heating = 5.0 * 365.0 * 24.0 * 3600.0
    time_to_power = []
    time = 0
    while time < time_heating:
        power = 10e3 * (time_heating - time) / time_heating
        time_to_power.append([time, power])
        time += 3600.0
    steam_injection(folder=opath('power_policy', 'decrease'),
                    time_to_power=time_to_power)
