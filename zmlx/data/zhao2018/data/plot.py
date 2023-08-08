import matplotlib.pyplot as plt
import numpy as np

# #font seetting
# font = {
#     'family': 'sans-serif',
#     'sans-serif': 'Arial',
#     'weight': 'normal',
#     'size': 20
# }
# plt.rc('font', **font)  # pass in the font dict as kwargs
plt.rcParams['xtick.direction'] = 'in'
plt.rcParams['ytick.direction'] = 'in'


def plot(filename):
    d = np.loadtxt(filename)
    plt.plot(d[:, 0], d[:, 1], linewidth=2.0, linestyle='-', color='r')
    # plt.xlim(left=0, right=1)
    ax = plt.gca()
    ax.xaxis.set_ticks_position('top')
    ax.invert_yaxis()
    ax.xaxis.set_label_position('top')


plt.subplot(171)
plot('TOC实测.txt')
plt.ylabel('Depth (m)')

plt.subplot(172)
plot('游离气含量.txt')
plt.yticks([])

plt.subplot(173)
plot('滞留轻质油量.txt')
plt.yticks([])

plt.subplot(174)
plot('滞留轻质+中质+重质油量.txt')
plt.yticks([])

plt.subplot(175)
plot('残余生油潜力.txt')
plt.yticks([])

plt.subplot(176)
plot('含水饱和度.txt')
plt.yticks([])

plt.subplot(177)
plot('含水率.txt')
plt.yticks([])

plt.tight_layout()
plt.show()
