"""
用于模拟砂的沉降及脱离
"""
from zmlx.config.alg import settings
from zml import Seepage, Interp1

# 存储的text
text_key = 'sand_settings'


def get_settings(model: Seepage):
    """
    读取设置
    """
    return settings.get(model, text_key=text_key)


def set_settings(model: Seepage, data):
    """
    写入设置
    """
    return settings.put(model, data=data, text_key=text_key)


def add_setting(model: Seepage, *, sol_sand, flu_sand, v2q, fid):
    """
    添加设置
    """
    return settings.add(model, text_key=text_key,
                        sol_sand=sol_sand, flu_sand=flu_sand, v2q=v2q, fid=fid)


def iterate(model: Seepage, last_dt):
    """
    更新砂
    """
    for item in get_settings(model):
        assert isinstance(item, dict)

        sol_sand = item.get('sol_sand')
        flu_sand = item.get('flu_sand')
        v2q = item.get('v2q')
        fid = item.get('fid')

        # 计算此刻的速度
        vel = model.get_cell_flu_vel(fid=fid, last_dt=last_dt)

        # 更新砂
        model.update_sand(sol_sand=sol_sand, flu_sand=flu_sand, dt=last_dt,
                          v2q=Interp1(x=v2q[0], y=v2q[1]),
                          vel=vel)
