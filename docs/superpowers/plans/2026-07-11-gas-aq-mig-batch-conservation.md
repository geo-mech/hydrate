# Gas-Aqueous Migration Batch Inference Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace per-cell PyTorch calls in `gas_aq_mig.py` with one vectorized call per time step and enforce gas-plus-aqueous mass conservation for H2O, CH4, N2, and He.

**Architecture:** Keep ZMLX state access as NumPy arrays and add local batch feature, inference, decode, and conservation helpers to `gas_aq_mig.py`. Surrogate cells use one `N x 10` tensor; only scalar Reaktoro anchors and out-of-domain fallbacks retain threaded iteration. Project every returned phase split onto its pre-equilibrium component totals, and retain an initial model-wide reference for drift reporting.

**Tech Stack:** Python, NumPy, PyTorch, ZMLX, Reaktoro, pytest-style function tests

---

### Task 1: Vectorized surrogate inference

**Files:**
- Modify: `zmlx/scen/uv_equilibrium/tests/gas_aq_mig.py`
- Test: `zmlx/scen/uv_equilibrium/tests/test_gas_aq_mig_surrogate.py`

- [ ] **Step 1: Write a failing one-forward-call test**

Add a counting `torch.nn.Module` and call the wished-for batch API with three states:

```python
class CountingNet(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.calls = 0

    def forward(self, values):
        self.calls += 1
        result = torch.zeros((len(values), 6), dtype=values.dtype)
        result[:, 2:] = 0.25
        return result


def test_surrogate_batch_uses_one_network_forward_for_all_cells():
    net = CountingNet()
    solver = SimpleNamespace(model=net)
    temperature = np.array([300.0, 330.0, 360.0])
    pressure = np.array([10.0e6, 20.0e6, 30.0e6])
    masses = np.array([
        [0.0, 3.0, 0.5, 0.01, 100.0, 0.2, 0.05, 0.001],
        [0.0, 2.0, 0.4, 0.02, 120.0, 0.3, 0.04, 0.002],
        [0.0, 1.0, 0.3, 0.03, 140.0, 0.4, 0.03, 0.003],
    ])

    next_temperature, _, result = mig._solve_surrogate_batch(
        solver, temperature, pressure, masses
    )

    assert net.calls == 1
    assert next_temperature.shape == (3,)
    assert result.shape == (3, 8)
```

- [ ] **Step 2: Run the focused test and verify red**

Run:

```powershell
C:\Users\Lyx\conda_envs\rkt\python.exe -m pytest zmlx/scen/uv_equilibrium/tests/test_gas_aq_mig_surrogate.py::test_surrogate_batch_uses_one_network_forward_for_all_cells -q
```

Expected: failure because `_solve_surrogate_batch` does not exist.

- [ ] **Step 3: Implement vectorized feature construction and inference**

Add `_batch_features` and `_solve_surrogate_batch` to `gas_aq_mig.py`. Build totals with `masses[:, :4] + masses[:, 4:]`, populate `features[:, 2::2]` with log-scaled component fractions, and `features[:, 3::2]` with gas fractions. Invoke the network once:

```python
with torch.inference_mode():
    prediction = solver.model(torch.from_numpy(features)).cpu().numpy()
```

Decode all rows with broadcasting:

```python
gas = totals * np.clip(prediction[:, 2:6], 0.0, 1.0)
result = np.concatenate((gas, totals - gas), axis=1)
```

Validate input shapes before inference and return empty arrays without calling the network when `N == 0`.

- [ ] **Step 4: Verify green and scalar parity**

Add a test loading the existing checkpoint, comparing batch rows against repeated existing scalar `solve` results with `np.testing.assert_allclose`, then run the complete migration test module.

### Task 2: Four-component conservation projection

**Files:**
- Modify: `zmlx/scen/uv_equilibrium/tests/gas_aq_mig.py`
- Test: `zmlx/scen/uv_equilibrium/tests/test_gas_aq_mig_surrogate.py`

- [ ] **Step 1: Write failing projection tests**

Use deliberately non-conservative, negative, and non-finite output masses. Assert each row preserves all four input totals:

```python
corrected, report = mig._project_component_totals(before, predicted)
np.testing.assert_allclose(
    corrected[:, :4] + corrected[:, 4:],
    before[:, :4] + before[:, 4:],
    rtol=0.0,
    atol=1.0e-12,
)
assert np.isfinite(corrected).all()
assert (corrected >= 0.0).all()
assert report["max_raw_relative_error"] > 0.0
assert report["max_corrected_relative_error"] <= 1.0e-12
```

- [ ] **Step 2: Run the focused test and verify red**

Expected: failure because `_project_component_totals` does not exist.

- [ ] **Step 3: Implement automatic projection**

Sanitize predicted phase masses, calculate their gas share, and reconstruct each component from the pre-equilibrium totals. Calculate raw and corrected maximum absolute/relative errors over every row and all four components.

- [ ] **Step 4: Run focused and existing conservation tests**

Run both the new projection test and `test_surrogate_backend_preserves_component_mass_totals`; expected result is pass.

### Task 3: Integrate one-batch balance and hybrid fallback

**Files:**
- Modify: `zmlx/scen/uv_equilibrium/tests/gas_aq_mig.py`
- Test: `zmlx/scen/uv_equilibrium/tests/test_gas_aq_mig_surrogate.py`

- [ ] **Step 1: Write a failing balance routing test**

Replace the batch surrogate helper with a recorder, run `balance` on a small model, and assert the recorder receives all active cell rows in one call. Also assert no call to `_solve_cell` occurs for an all-in-domain pure-surrogate step.

- [ ] **Step 2: Verify the routing test fails against the current loop**

Expected: `_solve_cell` is called through `_pool.map`, or the batch recorder is never called.

- [ ] **Step 3: Implement batch routing**

Replace the generator and `_pool.map` path in `balance` with an `N x 8` mass matrix and `_solve_balance_batch`:

```python
if backend_is_surrogate:
    next_t, next_p, predicted = _solve_surrogate_batch(...)
elif hybrid_non_anchor:
    # One surrogate call for the complete in-domain mask.
    # Threaded Reaktoro only for the complementary mask.
else:
    # Threaded Reaktoro for the anchor or Reaktoro backend.
```

Project all successful outputs before writing phase masses. Failed Reaktoro rows retain their prior masses and temperature.

- [ ] **Step 4: Verify batch routing and anchor behavior**

Run the migration test module. Existing `_anchor_due` and hybrid fallback tests must remain green.

### Task 4: Initial/global mass diagnostics

**Files:**
- Modify: `zmlx/scen/uv_equilibrium/tests/gas_aq_mig.py`
- Test: `zmlx/scen/uv_equilibrium/tests/test_gas_aq_mig_surrogate.py`

- [ ] **Step 1: Write a failing global-report test**

Create two sets of fluid arrays with known totals and assert the report contains `initial`, `current`, and `relative_drift` values for H2O, CH4, N2, and He. Verify the latest report can be retrieved by model key.

- [ ] **Step 2: Verify red**

Expected: failure because reference/report helpers do not exist.

- [ ] **Step 3: Implement model references and concise reporting**

Store references by `model.handle_str`, initialize them in `create` or on first `balance`, and expose `get_mass_conservation_report(model)`. Print at initialization, every `GAS_AQ_MASS_REPORT_INTERVAL` calls, or when the local raw correction exceeds `GAS_AQ_MASS_TOLERANCE`.

- [ ] **Step 4: Verify diagnostics do not modify transport totals**

Assert the report observes global drift but does not rescale arrays. Local equilibrium outputs must still be automatically projected.

### Task 5: Full verification

**Files:**
- Verify: `zmlx/scen/uv_equilibrium/tests/gas_aq_mig.py`
- Verify: `zmlx/scen/uv_equilibrium/tests/test_gas_aq_mig_surrogate.py`
- Verify: `zmlx/scen/uv_equilibrium/tests/test_train_gas_aq_uv_surrogate.py`

- [ ] **Step 1: Compile changed modules**

Run `python -m compileall` for the migration and surrogate modules; expected exit code is zero.

- [ ] **Step 2: Run relevant regression tests**

Run the migration, training, equilibrium, and minimal-script test modules; expected result is zero failures.

- [ ] **Step 3: Run a real-checkpoint batch comparison**

Load the Round5 checkpoint, solve representative states by scalar and batch paths, and report maximum temperature and phase-mass differences.

- [ ] **Step 4: Run a small ZMLX model balance**

Create a small model, run one pure-surrogate balance, and verify all four model-wide totals before and after are equal within `rtol=1e-12` and `atol=1e-12`.

- [ ] **Step 5: Inspect the final diff**

Run `git diff --check` and confirm no unrelated user changes were altered.
