"""
Created on Fri Jan 27 19:12:20 2023

@author: Maryelin

Viscosity of Hydrogen in Gaseous and Liquid States for Temperatures Up to 5000° K.
L. I. Stiel and George Thodos
https://pubs.acs.org/doi/abs/10.1021/i160007a014#

"""

def liq_vis_h2(P, T):
    tc = 33.18
    vis = (208e-5 * (T / tc)**0.65) * 0.001
    return vis


