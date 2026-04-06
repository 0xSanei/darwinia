"""
Tests for darwinia.integrations — SkillBridge and SkillRegistry.
"""

import unittest
import numpy as np

from darwinia.integrations.skill_bridge import (
    SkillBridge,
    SkillRegistry,
    INTEGRATION_TEMPLATES,
    IntegrationTemplate,
)


class TestSkillBridgeEvolve(unittest.TestCase):
    """Test SkillBridge.evolve() returns valid structure."""

    def test_evolve_returns_required_keys(self):
        bridge = SkillBridge()
        # Generate synthetic candles: (N, 6) — ts, open, high, low, close, volume
        np.random.seed(42)
        n = 200
        closes = 100 + np.cumsum(np.random.randn(n) * 0.5)
        candles = np.column_stack([
            np.arange(n),          # timestamp
            closes - 0.3,          # open
            closes + 0.5,          # high
            closes - 0.5,          # low
            closes,                # close
            np.random.rand(n) * 1000,  # volume
        ])

        result = bridge.evolve({
            "generations": 3,
            "population_size": 10,
            "data": candles,
        })

        self.assertIsInstance(result, dict)
        self.assertIn("champion", result)
        self.assertIn("evolution_summary", result)
        self.assertIn("patterns", result)

        summary = result["evolution_summary"]
        self.assertEqual(summary["generations_run"], 3)
        self.assertEqual(summary["population_size"], 10)
        self.assertIn("final_champion_fitness", summary)
        self.assertIn("genetic_diversity", summary)


class TestSkillBridgeEvaluateStrategy(unittest.TestCase):
    """Test SkillBridge.evaluate_strategy() with known DNA."""

    def setUp(self):
        self.bridge = SkillBridge()
        # Load synthetic data so fitness can be computed
        np.random.seed(42)
        n = 200
        closes = 100 + np.cumsum(np.random.randn(n) * 0.5)
        candles = np.column_stack([
            np.arange(n),
            closes - 0.3,
            closes + 0.5,
            closes - 0.5,
            closes,
            np.random.rand(n) * 1000,
        ])
        # Run a minimal evolution to load data
        self.bridge.evolve({
            "generations": 2,
            "population_size": 10,
            "data": candles,
        })

    def test_evaluate_known_dna(self):
        # 17 genes, all at midpoint
        dna = [0.5] * 17
        result = self.bridge.evaluate_strategy(dna)

        self.assertIsInstance(result, dict)
        self.assertIn("genes", result)
        self.assertIn("fitness", result)
        self.assertIsNotNone(result["fitness"])
        self.assertEqual(len(result["genes"]), 17)

    def test_evaluate_rejects_wrong_length(self):
        with self.assertRaises(ValueError):
            self.bridge.evaluate_strategy([0.5] * 10)

    def test_evaluate_without_data(self):
        fresh = SkillBridge()
        dna = [0.5] * 17
        result = fresh.evaluate_strategy(dna)
        # Should succeed but fitness is None (no data)
        self.assertIsNone(result["fitness"])
        self.assertIn("note", result)


class TestSkillBridgeMarketRegime(unittest.TestCase):
    """Test SkillBridge.get_market_regime()."""

    def test_regime_after_evolve(self):
        bridge = SkillBridge()
        np.random.seed(42)
        n = 200
        closes = 100 + np.cumsum(np.random.randn(n) * 0.5)
        candles = np.column_stack([
            np.arange(n),
            closes - 0.3,
            closes + 0.5,
            closes - 0.5,
            closes,
            np.random.rand(n) * 1000,
        ])
        bridge.evolve({"generations": 2, "population_size": 10, "data": candles})

        regime = bridge.get_market_regime()
        self.assertIsInstance(regime, dict)
        self.assertIn("regime", regime)
        self.assertIn("confidence", regime)
        self.assertIn("momentum", regime)
        self.assertIn("volatility", regime)
        self.assertIn("trend_strength", regime)
        # regime should be a valid enum value string
        valid_regimes = {"trending_up", "trending_down", "ranging", "volatile", "breakout"}
        self.assertIn(regime["regime"], valid_regimes)

    def test_regime_without_data_raises(self):
        bridge = SkillBridge()
        with self.assertRaises(RuntimeError):
            bridge.get_market_regime()


class TestSkillRegistry(unittest.TestCase):
    """Test SkillRegistry register / call / list."""

    def setUp(self):
        self.registry = SkillRegistry()

    def test_register_and_list(self):
        self.registry.register("test-skill", lambda: {"ok": True})
        self.assertIn("test-skill", self.registry.list_skills())

    def test_call_registered_skill(self):
        self.registry.register("echo", lambda msg="hi": {"echo": msg})
        result = self.registry.call("echo", msg="hello")
        self.assertEqual(result, {"echo": "hello"})

    def test_call_unregistered_raises(self):
        with self.assertRaises(KeyError):
            self.registry.call("nonexistent")

    def test_register_non_callable_raises(self):
        with self.assertRaises(TypeError):
            self.registry.register("bad", "not_a_function")

    def test_unregister(self):
        self.registry.register("temp", lambda: {})
        self.registry.unregister("temp")
        self.assertNotIn("temp", self.registry.list_skills())

    def test_has_skill(self):
        self.registry.register("x", lambda: {})
        self.assertTrue(self.registry.has_skill("x"))
        self.assertFalse(self.registry.has_skill("y"))

    def test_call_log(self):
        self.registry.register("log-test", lambda: {"v": 1})
        self.registry.call("log-test")
        log = self.registry.get_call_log()
        self.assertEqual(len(log), 1)
        self.assertEqual(log[0]["skill"], "log-test")


class TestIntegrationTemplates(unittest.TestCase):
    """Test that built-in integration templates exist and are well-formed."""

    def test_required_templates_exist(self):
        expected = {"macro-liquidity", "crypto-market-rank", "okx-dex-market"}
        self.assertEqual(expected, set(INTEGRATION_TEMPLATES.keys()))

    def test_templates_are_correct_type(self):
        for name, tmpl in INTEGRATION_TEMPLATES.items():
            self.assertIsInstance(tmpl, IntegrationTemplate, f"{name} is not IntegrationTemplate")

    def test_templates_have_required_fields(self):
        for name, tmpl in INTEGRATION_TEMPLATES.items():
            self.assertTrue(tmpl.name, f"{name} missing name")
            self.assertTrue(tmpl.description, f"{name} missing description")
            self.assertIsInstance(tmpl.input_schema, dict, f"{name} input_schema not dict")
            self.assertIsInstance(tmpl.output_schema, dict, f"{name} output_schema not dict")
            self.assertTrue(tmpl.hook_point, f"{name} missing hook_point")

    def test_template_to_dict(self):
        tmpl = INTEGRATION_TEMPLATES["macro-liquidity"]
        d = tmpl.to_dict()
        self.assertEqual(d["name"], "macro-liquidity")
        self.assertIn("input_schema", d)
        self.assertIn("output_schema", d)

    def test_bridge_get_templates(self):
        bridge = SkillBridge()
        templates = bridge.get_integration_templates()
        self.assertEqual(len(templates), 3)
        for name, t in templates.items():
            self.assertIn("hook_point", t)

    def test_registry_list_templates(self):
        registry = SkillRegistry()
        names = registry.list_templates()
        self.assertEqual(len(names), 3)
        self.assertIn("macro-liquidity", names)

    def test_registry_get_template(self):
        registry = SkillRegistry()
        t = registry.get_template("okx-dex-market")
        self.assertIsNotNone(t)
        self.assertEqual(t["name"], "okx-dex-market")
        self.assertIsNone(registry.get_template("nonexistent"))


if __name__ == "__main__":
    unittest.main()
