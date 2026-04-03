"""
Species tracking — identify distinct strategy lineages in the population.
"""

import numpy as np
from typing import List, Dict
from ..core.dna import AgentDNA


class SpeciationTracker:

    def identify_species(self, agents: List[AgentDNA],
                        max_species: int = 5) -> Dict[int, List[str]]:
        """Cluster agents into species using k-means on gene space."""
        if len(agents) < max_species:
            return {0: [a.id for a in agents]}

        gene_matrix = np.array([
            [getattr(a, g) for g in AgentDNA.GENE_FIELDS]
            for a in agents
        ])

        best_k = self._find_optimal_k(gene_matrix, max_species)
        labels = self._kmeans(gene_matrix, best_k)

        species = {}
        for i, agent in enumerate(agents):
            label = int(labels[i])
            if label not in species:
                species[label] = []
            species[label].append(agent.id)

        return species

    def name_species(self, agents: List[AgentDNA], labels: np.ndarray) -> Dict[int, str]:
        """Give species descriptive names based on dominant genes."""
        names = {}
        unique_labels = set(labels)

        for label in unique_labels:
            members = [a for a, l in zip(agents, labels) if l == label]
            gene_avgs = {}
            for gene in AgentDNA.GENE_FIELDS:
                gene_avgs[gene] = np.mean([getattr(a, gene) for a in members])

            dominant = max(gene_avgs, key=gene_avgs.get)
            names[label] = self._gene_to_species_name(dominant, gene_avgs[dominant])

        return names

    def _gene_to_species_name(self, gene: str, value: float) -> str:
        """Map dominant gene to a descriptive species name."""
        name_map = {
            'weight_trend': 'Trend Riders',
            'weight_price_momentum': 'Momentum Hunters',
            'weight_mean_reversion': 'Mean Reverters',
            'weight_volume': 'Volume Watchers',
            'weight_volatility': 'Volatility Traders',
            'contrarian_bias': 'Contrarians',
            'risk_appetite': 'Risk Seekers' if value > 0.6 else 'Risk Avoiders',
            'patience': 'Patient Stalkers' if value > 0.6 else 'Quick Strikers',
            'noise_filter': 'Signal Purists',
        }
        return name_map.get(gene, f'{gene}_specialists')

    def _kmeans(self, data: np.ndarray, k: int, max_iter: int = 50) -> np.ndarray:
        """Simple k-means without sklearn."""
        n = len(data)
        indices = np.random.choice(n, k, replace=False)
        centroids = data[indices].copy()
        labels = np.zeros(n, dtype=int)

        for _ in range(max_iter):
            for i in range(n):
                distances = [np.linalg.norm(data[i] - c) for c in centroids]
                labels[i] = np.argmin(distances)

            new_centroids = np.zeros_like(centroids)
            for j in range(k):
                members = data[labels == j]
                if len(members) > 0:
                    new_centroids[j] = members.mean(axis=0)
                else:
                    new_centroids[j] = centroids[j]

            if np.allclose(centroids, new_centroids):
                break
            centroids = new_centroids

        return labels

    def _find_optimal_k(self, data: np.ndarray, max_k: int) -> int:
        """Find optimal k using elbow method (simplified)."""
        inertias = []
        for k in range(2, max_k + 1):
            labels = self._kmeans(data, k)
            inertia = 0
            for j in range(k):
                members = data[labels == j]
                if len(members) > 0:
                    center = members.mean(axis=0)
                    inertia += np.sum((members - center) ** 2)
            inertias.append(inertia)

        for i in range(1, len(inertias)):
            if i > 0 and inertias[i-1] > 0:
                improvement = (inertias[i-1] - inertias[i]) / inertias[i-1]
                if improvement < 0.2:
                    return i + 1  # k = i+1 (offset by starting at 2)

        return min(3, max_k)
