"""
基于zmlx.extx.DynSys，实现有限元计算.
"""
from zmlx.fem.dyn import create_dyn  # 创建有限元问题等价的DynSys对象
from zmlx.fem.mesh_utils import enrich_with_mid_nodes, enriched_mesh_from_grid
