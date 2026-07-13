from zmlx.fem.elements.planar_stress_t6._stiffness import calc_stiffness
from zmlx.fem.elements.planar_stress_t6._strain import calc_strain
from zmlx.fem.elements.planar_stress_t6._stress import calc_stress
from zmlx.fem.mesh_utils import enrich_with_mid_nodes, enriched_mesh_from_grid

# 别名, 弃用
stiffness = calc_stiffness
