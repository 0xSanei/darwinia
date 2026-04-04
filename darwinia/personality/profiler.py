"""
Personality Profiler — quantifies an agent's trading personality from its DNA.

Maps raw genes into human-readable personality dimensions:
- Aggression (risk appetite + position sizing + patience)
- Conviction (entry threshold + noise filter)
- Adaptability (regime sensitivity + memory length)
- Contrarianism (contrarian bias)
- Time Preference (time horizon + patience)
"""

import numpy as np
from typing import Dict, List
from ..core.dna import AgentDNA


# Named personality archetypes and their gene signatures
ARCHETYPES = {
    'Scalper': {
        'aggression': (0.6, 1.0),
        'conviction': (0.0, 0.4),
        'adaptability': (0.5, 1.0),
        'contrarianism': (0.0, 0.4),
        'time_preference': (0.0, 0.3),
    },
    'Swing Trader': {
        'aggression': (0.3, 0.6),
        'conviction': (0.4, 0.7),
        'adaptability': (0.3, 0.7),
        'contrarianism': (0.0, 0.5),
        'time_preference': (0.4, 0.7),
    },
    'Position Trader': {
        'aggression': (0.1, 0.4),
        'conviction': (0.6, 1.0),
        'adaptability': (0.2, 0.5),
        'contrarianism': (0.0, 0.4),
        'time_preference': (0.7, 1.0),
    },
    'Contrarian': {
        'aggression': (0.3, 0.7),
        'conviction': (0.5, 1.0),
        'adaptability': (0.4, 0.8),
        'contrarianism': (0.6, 1.0),
        'time_preference': (0.3, 0.7),
    },
    'Conservative': {
        'aggression': (0.0, 0.3),
        'conviction': (0.5, 0.8),
        'adaptability': (0.2, 0.5),
        'contrarianism': (0.2, 0.5),
        'time_preference': (0.5, 0.8),
    },
    'Degen': {
        'aggression': (0.8, 1.0),
        'conviction': (0.0, 0.3),
        'adaptability': (0.6, 1.0),
        'contrarianism': (0.0, 0.3),
        'time_preference': (0.0, 0.2),
    },
}


class PersonalityProfiler:
    """Quantify and classify agent personalities from DNA."""

    DIMENSIONS = ['aggression', 'conviction', 'adaptability', 'contrarianism', 'time_preference']

    def profile(self, dna: AgentDNA) -> Dict:
        """
        Generate a full personality profile from DNA.

        Returns dict with:
        - dimensions: {name: float} scores in [0, 1]
        - archetype: closest named archetype
        - archetype_distance: how close (lower = better match)
        - description: human-readable summary
        """
        dims = self._compute_dimensions(dna)
        archetype, distance = self._match_archetype(dims)
        description = self._generate_description(dims, archetype)

        return {
            'dimensions': dims,
            'archetype': archetype,
            'archetype_distance': round(distance, 4),
            'description': description,
            'agent_id': dna.id,
            'generation': dna.generation,
        }

    def _compute_dimensions(self, dna: AgentDNA) -> Dict[str, float]:
        """Map raw genes to personality dimensions."""
        return {
            'aggression': float(np.clip(
                dna.risk_appetite * 0.4 + dna.position_sizing * 0.35 + (1 - dna.patience) * 0.25,
                0, 1
            )),
            'conviction': float(np.clip(
                dna.entry_threshold * 0.5 + dna.noise_filter * 0.5,
                0, 1
            )),
            'adaptability': float(np.clip(
                dna.regime_sensitivity * 0.5 + dna.memory_length * 0.3 + (1 - dna.noise_filter) * 0.2,
                0, 1
            )),
            'contrarianism': float(dna.contrarian_bias),
            'time_preference': float(np.clip(
                dna.time_horizon * 0.6 + dna.patience * 0.4,
                0, 1
            )),
        }

    def _match_archetype(self, dims: Dict[str, float]) -> tuple:
        """Find the closest named archetype."""
        best_name = 'Unknown'
        best_dist = float('inf')

        for name, ranges in ARCHETYPES.items():
            dist = 0
            for dim in self.DIMENSIONS:
                lo, hi = ranges[dim]
                mid = (lo + hi) / 2
                dist += (dims[dim] - mid) ** 2
            dist = dist ** 0.5

            if dist < best_dist:
                best_dist = dist
                best_name = name

        return best_name, best_dist

    def profile_population(self, agents: List[AgentDNA]) -> Dict:
        """Profile an entire population, return species distribution."""
        profiles = [self.profile(dna) for dna in agents]
        archetype_counts = {}
        for p in profiles:
            arch = p['archetype']
            archetype_counts[arch] = archetype_counts.get(arch, 0) + 1

        avg_dims = {}
        for dim in self.DIMENSIONS:
            avg_dims[dim] = float(np.mean([p['dimensions'][dim] for p in profiles]))

        return {
            'archetype_distribution': archetype_counts,
            'avg_dimensions': avg_dims,
            'profiles': profiles,
        }

    def _generate_description(self, dims: Dict[str, float], archetype: str) -> str:
        """Generate a one-line personality description."""
        traits = []

        if dims['aggression'] > 0.7:
            traits.append("aggressive")
        elif dims['aggression'] < 0.3:
            traits.append("cautious")

        if dims['conviction'] > 0.7:
            traits.append("high-conviction")
        elif dims['conviction'] < 0.3:
            traits.append("trigger-happy")

        if dims['adaptability'] > 0.7:
            traits.append("adaptive")
        elif dims['adaptability'] < 0.3:
            traits.append("rigid")

        if dims['contrarianism'] > 0.7:
            traits.append("contrarian")

        if dims['time_preference'] > 0.7:
            traits.append("long-horizon")
        elif dims['time_preference'] < 0.3:
            traits.append("short-term")

        trait_str = ", ".join(traits) if traits else "balanced"
        return f"{archetype} ({trait_str})"
