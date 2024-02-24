from zmlx.alg.sbatch import sbatch
import numpy as np


def main():
    sbatch('-m', 'zmlx.config.co2', 'co2_seq', 'base', c=2, t=1)

    for value in np.linspace(60, 300, 13):
        sbatch('-m', 'zmlx.config.co2', 'co2_seq', 'inj_depth', f'{value}', c=2, t=1)

    for value in 10 ** np.linspace(0, 2, 11) * 1.0e-15:
        sbatch('-m', 'zmlx.config.co2', 'co2_seq', 'perm', f'{value}', c=2, t=1)

    for value in np.linspace(5e6, 25e6, 21):
        sbatch('-m', 'zmlx.config.co2', 'co2_seq', 'p_seabed', f'{value}', c=2, t=1)

    for value in np.linspace(0.5, 6, 12) + 273.15:
        sbatch('-m', 'zmlx.config.co2', 'co2_seq', 't_seabed', f'{value}', c=2, t=1)


if __name__ == '__main__':
    main()
