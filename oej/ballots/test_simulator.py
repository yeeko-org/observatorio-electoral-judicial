import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm  # For progress bar (pip install tqdm if needed)
from scipy.stats import zipf
import random


class VotingSimulator:
    def __init__(self, zipf_param=1.4, concentration_factor=20):
        """Initialize simulator with the specified Zipf parameter
        and concentration factor."""
        self.zipf_param = zipf_param
        self.concentration_factor = concentration_factor

    def generate_popularity(self, candidates, zipf_values):
        """Generate candidate popularity using Zipf distribution with
        Dirichlet variation."""

        # Use Zipf values as concentration parameters for Dirichlet
        alpha = zipf_values * self.concentration_factor

        # Generate random probabilities from Dirichlet
        random_probs = np.random.dirichlet(alpha)
        popularity = { candidate: prob for candidate, prob
                       in zip(candidates, random_probs) }
        # shuffled_candidates = random.sample(candidates, len(candidates))
        # Assign to candidates
        # popularity = {}
        # for i, candidate in enumerate(shuffled_candidates):
        #     popularity[candidate] = random_probs[i]
        return popularity

    def simulate_voting(self, popularity, voters_size, candidates, squares):
        """Simulate voting with the given parameters."""
        votes = { candidate: 0 for candidate in candidates }

        # Convert to arrays for faster processing
        candidates_array = np.array(list(candidates))
        probs = np.array([popularity[c] for c in candidates])

        # If squares is greater than or equal to number of candidates,
        # all get selected
        if len(candidates) <= squares:
            for candidate in candidates:
                votes[candidate] = voters_size
            return votes

        # Run the simulation for each voter
        for _ in range(voters_size):
            # Weighted selection based on popularity
            selected = np.random.choice(
                candidates_array,
                size=squares,
                replace=False,
                p=probs
            )

            for candidate in selected:
                votes[candidate] += 1

        return votes

    def run_simulations(
            self, candidates, squares, voters_size=1000, iterations=1000):
        """Run multiple voting simulations and return the results."""
        all_votes = []
        n = len(candidates)
        zipf_values = zipf.pmf(range(1, n + 1), self.zipf_param)

        # Use tqdm for progress bar
        for _ in tqdm(range(iterations), desc="Running simulations"):
            # Generate new popularity distribution for each iteration
            popularity = self.generate_popularity(candidates, zipf_values)

            # Simulate voting
            votes = self.simulate_voting(
                popularity, voters_size, candidates, squares)
            all_votes.append(votes)

        return all_votes

    def plot_results(self, all_votes):
        """Plot the results using box plots to show
        distribution of votes across simulations."""
        # Extract data
        candidates = sorted(all_votes[0].keys())
        n_iterations = len(all_votes)

        # Create a matrix for all votes (candidates × iterations)
        vote_matrix = np.zeros((len(candidates), n_iterations))
        for i, candidate in enumerate(candidates):
            for j, votes in enumerate(all_votes):
                vote_matrix[i, j] = votes[candidate]

        # Calculate statistics
        means = np.mean(vote_matrix, axis=1)
        medians = np.median(vote_matrix, axis=1)
        stds = np.std(vote_matrix, axis=1)

        # Create figure
        fig, ax = plt.subplots(figsize=(12, 8))

        # Box plot
        positions = range(1, len(candidates) + 1)
        bp = ax.boxplot([vote_matrix[i] for i in range(len(candidates))],
                        positions=positions, patch_artist=True,
                        showfliers=True, widths=0.6)

        # Custom colors for boxes
        colors = plt.cm.viridis(np.linspace(0, 0.9, len(candidates)))
        for i, box in enumerate(bp['boxes']):
            box.set(facecolor=colors[i], alpha=0.8)
            bp['medians'][i].set(color='red', linewidth=2)

        # Add mean points and connecting line
        ax.plot(positions, means, 'ro', markersize=8, label='Mean')
        ax.plot(positions, means, 'r--', alpha=0.7)

        # Add statistical annotations
        for i, candidate in enumerate(candidates):
            stats_text = (
                f"Mean: {means[i]:.1f}\n"
                f"Median: {medians[i]:.1f}\n"
                f"Std Dev: {stds[i]:.1f}"
            )
            # Position text above the maximum value
            y_pos = (np.max(vote_matrix[i]) + 0.05 *
                     (ax.get_ylim()[1] - ax.get_ylim()[0]))
            ax.text(i + 1, y_pos, stats_text,
                    ha='center', va='bottom', fontsize=9,
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))

        # Labels and styling
        ax.set_title(f'Vote Distribution Across {n_iterations} Simulations\n'
                     f'(Zipf α={self.zipf_param}, '
                     f'Concentration Factor={self.concentration_factor})',
                     fontsize=14)
        ax.set_xlabel('Candidate ID', fontsize=12)
        ax.set_ylabel('Number of Votes', fontsize=12)
        ax.set_xticks(positions)
        ax.set_xticklabels(candidates)
        ax.grid(axis='y', linestyle='--', alpha=0.3)
        ax.legend()

        plt.tight_layout()
        plt.show()

        # Return statistics dictionary
        return {
            'means': { candidates[i]: means[i] for i in range(len(candidates)) },
            'medians': { candidates[i]: medians[i] for i in range(len(candidates)) },
            'stds': { candidates[i]: stds[i] for i in range(len(candidates)) }
        }


def main(candidate_ids=None, square_quantity=1,
         zipf_param=1.3, concentration_factor=20, cand_size=3):
    """
    Run voting simulations with the specified parameters.

    Parameters:
    - candidate_ids: List of candidate IDs (defaults to [1, 2, 3, 4] if None)
    - square_quantity: Number of squares each voter can select
    """
    if candidate_ids is None:
        candidate_ids = list(range(1, cand_size + 1))

    # Create simulator with fixed parameters
    simulator = VotingSimulator(
        zipf_param=zipf_param, concentration_factor=concentration_factor)

    # Run simulations
    all_votes = simulator.run_simulations(
        candidates=candidate_ids,
        squares=square_quantity,
        voters_size=1000,
        iterations=1000  # Run 1000 iterations
    )

    # Plot results
    statistics = simulator.plot_results(all_votes)

    # Print summary statistics
    print("\nSummary Statistics:")
    print("-" * 50)
    print(f"{'Candidate':<10} {'Mean':<10} {'Median':<10} {'Std Dev':<10}")
    print("-" * 50)

    for candidate in sorted(statistics['means'].keys()):
        print(f"{candidate:<10} {statistics['means'][candidate]:<10.2f} "
              f"{statistics['medians'][candidate]:<10.2f} "
              f"{statistics['stds'][candidate]:<10.2f}")

    return simulator


if __name__ == "__main__":
    main(zipf_param=1.1, concentration_factor=30, cand_size=2)