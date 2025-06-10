import numpy as np
import codecs

# 1. 读取 tdat 文件（Latin-1 编码）
with codecs.open('thermo_data.tdat', 'r', 'latin-1') as f:
    lines = [line.rstrip('\n') for line in f]

# 2. 找到包含给定反应物的反应条目
reactants = ['Ca++', 'CO3--']
target_block = None
for i, line in enumerate(lines):
    if 'species in reaction' in line:
        # 解析化学计量行，提取正计量的物种名
        parts = line.split()
        try:
            n = int(parts[0])
        except:
            continue
        # 回溯寻找反应名称行
        name_line = None
        k = i - 1
        while k >= 0:
            if lines[k].strip() == '' or lines[k].startswith('*') or lines[k].startswith(' '):
                k -= 1
            else:
                name_line = lines[k].strip()
                break
        # 提取物种列表
        species_tokens = []
        m = i+1
        while m < len(lines) and len(species_tokens)//2 < n:
            tokens = lines[m].strip().split()
            species_tokens.extend(tokens)
            m += 1
        species = [species_tokens[j*2+1] for j in range(n)]
        # 检查是否包含反应物列表（兼容 CO3-- 与 HCO3-）
        names = [s for s in species if float(species_tokens[2*species.index(s)]) > 0]
        if 'Ca++' in names and any(sp in names for sp in ['CO3--','HCO3-']):
            target_block = (name_line, species_tokens, m)
            break

# 3. 解析目标反应的 logK 数据
if target_block:
    name_line, species_tokens, m = target_block
    # 从 m 行开始取出后续的 logK 数值
    log10K_values = []
    while len(log10K_values) < 8 and m < len(lines):
        nums = [float(x) for x in lines[m].split() if x.replace('.','',1).replace('-','',1).isdigit()]
        log10K_values.extend(nums)
        m += 1
    log10K = np.array(log10K_values[:8])
    T_C = np.array([0,25,60,100,150,200,250,300])
    T_K = T_C + 273.15
    K_vals = 10**log10K

    # 4. 拟合 Van't Hoff 曲线
    invT = 1.0/T_K
    lnK = np.log(K_vals)
    slope, intercept = np.polyfit(invT, lnK, 1)
    # 任意温度计算 K(T) 和归一化 k(T)
    T_query = np.linspace(273.15, 573.15, 101)  # 0°C 到 300°C
    lnK_query = intercept + slope*(1.0/T_query)
    K_query = np.exp(lnK_query)
    k_norm = K_query / np.max(K_query)

    # 5. 输出结果（表格和图形）
    print("T(°C)\tlog10K\tK\tk_norm")
    for Tc, lnKv, Kv, kn in zip(T_query-273.15, lnK_query/np.log(10), K_query, k_norm):
        print(f"{Tc:.0f}\t{(lnKv):.2f}\t{Kv:.2e}\t{kn:.3f}")
