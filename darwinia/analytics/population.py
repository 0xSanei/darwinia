"""
Population Analytics — rich statistics about an evolved population.

Provides convergence analysis, diversity metrics, gene correlations,
clustering, and fitness distribution for research and visualization.
"""

import math
from typing import List, Dict, Tuple

import numpy as np

from ..core.dna import AgentDNA


class PopulationAnalyzer:
    """Analyze a population of AgentDNA instances."""

    def __init__(self, population: List[AgentDNA]):
        if not population:
            raise ValueError("Population must contain at least one agent.")
        self.population = population
        self.gene_names = AgentDNA.GENE_FIELDS
        self._matrix = self._build_gene_matrix()

    def _build_gene_matrix(self) -> np.ndarray:
        """Build an (n_agents x n_genes) matrix of gene values."""
        return np.array([
            [getattr(agent, g) for g in self.gene_names]
            for agent in self.population
        ])

    # ------------------------------------------------------------------
    # Core analytics
    # ------------------------------------------------------------------

    def gene_statistics(self) -> dict:
        """Mean, std, min, max for each gene across the population.

        Returns:
            Dict mapping gene name -> {mean, std, min, max}.
        """
        stats = {}
        for i, gene in enumerate(self.gene_names):
            col = self._matrix[:, i]
            stats[gene] = {
                'mean': float(np.mean(col)),
                'std': float(np.std(col)),
                'min': float(np.min(col)),
                'max': float(np.max(col)),
            }
        return stats

    def convergence_score(self) -> float:
        """Population convergence: 0.0 = fully random, 1.0 = fully converged.

        Based on normalized gene variance. A uniform [0,1] distribution has
        variance ~0.0833; we scale relative to that theoretical maximum.
        """
        if len(self.population) < 2:
            return 1.0

        variances = np.var(self._matrix, axis=0)
        # Theoretical max variance for uniform [0,1] is 1/12
        max_var = 1.0 / 12.0
        mean_normalized_var = float(np.mean(variances / max_var))
        score = 1.0 - min(1.0, mean_normalized_var)
        return round(score, 6)

    def cluster_agents(self, n_clusters: int = 3) -> List[List[str]]:
        """K-means style clustering of agents by DNA similarity.

        Uses Lloyd's algorithm with numpy only (no sklearn).

        Args:
            n_clusters: Number of clusters to form.

        Returns:
            List of clusters, each cluster is a list of agent IDs.
        """
        n = len(self.population)
        k = min(n_clusters, n)

        if k <= 1:
            return [[a.id for a in self.population]]

        # Initialize centroids via k-means++ style selection
        rng = np.random.RandomState(42)
        centroids = np.empty((k, self._matrix.shape[1]))
        idx = rng.randint(0, n)
        centroids[0] = self._matrix[idx]

        for c in range(1, k):
            dists = np.min([
                np.sum((self._matrix - centroids[j]) ** 2, axis=1)
                for j in range(c)
            ], axis=0)
            probs = dists / (dists.sum() + 1e-12)
            idx = rng.choice(n, p=probs)
            centroids[c] = self._matrix[idx]

        # Lloyd iterations
        for _ in range(50):
            # Assign each point to nearest centroid
            dists = np.array([
                np.sum((self._matrix - centroids[j]) ** 2, axis=1)
                for j in range(k)
            ])  # (k, n)
            labels = np.argmin(dists, axis=0)

            # Update centroids
            new_centroids = np.copy(centroids)
            for j in range(k):
                members = self._matrix[labels == j]
                if len(members) > 0:
                    new_centroids[j] = members.mean(axis=0)

            if np.allclose(centroids, new_centroids):
                break
            centroids = new_centroids

        # Build cluster lists of agent IDs
        clusters: List[List[str]] = [[] for _ in range(k)]
        for i, label in enumerate(labels):
            clusters[label].append(self.population[i].id)

        # Remove empty clusters
        clusters = [c for c in clusters if c]
        return clusters

    def diversity_metrics(self) -> dict:
        """Shannon entropy of gene distributions and effective population size.

        Returns:
            Dict with 'shannon_entropy' (per-gene dict), 'mean_entropy',
            and 'effective_population_size'.
        """
        n_bins = max(5, int(math.sqrt(len(self.population))))
        per_gene_entropy = {}

        for i, gene in enumerate(self.gene_names):
            col = self._matrix[:, i]
            counts, _ = np.histogram(col, bins=n_bins, range=(0.0, 1.0))
            probs = counts / counts.sum()
            probs = probs[probs > 0]
            entropy = -float(np.sum(probs * np.log2(probs)))
            per_gene_entropy[gene] = round(entropy, 6)

        mean_entropy = float(np.mean(list(per_gene_entropy.values())))

        # Effective population size based on fitness proportions
        fitnesses = np.array([a.fitness for a in self.population])
        total = fitnesses.sum()
        if total > 0:
            props = fitnesses / total
            props = props[props > 0]
            eff_size = float(np.exp(-np.sum(props * np.log(props + 1e-12))))
        else:
            eff_size = float(len(self.population))

        return {
            'shannon_entropy': per_gene_entropy,
            'mean_entropy': round(mean_entropy, 6),
            'effective_population_size': round(eff_size, 4),
        }

    def gene_correlations(self) -> dict:
        """Pairwise Pearson correlations between genes.

        Returns:
            Dict with 'matrix' (gene x gene dict) and 'top_pairs'
            (sorted list of most correlated pairs).
        """
        if len(self.population) < 3:
            return {'matrix': {}, 'top_pairs': []}

        n_genes = len(self.gene_names)
        corr = np.corrcoef(self._matrix.T)  # (n_genes, n_genes)

        # Handle NaN from zero-variance columns
        corr = np.nan_to_num(corr, nan=0.0)

        matrix = {}
        pairs: List[Tuple[str, str, float]] = []

        for i in range(n_genes):
            row = {}
            for j in range(n_genes):
                row[self.gene_names[j]] = round(float(corr[i, j]), 4)
                if j > i:
                    pairs.append((
                        self.gene_names[i],
                        self.gene_names[j],
                        round(float(corr[i, j]), 4),
                    ))
            matrix[self.gene_names[i]] = row

        pairs.sort(key=lambda x: abs(x[2]), reverse=True)
        top_pairs = [
            {'gene_a': a, 'gene_b': b, 'correlation': c}
            for a, b, c in pairs[:10]
        ]

        return {'matrix': matrix, 'top_pairs': top_pairs}

    def fitness_distribution(self) -> dict:
        """Histogram-style buckets of fitness scores.

        Returns:
            Dict with 'buckets' list, 'mean', 'median', 'std'.
        """
        fitnesses = np.array([a.fitness for a in self.population])
        n_buckets = 10

        fmin = float(np.min(fitnesses))
        fmax = float(np.max(fitnesses))

        if fmin == fmax:
            return {
                'buckets': [{'range': [fmin, fmax], 'count': len(self.population)}],
                'mean': float(np.mean(fitnesses)),
                'median': float(np.median(fitnesses)),
                'std': 0.0,
            }

        counts, edges = np.histogram(fitnesses, bins=n_buckets)
        buckets = []
        for i in range(len(counts)):
            buckets.append({
                'range': [round(float(edges[i]), 4), round(float(edges[i + 1]), 4)],
                'count': int(counts[i]),
            })

        return {
            'buckets': buckets,
            'mean': round(float(np.mean(fitnesses)), 4),
            'median': round(float(np.median(fitnesses)), 4),
            'std': round(float(np.std(fitnesses)), 4),
        }

    def to_dict(self) -> dict:
        """All analytics as a JSON-serializable dict."""
        return {
            'population_size': len(self.population),
            'gene_statistics': self.gene_statistics(),
            'convergence_score': self.convergence_score(),
            'diversity_metrics': self.diversity_metrics(),
            'gene_correlations': self.gene_correlations(),
            'fitness_distribution': self.fitness_distribution(),
            'clusters': self.cluster_agents(),
        }
