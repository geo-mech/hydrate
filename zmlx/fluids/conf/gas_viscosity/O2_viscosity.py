# -*- coding: utf-8 -*-
"""O2 气体粘度关联式（Sutherland's law approximation）.

Sutherland's law approximation for gas viscosity.

Modified by Claude, 2026-08-12
"""
# Sutherland's law approximation for gas viscosity:
# https://doc.comsol.com/5.5/doc/com.comsol.help.cfd/cfd_ug_fluidflow_high_mach.08.27.html


def vis_o2(P, T):
    t_ref = 273
    vis_ref = 1.919e-5
    s_ref = 139
    viscosity = vis_ref * (
            (T / t_ref) ** (3 / 2) * ((t_ref + s_ref) / (
            T + s_ref)))  # Sutherlands's equation for ideal gas
    return viscosity
