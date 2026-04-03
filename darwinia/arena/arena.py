"""
Adversarial Arena — runs Alpha agents against Adversary attacks.
"""

import numpy as np
from ..core.dna import AgentDNA
from ..core.agent import TradingAgent
from .adversary import AdversaryAgent
from ..core.types import RoundResult


class AdversarialArena:

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.adversary = AdversaryAgent(self.config)
        self.rounds_per_test = self.config.get('rounds_per_test', 3)
        self.history: list = []

    def test_agent(self, dna: AgentDNA, normal_data: np.ndarray) -> float:
        """
        Test an agent against adversarial scenarios.
        Returns survival bonus (0.0 to 1.0).
        """
        survived = 0
        total = self.rounds_per_test

        for _ in range(total):
            attack = self.adversary.generate_attack(target_dna=dna)
            agent = TradingAgent(dna)
            trades = agent.run(attack.candles)

            total_pnl = sum(t.pnl for t in trades) if trades else 0
            initial = 10000.0
            pnl_pct = total_pnl / initial

            agent_survived = pnl_pct > -0.20

            if agent_survived:
                survived += 1

            self.adversary.record_result(attack.pattern_type, not agent_survived)

            self.history.append(RoundResult(
                alpha_pnl=pnl_pct,
                trap_type=attack.pattern_type,
                survived=agent_survived,
                alpha_id=dna.id,
                generation=dna.generation,
            ))

        return survived / total

    def get_arms_race_data(self) -> dict:
        """Get data for arms race visualization."""
        by_gen = {}
        for r in self.history:
            gen = r.generation
            if gen not in by_gen:
                by_gen[gen] = {'survived': 0, 'total': 0, 'by_attack': {}}
            by_gen[gen]['total'] += 1
            if r.survived:
                by_gen[gen]['survived'] += 1

            attack = r.trap_type
            if attack not in by_gen[gen]['by_attack']:
                by_gen[gen]['by_attack'][attack] = {'survived': 0, 'total': 0}
            by_gen[gen]['by_attack'][attack]['total'] += 1
            if r.survived:
                by_gen[gen]['by_attack'][attack]['survived'] += 1

        return by_gen
