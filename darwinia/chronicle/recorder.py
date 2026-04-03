"""
Records every generation's data for later visualization and analysis.
"""

import json
from pathlib import Path


class EvolutionRecorder:

    def __init__(self, output_dir: str = 'output'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / 'generations').mkdir(exist_ok=True)
        (self.output_dir / 'champions').mkdir(exist_ok=True)
        self.summary = []

    def record_generation(self, stats: dict):
        """Save one generation's complete data."""
        gen = stats['generation']

        gen_data = {
            'generation': gen,
            'champion_fitness': stats['champion_fitness'],
            'avg_fitness': stats['avg_fitness'],
            'min_fitness': stats['min_fitness'],
            'max_fitness': stats['max_fitness'],
            'genetic_diversity': stats['genetic_diversity'],
            'population': stats['population_snapshot'],
        }

        gen_path = self.output_dir / 'generations' / f'gen_{gen:04d}.json'
        with open(gen_path, 'w') as f:
            json.dump(gen_data, f, indent=2, default=str)

        champ_path = self.output_dir / 'champions' / f'champion_gen_{gen:04d}.json'
        with open(champ_path, 'w') as f:
            json.dump(stats['champion'].to_dict(), f, indent=2, default=str)

        self.summary.append({
            'generation': gen,
            'champion_fitness': stats['champion_fitness'],
            'avg_fitness': stats['avg_fitness'],
            'genetic_diversity': stats['genetic_diversity'],
        })

    def save_summary(self):
        """Save the evolution summary."""
        path = self.output_dir / 'evolution_summary.json'
        with open(path, 'w') as f:
            json.dump(self.summary, f, indent=2)

    def save_final_report(self, results: dict):
        """Save the complete evolution report."""
        path = self.output_dir / 'final_report.json'
        with open(path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
