"""
Adversary Agent — generates attack scenarios to test Alpha agents.
"""

import numpy as np
import random
from typing import List, Dict
from ..core.dna import AgentDNA
from ..core.types import AttackScenario


class AdversaryAgent:
    """
    Generates market scenarios designed to trap trading agents.
    """

    ATTACK_TEMPLATES = {
        'rug_pull': {
            'description': 'Steady rise followed by sudden 90%+ crash',
            'difficulty': 0.7,
            'phases': [
                {'type': 'uptrend', 'length': 50, 'magnitude': 0.5},
                {'type': 'crash', 'length': 3, 'magnitude': -0.9},
            ]
        },
        'fake_breakout': {
            'description': 'Price breaks resistance then immediately reverses',
            'difficulty': 0.6,
            'phases': [
                {'type': 'range', 'length': 40, 'magnitude': 0.05},
                {'type': 'spike', 'length': 3, 'magnitude': 0.15},
                {'type': 'crash', 'length': 10, 'magnitude': -0.25},
            ]
        },
        'slow_bleed': {
            'description': 'Gradual decline with misleading bounces',
            'difficulty': 0.8,
            'phases': [
                {'type': 'slow_decline_with_bounces', 'length': 100, 'magnitude': -0.4},
            ]
        },
        'whipsaw': {
            'description': 'Rapid alternating moves to trigger stops',
            'difficulty': 0.5,
            'phases': [
                {'type': 'oscillate', 'length': 60, 'magnitude': 0.08},
            ]
        },
        'volume_mirage': {
            'description': 'Volume spike with no follow-through',
            'difficulty': 0.6,
            'phases': [
                {'type': 'volume_spike_flat_price', 'length': 30, 'magnitude': 0.02},
                {'type': 'decline', 'length': 20, 'magnitude': -0.15},
            ]
        },
        'pump_and_dump': {
            'description': 'Rapid pump followed by equally rapid dump',
            'difficulty': 0.7,
            'phases': [
                {'type': 'pump', 'length': 10, 'magnitude': 0.4},
                {'type': 'dump', 'length': 5, 'magnitude': -0.45},
            ]
        },
    }

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.attack_success_history: Dict[str, List[bool]] = {
            k: [] for k in self.ATTACK_TEMPLATES
        }

    def generate_attack(self, target_dna: AgentDNA = None) -> AttackScenario:
        """Generate an attack scenario, optionally targeted at specific DNA."""
        if target_dna and random.random() < 0.7:
            attack_type = self._choose_targeted_attack(target_dna)
        else:
            attack_type = random.choice(list(self.ATTACK_TEMPLATES.keys()))

        template = self.ATTACK_TEMPLATES[attack_type]
        candles = self._build_scenario(template, base_price=100.0)

        return AttackScenario(
            name=attack_type,
            description=template['description'],
            pattern_type=attack_type,
            difficulty=template['difficulty'],
            candles=candles,
        )

    def _choose_targeted_attack(self, dna: AgentDNA) -> str:
        """Choose attack based on DNA vulnerabilities."""
        if dna.weight_trend > 0.7 or dna.contrarian_bias < 0.3:
            return random.choice(['fake_breakout', 'whipsaw'])
        if dna.weight_price_momentum > 0.7:
            return random.choice(['pump_and_dump', 'rug_pull'])
        if dna.patience > 0.7 and dna.stop_loss_pct < 0.3:
            return 'slow_bleed'
        if dna.weight_volume > 0.7:
            return 'volume_mirage'
        return random.choice(list(self.ATTACK_TEMPLATES.keys()))

    def _build_scenario(self, template: dict, base_price: float) -> np.ndarray:
        """Build OHLCV candles from attack template phases."""
        all_candles = []
        current_price = base_price
        timestamp = 0

        for phase in template['phases']:
            phase_candles, current_price = self._generate_phase(
                phase, current_price, timestamp
            )
            all_candles.extend(phase_candles)
            timestamp += len(phase_candles)

        return np.array(all_candles)

    def _generate_phase(self, phase: dict, start_price: float,
                        start_time: int) -> tuple:
        """Generate candles for one phase of an attack scenario."""
        candles = []
        price = start_price
        length = phase['length']
        magnitude = phase['magnitude']

        for i in range(length):
            progress = i / max(1, length - 1)

            if phase['type'] == 'uptrend':
                target = start_price * (1 + magnitude * progress)
                noise = random.gauss(0, 0.005)
                price = target * (1 + noise)
            elif phase['type'] in ('crash', 'dump'):
                target = start_price * (1 + magnitude * progress)
                noise = random.gauss(0, 0.01)
                price = max(0.01, target * (1 + noise))
            elif phase['type'] == 'range':
                noise = random.gauss(0, magnitude)
                price = start_price * (1 + noise)
            elif phase['type'] == 'spike':
                target = start_price * (1 + magnitude * progress)
                price = target
            elif phase['type'] == 'slow_decline_with_bounces':
                trend = magnitude * progress
                bounce = 0.03 * np.sin(progress * 8 * np.pi)
                noise = random.gauss(0, 0.01)
                price = start_price * (1 + trend + bounce + noise)
            elif phase['type'] == 'oscillate':
                swing = magnitude * np.sin(progress * 12 * np.pi)
                price = start_price * (1 + swing)
            elif phase['type'] in ('pump',):
                target = start_price * (1 + magnitude * progress)
                price = target * (1 + random.gauss(0, 0.01))
            elif phase['type'] == 'volume_spike_flat_price':
                noise = random.gauss(0, magnitude)
                price = start_price * (1 + noise)
            elif phase['type'] == 'decline':
                target = start_price * (1 + magnitude * progress)
                price = target * (1 + random.gauss(0, 0.005))
            else:
                price = start_price

            h = price * (1 + abs(random.gauss(0, 0.005)))
            l = price * (1 - abs(random.gauss(0, 0.005)))
            o = price * (1 + random.gauss(0, 0.002))

            base_vol = 1000
            if phase['type'] in ('crash', 'dump', 'pump', 'spike'):
                vol = base_vol * random.uniform(3, 8)
            elif phase['type'] == 'volume_spike_flat_price':
                vol = base_vol * random.uniform(5, 15)
            else:
                vol = base_vol * random.uniform(0.5, 2)

            candles.append([
                start_time + i,
                o, h, l, price, vol,
            ])

        return candles, price

    def record_result(self, attack_type: str, succeeded: bool):
        """Track which attacks succeed for future strategy."""
        if attack_type in self.attack_success_history:
            self.attack_success_history[attack_type].append(succeeded)
