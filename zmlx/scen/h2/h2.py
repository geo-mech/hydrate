"""
定义氢气的参数

by 张琦
"""

import math

import zmlx.alg.sys as warnings
from zml import Interp2, Seepage, data_version


def create(t_min=150, t_max=423, p_min=0.1e6, p_max=220e6, name=None):
    """
    参考：Correlations for prediction of hydrogen gas viscosity and density for production, transportation, storage, and utilization applications
          https://doi.org/10.1016/j.ijhydene.2023.05.202
    """

    assert 140 < t_min < t_max < 430
    assert 0.0e6 < p_min < p_max < 230e6
    
    a = [0.958737511232263,-0.0537931756541833,-0.0417130264021347,0.00401309021911078,1.1146015668052e-5]
    b = [0.00150682400345535,0.00132122304497608,2.20790728835293e-12,-7.46651846381023e-17,4.45098340713357e-15]
    c = [0.4492195,-23.84114,0.0562519,1.01124,-0.0289739,-0.0011064,-0.0385377,-42.98531,0.0010446,
         0.004043,0.0043762,-70.18049,0.016152,0.0092372,0.1085783,0.0076386,-9.09e-05]
    Tc = 33.19    #K
    Pc = 1.315e6  #Pa
    

    
    def get_density(P, T):
        T = max(t_min, min(t_max, T))
        P = max(p_min, min(p_max, P))

        Tpr, Ppr = T/Tc, P/Pc
        A = c[0]*(Tpr-c[1])**(0.5)-c[2]*Tpr-c[3]
        B = (c[4]-c[5]*Tpr)*Ppr + (c[6]/(Tpr-c[7])-c[8]+c[9]/(10**(c[10]*(Tpr-c[11]))))*Ppr**2
        C = c[12]-c[13]*math.log(Tpr)
        D = 10**(c[14]-c[15]*Tpr+c[16]*Tpr**2)
        Z = A + (1-A)/math.exp(B) + C*Ppr**D
        density = (P*2.016e-3)/(Z*8.314472*T)  #kg/m3
        return density

    def get_viscosity(P, T):
        T = max(t_min, min(t_max, T))
        P = max(p_min, min(p_max, P))
        density = get_density(P, T)

        T_s = T/30.41
        E = a[0] + a[1]*math.log(T_s) + a[2]*math.log(T_s)**2 + a[3]*math.log(T_s)**3 + \
            a[4]*math.log(T_s)**4
        vis_0 = 1.00697*T**(1/2)/(math.exp(E))  
        vis_ex = b[0]*density + b[1]*density**2 + b[2]*density**6/T_s**3 + b[3]*density**8 + b[4]*density**8/T_s
        viscosity = (vis_0 + vis_ex) * 1.0e-6     #Pa*s
        return viscosity

    def create_density():
        den = Interp2()
        den.create(p_min, 0.1e6, p_max, t_min, 1, t_max, get_density)
        return den

    def create_viscosity():
        vis = Interp2()
        vis.create(p_min, 0.1e6, p_max, t_min, 1, t_max, get_viscosity)
        return vis
        
    specific_heat = 14300.0

    return Seepage.FluDef(
        den=create_density(), vis=create_viscosity(),
        specific_heat=specific_heat, name=name)


def create_flu(*args, **kwargs):
    warnings.warn('use function <create> instead', DeprecationWarning,
                  stacklevel=2)
    return create(*args, **kwargs)


def show_all():
    from zmlx.plt.fig2 import show_field2
    flu = create()
    show_field2(flu.den, [4e6, 15e6], [274, 290], caption='den')
    show_field2(flu.vis, [4e6, 15e6], [274, 290], caption='vis')


if __name__ == '__main__':
    from zmlx.ui import gui

    gui.execute(show_all, close_after_done=False)
