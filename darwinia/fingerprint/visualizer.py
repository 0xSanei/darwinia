"""
Strategy Fingerprint — unique visual representation of a strategy's DNA.

Creates a genetic fingerprint that makes it easy to compare strategies at a glance.
"""

import math
from typing import Dict, List

from darwinia.core.dna import AgentDNA


# Gene groupings by category
CATEGORIES = {
    "Signal": [
        "weight_price_momentum", "weight_volume", "weight_volatility",
        "weight_mean_reversion", "weight_trend",
    ],
    "Threshold": [
        "entry_threshold", "exit_threshold", "stop_loss_pct", "take_profit_pct",
    ],
    "Personality": [
        "risk_appetite", "time_horizon", "contrarian_bias", "patience",
        "position_sizing",
    ],
    "Adaptation": [
        "regime_sensitivity", "memory_length", "noise_filter",
    ],
}

# Short display names for genes
SHORT_NAMES = {
    "weight_price_momentum": "momentum",
    "weight_volume": "volume",
    "weight_volatility": "volatility",
    "weight_mean_reversion": "mean_rev",
    "weight_trend": "trend",
    "entry_threshold": "entry",
    "exit_threshold": "exit",
    "stop_loss_pct": "stop_loss",
    "take_profit_pct": "take_profit",
    "risk_appetite": "risk",
    "time_horizon": "horizon",
    "contrarian_bias": "contrarian",
    "patience": "patience",
    "position_sizing": "sizing",
    "regime_sensitivity": "regime",
    "memory_length": "memory",
    "noise_filter": "noise",
}


class StrategyFingerprint:
    """Visual fingerprint of a strategy's DNA for quick comparison."""

    def __init__(self, dna: AgentDNA):
        self.dna = dna
        self._genes = dna.get_genes()

    def _category_averages(self) -> Dict[str, float]:
        """Average gene value per category."""
        avgs = {}
        for cat, gene_names in CATEGORIES.items():
            vals = [self._genes[g] for g in gene_names]
            avgs[cat] = sum(vals) / len(vals)
        return avgs

    def radar_ascii(self, width: int = 40) -> str:
        """ASCII bar chart showing category averages as a radial-style plot."""
        avgs = self._category_averages()
        archetype = self.archetype()
        bar_width = width - 16  # space for label + value

        lines = []
        lines.append(f"┌{'─' * (width - 2)}┐")
        lines.append(f"│{'Strategy Fingerprint':^{width - 2}}│")
        lines.append(f"│{'ID: ' + self.dna.id + '  Gen: ' + str(self.dna.generation):^{width - 2}}│")
        lines.append(f"│{'Archetype: ' + archetype:^{width - 2}}│")
        lines.append(f"├{'─' * (width - 2)}┤")

        for cat, avg in avgs.items():
            filled = round(avg * bar_width)
            empty = bar_width - filled
            bar = "█" * filled + "░" * empty
            lines.append(f"│ {cat:<12}{bar} {avg:.2f} │")

        lines.append(f"├{'─' * (width - 2)}┤")

        # Per-gene detail within each category
        for cat, gene_names in CATEGORIES.items():
            lines.append(f"│ {cat + ':':─<{width - 3}}│")
            for g in gene_names:
                val = self._genes[g]
                name = SHORT_NAMES[g]
                detail_bar_w = width - 22
                filled = round(val * detail_bar_w)
                empty = detail_bar_w - filled
                bar = "▓" * filled + "░" * empty
                lines.append(f"│   {name:<10}{bar} {val:.2f} │")

        lines.append(f"└{'─' * (width - 2)}┘")
        return "\n".join(lines)

    def compare(self, other_dna: AgentDNA) -> dict:
        """Gene-by-gene comparison with difference highlighting."""
        other_genes = other_dna.get_genes()
        result = {}
        for gene in AgentDNA.GENE_FIELDS:
            a = self._genes[gene]
            b = other_genes[gene]
            diff = b - a
            abs_diff = abs(diff)
            if abs_diff > 0.3:
                marker = "!!!"
            elif abs_diff > 0.15:
                marker = "! "
            elif abs_diff > 0.05:
                marker = "~ "
            else:
                marker = "  "
            arrow = "↑" if diff > 0.005 else ("↓" if diff < -0.005 else "=")
            result[gene] = {
                "self": round(a, 4),
                "other": round(b, 4),
                "diff": round(diff, 4),
                "abs_diff": round(abs_diff, 4),
                "arrow": arrow,
                "marker": marker,
            }
        return result

    def similarity(self, other_dna: AgentDNA) -> float:
        """Cosine similarity between two DNA vectors (0-1)."""
        other_genes = other_dna.get_genes()
        a_vals = [self._genes[g] for g in AgentDNA.GENE_FIELDS]
        b_vals = [other_genes[g] for g in AgentDNA.GENE_FIELDS]

        dot = sum(x * y for x, y in zip(a_vals, b_vals))
        mag_a = math.sqrt(sum(x * x for x in a_vals))
        mag_b = math.sqrt(sum(x * x for x in b_vals))

        if mag_a == 0 or mag_b == 0:
            return 0.0
        return dot / (mag_a * mag_b)

    def dominant_traits(self) -> List[str]:
        """Genes significantly different from their default values (threshold > 0.2)."""
        defaults = AgentDNA()
        default_genes = defaults.get_genes()
        traits = []
        for gene, val in self._genes.items():
            baseline = default_genes[gene]
            deviation = val - baseline
            if abs(deviation) > 0.2:
                direction = "high" if deviation > 0 else "low"
                traits.append(f"{SHORT_NAMES[gene]}:{direction}({val:.2f})")
        return traits

    def archetype(self) -> str:
        """Classify strategy into an archetype based on gene patterns.

        Uses a weighted scoring system where each archetype has primary
        (weight 2) and secondary (weight 1) gene signals.
        """
        g = self._genes

        def _score(conditions: list) -> float:
            """Score from (value, target_high, weight) tuples.
            target_high=True means gene should be high, False means low.
            """
            total = 0.0
            weight_sum = 0.0
            for val, target_high, w in conditions:
                signal = (val - 0.5) if target_high else (0.5 - val)
                total += signal * w
                weight_sum += w
            return total / weight_sum if weight_sum else 0.0

        scores = {}

        # Aggressive Momentum: high risk + high momentum + low patience
        scores["Aggressive Momentum"] = _score([
            (g["risk_appetite"], True, 2),
            (g["weight_price_momentum"], True, 2),
            (g["patience"], False, 1.5),
            (g["position_sizing"], True, 1),
        ])

        # Conservative Mean-Reversion: low risk + high mean_reversion + high patience
        scores["Conservative Mean-Reversion"] = _score([
            (g["risk_appetite"], False, 1.5),
            (g["weight_mean_reversion"], True, 2.5),
            (g["patience"], True, 1),
            (g["noise_filter"], True, 1),
        ])

        # Balanced Adaptive: moderate everything + high regime_sensitivity
        extremeness = sum(
            abs(g[k] - 0.5) for k in [
                "risk_appetite", "weight_price_momentum", "patience",
                "time_horizon", "weight_trend", "weight_mean_reversion",
            ]
        ) / 6
        # Lower extremeness = more balanced (max contribution 0.5)
        balance_signal = 0.5 - extremeness
        regime_signal = g["regime_sensitivity"] - 0.5
        scores["Balanced Adaptive"] = balance_signal * 0.6 + regime_signal * 0.4

        # Contrarian: high contrarian_bias (primary signal)
        scores["Contrarian"] = _score([
            (g["contrarian_bias"], True, 3),
            (g["patience"], True, 1),
            (g["weight_mean_reversion"], True, 1),
        ])

        # Scalper: low horizon + low stop/tp + high noise_filter (all must contribute)
        scores["Scalper"] = _score([
            (g["time_horizon"], False, 2),
            (g["noise_filter"], True, 1.5),
            (g["stop_loss_pct"], False, 1),
            (g["take_profit_pct"], False, 1),
            (g["patience"], False, 1),
        ])

        # Trend Follower: high trend + high horizon + high patience
        scores["Trend Follower"] = _score([
            (g["weight_trend"], True, 2),
            (g["time_horizon"], True, 1.5),
            (g["patience"], True, 1.5),
            (g["contrarian_bias"], False, 1),
        ])

        best = max(scores, key=scores.get)
        if scores[best] > 0.10:
            return best
        return "Hybrid"

    def to_dict(self) -> dict:
        """Full fingerprint data."""
        return {
            "id": self.dna.id,
            "generation": self.dna.generation,
            "fitness": self.dna.fitness,
            "genes": {g: round(v, 4) for g, v in self._genes.items()},
            "archetype": self.archetype(),
            "dominant_traits": self.dominant_traits(),
            "category_averages": {
                k: round(v, 4) for k, v in self._category_averages().items()
            },
        }
