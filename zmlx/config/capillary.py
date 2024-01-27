"""
用于管理毛管压力驱动下的流动
"""
from zml import Vector, Seepage, Interp1, parse_fid3

vs0 = Vector()
vk = Vector()
vg = Vector()
vpg = Vector()


def iterate(model: Seepage, dt: float, fid0=None, fid1=None, ca_ipc=None, ds=0.05):
    """
    在毛管力驱动下的流动
    """
    if dt <= 1.0e-30:
        return
    if fid0 is not None and fid1 is not None and ca_ipc is not None:
        model.get_linear_dpre(fid0=fid0, fid1=fid1, ca_ipc=ca_ipc, vs0=vs0, vk=vk, ds=ds, cell_ids=None)
        model.get_cond_for_exchange(fid0=fid0, fid1=fid1, buffer=vg)
        model.diffusion(dt, fid0=fid0, fid1=fid1, vs0=vs0, vk=vk, vg=vg, vpg=vpg)
    else:
        buf = model.get_buffer('cap_settings')
        ind = 0
        while ind + 6 < buf.size:
            a0 = round(buf[ind + 0])
            b0 = round(buf[ind + 1])
            c0 = round(buf[ind + 2])
            a1 = round(buf[ind + 3])
            b1 = round(buf[ind + 4])
            c1 = round(buf[ind + 5])
            ca_ipc = round(buf[ind + 6])
            ind += 7
            iterate(model=model, dt=dt, fid0=(a0, b0, c0), fid1=(a1, b1, c1), ca_ipc=ca_ipc, ds=ds)


def add(model: Seepage, fid0, fid1, get_idx, data):
    """
    创建一个毛管压力计算模型，其中fid0和fid1为涉及的两种流体。毛管压力定义为fid0的压力减去fid1的压力。model为创建好的渗流模型（或者Mesh）.
        idx = get_idx(x, y, z)
    是一个函数，该函数返回给定位置所需要采用的毛管压力曲线的ID，注意这个ID从0开始编号.
    后续的所有参数为毛管压力曲线，可以是Interp1类型，也可以给定两个list.
    """
    buf = model.get_buffer('cap_settings')
    assert buf.size % 7 == 0
    count = buf.size // 7
    ca_ipc = model.reg_cell_key(f'ipc_{count}')

    ipcs = []
    for curve_id in range(len(data)):
        if isinstance(data[curve_id], Interp1):
            idx = model.add_pc(data[curve_id], need_id=True)
            ipcs.append(idx)
            continue
        if isinstance(data[curve_id], str):
            idx = model.add_pc(_s2p(data[curve_id]), need_id=True)
            ipcs.append(idx)
            continue
        else:
            s, p = data[curve_id]
            assert len(s) == len(p) and len(s) >= 2
            for i in range(1, len(s)):
                assert s[i - 1] < s[i]
                assert p[i - 1] < p[i]
            s2p = Interp1(x=s, y=p)
            idx = model.add_pc(s2p, need_id=True)
            ipcs.append(idx)

    for cell_id in range(model.cell_number):
        idx = round(get_idx(*model.get_cell(cell_id).pos))
        assert 0 <= idx < len(data)
        ipc = ipcs[idx]
        model.get_cell(cell_id).set_attr(ca_ipc, ipc)

    if isinstance(fid0, str):
        fid0 = model.find_fludef(fid0)

    ia, ib, ic = parse_fid3(fid0)
    buf.append(ia)
    buf.append(ib)
    buf.append(ic)

    if isinstance(fid1, str):
        fid1 = model.find_fludef(fid1)

    ia, ib, ic = parse_fid3(fid1)
    buf.append(ia)
    buf.append(ib)
    buf.append(ic)

    buf.append(ca_ipc)


def _s2p(text):
    """
    根据文本来创建从饱和度到毛管压力的插值
    """
    vv = [[float(w) for w in line.split()] for line in text.splitlines() if len(line) > 2]
    s = [v[0] for v in vv]
    p = [v[1] for v in vv]
    assert len(s) == len(p) and len(s) >= 2
    for i in range(1, len(s)):
        assert s[i - 1] < s[i]
        assert p[i - 1] < p[i]
    return Interp1(x=s, y=p)
