# ** desc = 'matplotlib绘图示例'
#
# 本案例演示频谱分析的可视化。生成一个含有噪声的正弦信号，使用
# matplotlib的subplot_mosaic创建复合布局，分别绘制时域信号、
# 幅度谱、对数幅度谱（dB）、相位谱和角度谱。展示了信号处理中
# 常用频谱分析函数的绘图方法。

from zmlx import *


def on_figure(fig):
    """
    在figure上绘制频谱分析图

    生成一个带噪声的4Hz正弦信号（采样率100Hz，时长10s），
    用subplot_mosaic排列子图，分别展示时域信号和四种频谱分析结果。

    Args:
        fig: matplotlib.figure.Figure对象
    """
    np.random.seed(0)

    dt = 0.01           # 采样间隔（s）
    Fs = 1 / dt         # 采样频率（Hz）
    t = np.arange(0, 10, dt)

    # 生成有色噪声：白噪声经指数衰减滤波器卷积
    nse = np.random.randn(len(t))
    r = np.exp(-t / 0.05)         # 指数衰减滤波器（时间常数0.05s）
    cnse = np.convolve(nse, r) * dt
    cnse = cnse[:len(t)]          # 截断至与时间序列相同长度

    # 合成信号：4Hz正弦波 + 有色噪声
    s = 0.1 * np.sin(4 * np.pi * t) + cnse

    # 创建马赛克布局子图
    # 第一行：信号（占两列），第二行：幅度谱和对数幅度谱，
    # 第三行：相位谱和角度谱
    axs = fig.subplot_mosaic([["signal", "signal"],
                              ["magnitude", "log_magnitude"],
                              ["phase", "angle"]])

    # 绘制时域信号
    axs["signal"].set_title("Signal")
    axs["signal"].plot(t, s, color='C0')
    axs["signal"].set_xlabel("Time (s)")
    axs["signal"].set_ylabel("Amplitude")

    # 绘制不同类型的频谱图
    axs["magnitude"].set_title("Magnitude Spectrum")
    axs["magnitude"].magnitude_spectrum(s, Fs=Fs, color='C1')

    axs["log_magnitude"].set_title("Log. Magnitude Spectrum")
    axs["log_magnitude"].magnitude_spectrum(s, Fs=Fs, scale='dB', color='C1')

    axs["phase"].set_title("Phase Spectrum ")
    axs["phase"].phase_spectrum(s, Fs=Fs, color='C2')

    axs["angle"].set_title("Angle Spectrum")
    axs["angle"].angle_spectrum(s, Fs=Fs, color='C2')
    fig.tight_layout()


if __name__ == '__main__':
    plot(on_figure, gui_mode=True)
