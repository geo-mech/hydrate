# Gas-Aqueous Migration Batch Inference and Conservation Design

## Scope

Change `zmlx/scen/uv_equilibrium/tests/gas_aq_mig.py` so one PyTorch call
processes all equilibrium-active cells in a time step. Preserve the current
checkpoint, scalar Reaktoro fallback, backend selection, and periodic Reaktoro
anchor behavior.

## Batch Data Flow

1. Read pressure, aqueous temperature, and all phase masses through
   `as_numpy(model)`.
2. Assemble one `N x 8` mass matrix for the active cells in `SPECIES_NAMES`
   order.
3. Build the complete `N x 10` scale-invariant feature matrix with NumPy
   broadcasting.
4. Run the surrogate network once with an `N x 10` tensor.
5. Decode the `N x 6` prediction to temperature, pressure, and an `N x 8`
   phase-mass matrix.
6. Write complete NumPy arrays back to ZMLX. No Python loop may iterate over
   surrogate cells; a small fixed loop over the four components or fluid names
   is acceptable.

In hybrid mode, in-domain cells share one surrogate batch. Out-of-domain cells
and periodic anchor steps continue to use Reaktoro because that solver exposes
only a scalar state interface. Reaktoro work may remain in the existing thread
pool.

## Conservation Rules

For every cell and each component `H2O`, `CH4`, `N2`, and `He`, capture the
pre-equilibrium total:

`component_total = gas_mass + aqueous_mass`

After surrogate or Reaktoro calculation, sanitize non-finite and negative phase
masses, then project the phase split back onto the captured component total.
Use the predicted gas fraction when the predicted phase sum is positive;
otherwise retain a valid zero-gas split. Set aqueous mass as
`component_total - gas_mass` so the corrected sum is exact up to floating-point
roundoff.

Measure the maximum per-cell absolute and relative error before and after the
projection. Corrections are automatic and do not stop the simulation.

Store the model-wide component totals when the model is created or first seen.
At each balance call, compare current totals with this baseline. This global
diagnostic reports transport-related drift but does not rescale the model,
because future boundary conditions or sources may legitimately change global
mass.

## Diagnostics

Keep the latest conservation report in module state for programmatic access.
Print one concise report at initialization, at the configured report interval,
or when correction exceeds tolerance. The report includes initial/current total
and relative drift for all four components, plus the maximum local correction.

## Error Handling

- Empty active-cell selections return without invoking PyTorch.
- Invalid phase-mass outputs are replaced during conservation projection;
  invalid temperatures retain the pre-equilibrium cell temperature.
- A failed Reaktoro cell keeps its pre-equilibrium state.
- Shape mismatches raise a clear `ValueError` before model data is changed.

## Verification

- A fake batch model proves that one network forward call receives all active
  cells.
- Batch predictions match the existing scalar surrogate on representative
  states.
- Deliberately non-conservative and invalid predictions are projected to exact
  per-cell totals for all four components.
- A small ZMLX model preserves component totals through `balance`.
- Existing backend, anchor, checkpoint replay, and migration tests continue to
  pass.
