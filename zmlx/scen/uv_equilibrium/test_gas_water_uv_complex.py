from gas_water_uv_equilibrium import GasWaterUVEquilibrium


DATABASE_REQUESTED = "supcrtbl"
CANDIDATE_GASES = ("He", "N2", "H2", "CH4", "CO2")


def total_before(case, comp):
    return case["aq_gas_kg"].get(comp, 0.0) + case["gas_kg"].get(comp, 0.0)


def total_after(result, comp):
    return result["aq_gas_kg"].get(comp, 0.0) + result["gas_kg"].get(comp, 0.0)


def relerr(a, b):
    return abs(a - b) / max(abs(b), 1e-30)


def make_case(multiplier=1.0):
    return {
        "water_kg": 1.0,
        "aq_gas_kg": {
            "He": 2.0e-8 * multiplier,
            "N2": 2.0e-5 * multiplier,
            "H2": 1.0e-6 * multiplier,
            "CH4": 5.0e-6 * multiplier,
            "CO2": 2.0e-4 * multiplier,
        },
        "gas_kg": {
            "He": 5.0e-8 * multiplier,
            "N2": 8.0e-4 * multiplier,
            "H2": 1.0e-4 * multiplier,
            "CH4": 4.0e-4 * multiplier,
            "CO2": 2.0e-3 * multiplier,
        },
    }


def print_result(title, eq, case, result):
    print("\n" + "=" * 90)
    print(title)
    print("=" * 90)
    print("请求数据库:", eq.requested_database_name)
    print("实际数据库:", eq.database_used)
    print("组分映射:", eq.describe()["aqueous_species_map"], eq.describe()["gas_species_map"])

    if not result["success"]:
        print("计算失败:", result["error"])
        print("诊断信息:", result.get("diagnostics", {}))
        return

    print(f"平衡温度: {result['temperature_K']:.6g} K")
    print(f"平衡压力: {result['pressure_Pa']:.6g} Pa")

    d = result["diagnostics"]
    print(f"V0: {d['V0_m3']:.6e} m3, V: {d['V_final_m3']:.6e} m3, dV: {d['volume_error_m3']:.3e} m3")
    print(f"U0: {d['U0_J']:.6e} J,  U: {d['U_final_J']:.6e} J,  dU: {d['internal_energy_error_J']:.3e} J")

    print("\n气体分配与组分质量检查：")
    print(f"{'气体':<8s} {'初始总/kg':>14s} {'水相/kg':>14s} {'气相/kg':>14s} {'最终总/kg':>14s} {'相对误差':>12s}")
    print("-" * 84)
    for comp in CANDIDATE_GASES:
        b = total_before(case, comp)
        aq = result["aq_gas_kg"].get(comp, 0.0)
        gas = result["gas_kg"].get(comp, 0.0)
        a = aq + gas
        print(f"{comp:<8s} {b:14.6e} {aq:14.6e} {gas:14.6e} {a:14.6e} {relerr(a, b):12.3e}")

    print("\n水：")
    print("H2O(aq) =", f"{result['all_species_kg'].get('H2O(aq)', 0.0):.6e}", "kg")
    print("H2O(g)  =", f"{result['all_species_kg'].get('H2O(g)', 0.0):.6e}", "kg")


def main():
    # 一次性初始化，包含 CH4。若 supcrtbl 不含 CH4(aq)，会自动 fallback 到 supcrtbl-organics。
    eq = GasWaterUVEquilibrium(
        database_name=DATABASE_REQUESTED,
        gas_components=CANDIDATE_GASES,
        include_water_vapor=True,
        epsilon=1.0e-30,
        auto_use_organics=True,
    )

    print("初始化成功")
    print("配置:", eq.describe())

    # 算例 1：常规多气体 UV 平衡。
    case1 = make_case(multiplier=1.0)
    result1 = eq.solve(
        temperature_K=298.15,
        pressure_Pa=10.0e6,
        water_kg=case1["water_kg"],
        aq_gas_kg=case1["aq_gas_kg"],
        gas_kg=case1["gas_kg"],
        fixed_volume_m3=None,
        temperature_bounds_K=(273.15, 800.0),
        pressure_bounds_Pa=(1.0e5, 200.0e6),
    )
    print_result("算例 1：He-N2-H2-CH4-CO2，多气体自洽体积 UV 平衡", eq, case1, result1)

    # 算例 2：高气量。
    case2 = make_case(multiplier=5.0)
    result2 = eq.solve(
        temperature_K=323.15,
        pressure_Pa=20.0e6,
        water_kg=case2["water_kg"],
        aq_gas_kg=case2["aq_gas_kg"],
        gas_kg=case2["gas_kg"],
        fixed_volume_m3=None,
        temperature_bounds_K=(273.15, 1000.0),
        pressure_bounds_Pa=(1.0e5, 500.0e6),
    )
    print_result("算例 2：高气量多气体自洽体积 UV 平衡", eq, case2, result2)

    # 算例 3：外部孔隙体积约束。
    if result2["success"]:
        fixed_volume = result2["diagnostics"]["V0_m3"] * 0.95
        result3 = eq.solve(
            temperature_K=323.15,
            pressure_Pa=20.0e6,
            water_kg=case2["water_kg"],
            aq_gas_kg=case2["aq_gas_kg"],
            gas_kg=case2["gas_kg"],
            fixed_volume_m3=fixed_volume,
            temperature_bounds_K=(273.15, 1200.0),
            pressure_bounds_Pa=(1.0e5, 1000.0e6),
        )
        print_result("算例 3：外部孔隙体积约束，V = 0.95 V0(case2)", eq, case2, result3)


if __name__ == "__main__":
    main()
