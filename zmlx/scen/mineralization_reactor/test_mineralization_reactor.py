import math
import importlib.util
import sys
import unittest
from pathlib import Path


def ensure_hydrate_root():
    root = str(Path(__file__).resolve().parents[3])
    if root not in sys.path:
        sys.path.insert(0, root)
    return root


ensure_hydrate_root()

from zmlx.tfc import iterate
from zmlx.scen import mineralization_reactor as mineral


class MineralizationReactorTests(unittest.TestCase):
    def test_interface_matches_teacher_contract(self):
        reactor = mineral.Co2StorageMineral(scene='saline_aquifer', surface_area=1.0e-3)
        text = reactor.to_text()
        restored = mineral.Mineralization.from_text(text)

        self.assertTrue(callable(restored.list_fluid_names))
        self.assertTrue(callable(restored.calc_next_state))
        self.assertTrue(callable(restored.to_text))
        self.assertIn('ca', restored.list_fluid_names())
        self.assertIn('co2_aq', restored.list_fluid_names())
        self.assertIn('calcite', restored.list_fluid_names())
        self.assertIsInstance(restored, mineral.Co2StorageMineral)
        self.assertEqual(restored.scene, 'saline_aquifer')

    def test_from_text_supports_scene_presets_and_key_value_config(self):
        permafrost = mineral.Mineralization.from_text('permafrost')
        seabed = mineral.Mineralization.from_text('scene=seabed;sa=0.002')
        basalt = mineral.Mineralization.from_text('{"model":"co2_storage_mineral","scene":"basalt"}')

        self.assertEqual(permafrost.scene, 'permafrost')
        self.assertEqual(seabed.scene, 'seabed')
        self.assertTrue(math.isclose(seabed.surface_area, 0.002))
        self.assertEqual(basalt.scene, 'basalt')
        self.assertNotEqual(
            mineral.scene_state('permafrost')['Na+'],
            mineral.scene_state('basalt')['Na+'])

    def test_reaktoro_reactor_advances_state_dictionary(self):
        reactor = mineral.Co2StorageMineral(surface_area=1.0e-3)
        state0 = dict(mineral.DEFAULT_STATE)
        state0['CO2(aq)'] = 1.6e-3
        state1 = reactor.calc_next_state(
            current_state=state0,
            time_step=600.0,
            temperature=298.15,
            pressure=1.0e7)

        self.assertEqual(state1['reaktoro_succeeded'], 1.0)
        self.assertTrue(math.isfinite(state1['pH']))
        self.assertIn('Ca+2', state1)
        self.assertIn('Mg+2', state1)
        self.assertIn('Calcite_delta_kg', state1)
        self.assertNotEqual(state1['Ca+2'], state0['Ca+2'])

    def test_seepage_callback_uses_text_config_and_component_names(self):
        model = mineral.create(shape=(1, 1, 1))
        cell = model.get_cell(0)
        ca = mineral.component(cell, 'ca')
        calcite = mineral.component(cell, 'calcite')
        ca0 = ca.mass
        calcite0 = calcite.mass

        changed = mineral.mineralization_reaction(model, time_step=600.0)
        state = mineral.state_from_cell(cell)
        keys = mineral.key_fields(model)

        self.assertEqual(changed, 1)
        self.assertEqual(cell.get_attr(keys['reaktoro_succeeded']), 1.0)
        self.assertNotEqual(ca.mass, ca0)
        self.assertNotEqual(calcite.mass, calcite0)
        self.assertTrue(math.isclose(
            ca.mass,
            state['Ca+2'],
            rel_tol=1.0e-8))
        self.assertIn('co2_storage_mineral', model.get_text('Mineralization'))

    def test_iterate_invokes_registered_callback(self):
        model = mineral.create(shape=(2, 1, 1))
        iterate(model, dt=600.0, slots={'mineralization_reaction': mineral.mineralization_reaction})
        keys = mineral.key_fields(model)

        for cell in model.cells:
            self.assertEqual(cell.get_attr(keys['reaktoro_succeeded']), 1.0)
            self.assertTrue(math.isfinite(cell.get_attr(keys['pH'])))

    def test_seepage_layer_has_no_hard_coded_fluid_ids_or_temps_cache(self):
        text = (Path(__file__).resolve().parent / '_seepage.py').read_text(encoding='utf-8')

        self.assertNotIn('GAS_ID', text)
        self.assertNotIn('LIQ_ID', text)
        self.assertNotIn('SOL_ID', text)
        self.assertNotIn('model.temps', text)
        self.assertNotIn('get_fluid(0', text)
        self.assertIn('find_fludef(name)', text)

    def test_config_file_holds_shared_names_and_defaults(self):
        config_text = (Path(__file__).resolve().parent / '_config.py').read_text(encoding='utf-8')
        reactor_text = (Path(__file__).resolve().parent / '_mineralization.py').read_text(encoding='utf-8')

        self.assertIn('SCENES = {', config_text)
        self.assertIn('COMPONENT_SPECIES = {', config_text)
        self.assertIn("'permafrost'", config_text)
        self.assertIn("'seabed'", config_text)
        self.assertIn("'basalt'", config_text)
        self.assertIn('def component_molar_mass', config_text)
        self.assertIn('def species_formula', config_text)
        self.assertNotIn('MOLAR_MASS = {', config_text)
        self.assertIn("'co2_aq_kg'", config_text)
        self.assertNotIn("'CO2(aq)': species_mass", config_text)
        self.assertLess(mineral.DEFAULT_STATE['Ca+2'], 1.0e-3)
        self.assertLess(mineral.DEFAULT_STATE['Calcite'], 1.0e-3)
        self.assertNotIn("'co2_molal'", config_text)
        self.assertNotIn("'calcite_mol'", config_text)
        self.assertIn('from zmlx.scen.mineralization_reactor._config import', reactor_text)
        self.assertNotIn('STATE_SPECIES =', reactor_text)
        self.assertNotIn('DEFAULT_STATE =', reactor_text)
        self.assertIn("chemical.set(name, _positive(state.get(name, self._default_state[name])), 'kg')", reactor_text)
        self.assertNotIn("chemical.set(name, _positive(state.get(name, self._default_state[name])) * water, 'mol')", reactor_text)

    def test_reaktoro_database_provides_species_properties(self):
        self.assertTrue(mineral.validate_species())
        self.assertTrue(math.isclose(
            mineral.component_molar_mass('ca'),
            mineral.species_molar_mass('Ca+2'),
            rel_tol=1.0e-12))
        self.assertEqual(mineral.species_formula('calcite'), 'CaCO3')
        self.assertEqual(mineral.species_charge('Ca+2'), 2.0)
        self.assertGreater(mineral.mineral_density('calcite'), 2500.0)

    def test_show_uses_igg_hydrate_gui_and_main_can_skip_gui(self):
        folder = Path(__file__).resolve().parent
        show_text = (folder / '_show.py').read_text(encoding='utf-8')
        main_text = (folder / 'main.py').read_text(encoding='utf-8')
        test_text = (folder / 'test_mineralization_reactor.py').read_text(encoding='utf-8')

        self.assertIn('from zmlx.ui import plot', show_text)
        self.assertIn("'tricontourf'", show_text)
        self.assertIn('gui_mode=True', show_text)
        self.assertIn("'co2_aq_kg'", show_text)
        self.assertNotIn("'co2_molal'", show_text)
        self.assertNotIn('matplotlib', show_text + main_text)
        self.assertNotIn('tkinter', show_text + main_text)
        self.assertNotIn(chr(69) + ':' + chr(92), main_text + test_text)

        spec = importlib.util.spec_from_file_location('mineralization_reactor_main', folder / 'main.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        code = module.main(['--nogui', '--nx', '2', '--nz', '2', '--dt', '600'])
        self.assertEqual(code, 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
