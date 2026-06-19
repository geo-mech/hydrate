from gas_water_uv_equilibrium import GasWaterUVEquilibrium

eq = GasWaterUVEquilibrium(
    database_name="supcrtbl",
    gas_components=("He", "N2"),
)

result = eq.solve(
    temperature_K=298.15,
    pressure_Pa=1.0e5,
    water_kg=18.01528,
    aq_gas_kg={
        "He": 4.0026e-3,
        "N2": 28.0134e-3,
    },
    gas_kg={
        "He": 0.0,
        "N2": 0.0,
    },
    temperature_bounds_K=(298.15, 2273.15),
    pressure_bounds_Pa=(1.0e5, 1.0e8),
)

print(result["success"])
print(result["temperature_K"])
print(result["pressure_Pa"])
print(result["aq_gas_kg"])
print(result["gas_kg"])
print(result["diagnostics"])