#!/usr/bin/env python
"""PARDISO 求解器测试（正确性验证）."""

import time
from ctypes import c_double, c_int

import numpy as np


def _make_arrays(n, triplets):
    nnz = len(triplets)
    rows = (c_int * nnz)()
    cols = (c_int * nnz)()
    vals = (c_double * nnz)()
    for i, (r, c, v) in enumerate(triplets):
        rows[i] = r
        cols[i] = c
        vals[i] = v
    x = (c_double * n)()
    b = (c_double * n)()
    return rows, cols, vals, x, b


def _poisson2d_triplets(gx, gy):
    n = gx * gy
    def idx(i, j): return i * gy + j
    triplets = []
    for i in range(gx):
        for j in range(gy):
            k = idx(i, j)
            triplets.append((k, k, 4.0))
            if i > 0: triplets.append((k, idx(i - 1, j), -1.0))
            if i < gx - 1: triplets.append((k, idx(i + 1, j), -1.0))
            if j > 0: triplets.append((k, idx(i, j - 1), -1.0))
            if j < gx - 1: triplets.append((k, idx(i, j + 1), -1.0))
    return n, triplets


def _residual(n, triplets, x, b):
    r = np.zeros(n)
    for row, col, val in triplets:
        r[row] += val * x[col]
    return np.max(np.abs(r - np.array([b[i] for i in range(n)])))


def test_small_spd():
    """2x2 SPD 矩阵正确性测试."""
    print('=' * 60)
    print('  2x2 SPD 正确性测试')
    print('=' * 60)

    from zmlx.exts.pardiso import PARDISOSolver

    # A = [[4, -1], [-1, 4]], b = [1, 2], expected x = [0.4, 0.6]
    n = 2
    triplets = [(0, 0, 4.0), (0, 1, -1.0), (1, 0, -1.0), (1, 1, 4.0)]
    rows, cols, vals, x, b = _make_arrays(n, triplets)
    b[0] = 1.0; b[1] = 2.0

    par = PARDISOSolver(mtype=-2)
    err = par.solve(rows, cols, vals, x, b)
    assert err == 0, f'PARDISO failed: {err}'
    print(f'  PARDISO: x=[{x[0]:.6f}, {x[1]:.6f}]')

    assert abs(x[0] - 0.4) < 1e-10
    assert abs(x[1] - 0.6) < 1e-10

    r = _residual(n, triplets, x, b)
    print(f'  max|Ax-b| = {r:.2e}')
    assert r < 1e-10
    print('  OK 通过\n')


def test_fn_ctx():
    """fn/ctx 属性测试."""
    print('=' * 60)
    print('  fn/ctx 属性测试')
    print('=' * 60)

    from zmlx.exts.pardiso import PARDISOSolver
    par = PARDISOSolver()
    assert par.fn is not None
    assert par.ctx == par.handle
    print(f'  fn={par.fn}, ctx={par.ctx}')
    print('  OK 通过\n')


def main():
    test_small_spd()
    test_fn_ctx()
    print('=' * 60)
    print('  全部测试通过')
    print('=' * 60)


if __name__ == '__main__':
    main()
