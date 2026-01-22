"""
Consensus Evaluation Experiment
===============================

Compares SA-SBFT with PBFT consensus mechanism.
Generates Figures 6-8 from the paper.
"""

import numpy as np
import time
import argparse
from typing import List, Dict
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.consensus import SASBFTConsensus, Satellite
from src.consensus.sa_sbft import OrbitalState


def create_satellite_constellation(num_satellites: int, seed: int = 42) -> List[Satellite]:
    """Create a constellation of satellites."""
    np.random.seed(seed)
    satellites = []
    
    for i in range(num_satellites):
        angle = 2 * np.pi * i / num_satellites
        r = 6371 + 550  # km
        
        sat = Satellite(
            sat_id=i,
            reputation=np.random.uniform(0.5, 1.0),
            energy=np.random.uniform(0.3, 1.0),
            orbital_state=OrbitalState(
                position=np.array([
                    r * np.cos(angle),
                    r * np.sin(angle),
                    np.random.uniform(-100, 100)
                ]),
                velocity=np.array([
                    -7.6 * np.sin(angle),
                    7.6 * np.cos(angle),
                    0
                ]),
                epoch=time.time() / 86400.0
            )
        )
        satellites.append(sat)
    
    return satellites


def measure_consensus_latency(
    consensus: SASBFTConsensus,
    num_rounds: int,
    transactions_per_round: int = 10
) -> Dict:
    """Measure consensus latency over multiple rounds."""
    latencies = []
    successes = 0
    
    for round_num in range(num_rounds):
        transactions = [
            {'tx_id': f'tx_{round_num}_{i}', 'data': f'value_{i}'}
            for i in range(transactions_per_round)
        ]
        
        start_time = time.time()
        success, _ = consensus.run_consensus(transactions, start_time)
        end_time = time.time()
        
        if success:
            successes += 1
            latencies.append((end_time - start_time) * 1000)  # ms
    
    return {
        'mean_latency_ms': np.mean(latencies) if latencies else 0,
        'std_latency_ms': np.std(latencies) if latencies else 0,
        'p99_latency_ms': np.percentile(latencies, 99) if latencies else 0,
        'success_rate': successes / num_rounds
    }


def compute_message_complexity(n: int, na_ratio: float = 0.4) -> Dict:
    """Compute theoretical message complexity."""
    na = int(n * na_ratio)  # Active nodes
    ns = n - na  # Semi-active nodes
    
    # SA-SBFT complexity
    sbft_messages = (
        1 +  # Request
        na * (na - 1) + ns * (na // 2) +  # Pre-prepare
        na * (na - 1) +  # Prepare
        n - 1 +  # Commit (aggregated)
        n  # Reply
    )
    
    # PBFT complexity
    pbft_messages = (
        1 +  # Request
        n - 1 +  # Pre-prepare
        n * (n - 1) +  # Prepare
        n * (n - 1) +  # Commit
        n  # Reply
    )
    
    return {
        'n': n,
        'sa_sbft_messages': sbft_messages,
        'pbft_messages': pbft_messages,
        'reduction_ratio': pbft_messages / sbft_messages
    }


def run_experiment(
    node_counts: List[int] = [10, 20, 50, 100],
    rounds_per_config: int = 50,
    seed: int = 42
) -> Dict:
    """Run the full consensus evaluation experiment."""
    results = {
        'latency': [],
        'message_complexity': [],
        'energy': []
    }
    
    print("=" * 60)
    print("Consensus Evaluation Experiment")
    print("=" * 60)
    
    for n in node_counts:
        print(f"\nTesting with {n} nodes...")
        
        # Create constellation
        satellites = create_satellite_constellation(n, seed)
        shard_center = np.array([6371 + 10, 0, 0])
        
        # Initialize consensus
        consensus = SASBFTConsensus(
            satellites=satellites,
            shard_center=shard_center
        )
        
        # Measure latency
        latency_results = measure_consensus_latency(consensus, rounds_per_config)
        latency_results['n'] = n
        results['latency'].append(latency_results)
        
        print(f"  Mean latency: {latency_results['mean_latency_ms']:.2f} ms")
        print(f"  Success rate: {latency_results['success_rate']:.2%}")
        
        # Compute message complexity
        msg_results = compute_message_complexity(n)
        results['message_complexity'].append(msg_results)
        
        print(f"  SA-SBFT messages: {msg_results['sa_sbft_messages']}")
        print(f"  PBFT messages: {msg_results['pbft_messages']}")
        print(f"  Reduction: {msg_results['reduction_ratio']:.2f}x")
    
    return results


def main():
    parser = argparse.ArgumentParser(description='Consensus evaluation experiment')
    parser.add_argument('--nodes', nargs='+', type=int, default=[10, 20, 50, 100],
                       help='Number of nodes to test')
    parser.add_argument('--rounds', type=int, default=50,
                       help='Consensus rounds per configuration')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed')
    parser.add_argument('--output', type=str, default='experiments/outputs/consensus',
                       help='Output directory')
    
    args = parser.parse_args()
    
    # Run experiment
    results = run_experiment(args.nodes, args.rounds, args.seed)
    
    # Print summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    print("\nLatency Results:")
    for r in results['latency']:
        print(f"  n={r['n']}: {r['mean_latency_ms']:.2f} ± {r['std_latency_ms']:.2f} ms")
    
    print("\nMessage Complexity:")
    for r in results['message_complexity']:
        print(f"  n={r['n']}: SA-SBFT={r['sa_sbft_messages']}, PBFT={r['pbft_messages']}, "
              f"Reduction={r['reduction_ratio']:.2f}x")
    
    # Save results
    os.makedirs(args.output, exist_ok=True)
    
    import json
    with open(os.path.join(args.output, 'results.json'), 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to {args.output}/")


if __name__ == "__main__":
    main()
