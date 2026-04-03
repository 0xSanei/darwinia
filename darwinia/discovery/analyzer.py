"""
Pattern Discovery — analyze WHY survivors survived.
"""

import numpy as np
from typing import List
from ..core.dna import AgentDNA
from ..core.types import DiscoveredPattern


class PatternAnalyzer:

    def analyze_survivors(self, survivors: List[AgentDNA],
                         market_data: np.ndarray) -> List[DiscoveredPattern]:
        """Find patterns in what made survivors successful."""
        if not survivors:
            return []

        discovered = []

        convergence = self._analyze_gene_convergence(survivors)
        for gene, stats in convergence.items():
            if stats['convergence'] > 0.7:
                pattern = DiscoveredPattern(
                    name=f"converged_{gene}_{stats['mean']:.2f}",
                    features={gene: stats['mean']},
                    predictive_power=stats['convergence'],
                    human_equivalent=self._match_human_concept(gene, stats['mean']),
                    discovered_by='population',
                    generation=survivors[0].generation if survivors else 0,
                )
                discovered.append(pattern)

        combos = self._analyze_gene_combinations(survivors)
        for combo in combos:
            discovered.append(combo)

        return discovered

    def _analyze_gene_convergence(self, survivors: List[AgentDNA]) -> dict:
        """Check if specific genes converged to similar values."""
        convergence = {}

        for gene in AgentDNA.GENE_FIELDS:
            values = [getattr(a, gene) for a in survivors]
            mean = np.mean(values)
            std = np.std(values)

            max_std = 0.289  # std of uniform [0,1]
            convergence_score = 1 - (std / max_std)

            convergence[gene] = {
                'mean': float(mean),
                'std': float(std),
                'convergence': float(convergence_score),
            }

        return convergence

    def _analyze_gene_combinations(self, survivors: List[AgentDNA]) -> list:
        """Find interesting gene combinations in survivors."""
        patterns = []
        genes = AgentDNA.GENE_FIELDS

        for i, g1 in enumerate(genes):
            for g2 in genes[i+1:]:
                vals1 = [getattr(a, g1) for a in survivors]
                vals2 = [getattr(a, g2) for a in survivors]

                if len(vals1) < 3:
                    continue

                corr = np.corrcoef(vals1, vals2)[0, 1]

                if abs(corr) > 0.7:
                    pattern = DiscoveredPattern(
                        name=f"linked_{g1[:8]}_{g2[:8]}",
                        features={g1: float(np.mean(vals1)), g2: float(np.mean(vals2))},
                        predictive_power=float(abs(corr)),
                        human_equivalent=self._explain_combination(g1, g2, corr),
                        discovered_by='population',
                        generation=survivors[0].generation if survivors else 0,
                    )
                    patterns.append(pattern)

        return patterns

    def _match_human_concept(self, gene: str, value: float) -> str:
        """Try to match a converged gene to a known human trading concept."""
        mappings = {
            ('contrarian_bias', 'high'): 'Mean Reversion Strategy',
            ('contrarian_bias', 'low'): 'Trend Following Strategy',
            ('risk_appetite', 'low'): 'Conservative / Risk-Off',
            ('risk_appetite', 'high'): 'Aggressive / Risk-On',
            ('patience', 'high'): 'Position Trading',
            ('patience', 'low'): 'Scalping / Day Trading',
            ('time_horizon', 'high'): 'Swing Trading',
            ('time_horizon', 'low'): 'Intraday Trading',
            ('noise_filter', 'high'): 'Signal Smoothing (like EMA)',
        }

        level = 'high' if value > 0.6 else 'low' if value < 0.4 else None
        if level:
            return mappings.get((gene, level), 'No known equivalent')
        return 'No known equivalent'

    def _explain_combination(self, g1: str, g2: str, corr: float) -> str:
        """Generate human-readable explanation of gene combination."""
        direction = "positively" if corr > 0 else "negatively"
        return f"{g1} and {g2} are {direction} linked in survivors (r={corr:.2f})"
