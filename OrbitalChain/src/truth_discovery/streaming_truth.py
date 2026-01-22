"""
Privacy-Preserving Streaming Truth Discovery for OrbitalChain
=============================================================

Implements Algorithm 2 from the paper: Privacy-preserving streaming truth
discovery scheme for continuously mining reliable knowledge.

This module provides secure computation of truth values and weight updates
using secret sharing, Beaver triples, and garbled circuits.

References:
    - Li et al. (2016). Conflicts to harmony: A framework for resolving conflicts.
    - OrbitalChain Paper, Section 4.7
"""

import numpy as np
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass, field
import secrets

import sys
sys.path.append('..')

from crypto.secret_sharing import AdditiveSecretSharing, Share
from crypto.beaver_triples import BeaverTripleGenerator, SecureMultiplication, SharedTriple
from crypto.garbled_circuits import GarbledCircuitProtocol


@dataclass
class DataProviderState:
    """State maintained for each data provider."""
    provider_id: int
    weight: float = 1.0
    accumulated_distance: float = 0.0
    weight_shares: List[Share] = field(default_factory=list)
    distance_shares: List[Share] = field(default_factory=list)


@dataclass
class EpochResult:
    """Results from one epoch of truth discovery."""
    epoch: int
    truth_value: float
    weights: Dict[int, float]
    truth_shares: List[Share]
    processing_time_ms: float


class StreamingTruthDiscovery:
    """
    Privacy-preserving streaming truth discovery protocol.
    
    Implements the secure truth and weight update algorithms from
    Algorithm 2 of the OrbitalChain paper.
    
    Protocol Overview:
        1. Data providers secret-share their sensing values
        2. Satellites jointly compute the weighted truth using MPC
        3. Weights are updated based on deviation from truth
        4. Process repeats for each epoch
    
    Security Properties:
        - Individual sensing values remain hidden from satellites
        - Only aggregate truth and final weights are revealed
        - Secure against semi-honest adversaries
    
    Example:
        >>> td = StreamingTruthDiscovery(num_satellites=5, num_providers=10)
        >>> sensing_values = [0.5, 0.52, 0.48, 0.51, ...]
        >>> result = td.run_epoch(sensing_values)
        >>> print(f"Truth: {result.truth_value}")
    """
    
    # Scale factor for fixed-point arithmetic
    SCALE_FACTOR = 10**6
    
    def __init__(
        self,
        num_satellites: int,
        num_data_providers: int,
        decay_factor: float = 0.9,
        prime_modulus: Optional[int] = None
    ):
        """
        Initialize the truth discovery protocol.
        
        Args:
            num_satellites: Number of satellites (n) participating in MPC
            num_data_providers: Number of data providers (K)
            decay_factor: λ parameter for historical data weight (0 < λ ≤ 1)
            prime_modulus: Prime for finite field operations
        """
        if not 0 < decay_factor <= 1:
            raise ValueError("Decay factor must be in (0, 1]")
        
        self.num_satellites = num_satellites
        self.num_data_providers = num_data_providers
        self.decay_factor = decay_factor
        
        # Initialize cryptographic components
        self.ss = AdditiveSecretSharing(num_satellites, prime_modulus)
        self.prime_modulus = self.ss.prime_modulus
        self.mult = SecureMultiplication(num_satellites, self.prime_modulus)
        self.triple_gen = BeaverTripleGenerator(num_satellites, self.prime_modulus)
        self.gc_protocol = GarbledCircuitProtocol(self.prime_modulus)
        
        # Initialize state for each data provider
        self.providers: Dict[int, DataProviderState] = {
            k: DataProviderState(provider_id=k)
            for k in range(num_data_providers)
        }
        
        # Epoch counter
        self.current_epoch = 0
        
        # Store shares for each satellite
        self.satellite_states: Dict[int, Dict] = {
            i: {'weight_shares': {}, 'distance_shares': {}}
            for i in range(num_satellites)
        }
    
    def _scale_to_field(self, value: float) -> int:
        """Convert floating point to field element."""
        scaled = int(value * self.SCALE_FACTOR)
        return scaled % self.prime_modulus
    
    def _field_to_scale(self, value: int) -> float:
        """Convert field element back to floating point."""
        if value > self.prime_modulus // 2:
            value = value - self.prime_modulus
        return value / self.SCALE_FACTOR
    
    def submit_sensing_value(
        self,
        provider_id: int,
        sensing_value: float
    ) -> Tuple[List[Share], Tuple[List[SharedTriple], List[SharedTriple]]]:
        """
        Data provider submits their sensing value.
        
        Creates secret shares and multiplication triples for secure computation.
        
        Args:
            provider_id: ID of the data provider
            sensing_value: The sensing value x_l^k
        
        Returns:
            Tuple of (value_shares, (triple_set_0, triple_set_1))
        """
        # Scale and share the sensing value
        scaled_value = self._scale_to_field(sensing_value)
        value_shares = self.ss.share(scaled_value)
        
        # Generate multiplication triples
        triple_0 = self.triple_gen.generate_triple()
        triple_1 = self.triple_gen.generate_triple()
        
        return value_shares, (triple_0, triple_1)
    
    def secure_truth_update_epoch1(
        self,
        sensing_shares: Dict[int, List[Share]]
    ) -> List[Share]:
        """
        Secure truth update for epoch l=1 (Equation 19).
        
        At epoch 1, all weights are initialized to 1, so this is
        a simple averaging operation.
        
        Φ = Σ(w_k * x_k) / Σ(w_k) = Σ(x_k) / K
        
        Args:
            sensing_shares: Dictionary mapping provider_id -> shares of sensing value
        
        Returns:
            Shares of the computed truth Φ
        """
        K = len(sensing_shares)
        
        # Sum all sensing value shares (local operation)
        sum_shares = [
            Share(party_id=i, value=0, field_modulus=self.prime_modulus)
            for i in range(self.num_satellites)
        ]
        
        for provider_id, shares in sensing_shares.items():
            sum_shares = self.ss.add_shares(sum_shares, shares)
        
        # Divide by K (multiplication by 1/K)
        # In finite field, this requires computing modular inverse
        k_inv = pow(K, self.prime_modulus - 2, self.prime_modulus)
        truth_shares = self.ss.multiply_by_constant(sum_shares, k_inv)
        
        return truth_shares
    
    def secure_truth_update(
        self,
        sensing_shares: Dict[int, List[Share]],
        weight_shares: Dict[int, List[Share]],
        triples: Dict[int, List[SharedTriple]]
    ) -> List[Share]:
        """
        Secure truth update for epoch l >= 2 (Equations 20-21).
        
        Computes:
            t = Σ(w_k * x_k)  (using Beaver multiplication)
            z = Σ(w_k)
            Φ = t / z        (using garbled circuits)
        
        Args:
            sensing_shares: Shares of sensing values {k: [x_k]_i}
            weight_shares: Shares of weights {k: [w_k]_i}
            triples: Beaver triples for multiplication {k: triple}
        
        Returns:
            Shares of the computed truth Φ
        """
        # Step 1: Compute weighted sum t = Σ(w_k * x_k)
        weighted_products = []
        
        for k in sensing_shares.keys():
            # Secure multiplication: [w_k * x_k]
            product_shares = self.mult.multiply(
                weight_shares[k],
                sensing_shares[k],
                triples[k]
            )
            weighted_products.append(product_shares)
        
        # Sum all products
        t_shares = weighted_products[0]
        for product in weighted_products[1:]:
            t_shares = self.ss.add_shares(t_shares, product)
        
        # Step 2: Compute sum of weights z = Σ(w_k)
        z_shares = weight_shares[0]
        for k in range(1, len(weight_shares)):
            z_shares = self.ss.add_shares(z_shares, weight_shares[k])
        
        # Step 3: Secure division using garbled circuits
        # Φ = t / z
        # We need shares from two parties for the GC protocol
        truth_share_0, truth_share_1 = self.gc_protocol.gc_div(
            t_shares[0], t_shares[1],
            z_shares[0], z_shares[1]
        )
        
        # Distribute shares to all parties
        # In practice, this would use secret sharing
        truth_shares = [truth_share_0, truth_share_1]
        for i in range(2, self.num_satellites):
            truth_shares.append(Share(
                party_id=i,
                value=0,  # Additional parties get zero shares
                field_modulus=self.prime_modulus
            ))
        
        return truth_shares
    
    def secure_weight_update(
        self,
        truth_shares: List[Share],
        sensing_shares: Dict[int, List[Share]],
        triples: Dict[int, List[SharedTriple]]
    ) -> Dict[int, List[Share]]:
        """
        Secure weight update (Equations 22-23).
        
        For each data provider k:
            1. d_k = (x_k - Φ)²
            2. st(k) = st(k) * λ + d_k
            3. st* = Σ(st(k))
            4. w_k = -log(st(k) / st*)
        
        Args:
            truth_shares: Shares of current truth Φ
            sensing_shares: Shares of sensing values
            triples: Beaver triples for squaring
        
        Returns:
            Updated weight shares for each provider
        """
        updated_weights = {}
        distance_shares = {}
        
        # Step 1-2: Compute squared errors and update states
        for k, x_shares in sensing_shares.items():
            # Compute d = x_k - Φ
            neg_truth = self.ss.multiply_by_constant(
                truth_shares, 
                self.prime_modulus - 1  # -1 in field
            )
            d_shares = self.ss.add_shares(x_shares, neg_truth)
            
            # Compute d² using Beaver multiplication (Equation 22)
            d_squared_shares = self.mult.square(d_shares, triples[k])
            
            # Update accumulated distance: st(k) = st(k) * λ + d²
            # Get previous state
            prev_state = self.providers[k].distance_shares
            if prev_state:
                # st(k) * λ
                lambda_scaled = self._scale_to_field(self.decay_factor)
                scaled_prev = self.ss.multiply_by_constant(prev_state, lambda_scaled)
                # Add d²
                new_state = self.ss.add_shares(scaled_prev, d_squared_shares)
            else:
                new_state = d_squared_shares
            
            distance_shares[k] = new_state
            self.providers[k].distance_shares = new_state
        
        # Step 3: Compute total accumulated distance st*
        st_star_shares = distance_shares[0]
        for k in range(1, len(distance_shares)):
            st_star_shares = self.ss.add_shares(st_star_shares, distance_shares[k])
        
        # Step 4: Compute weights using GC (Equation 23)
        for k in distance_shares.keys():
            st_k = distance_shares[k]
            
            # Secure division and logarithm
            w_share_0, w_share_1 = self.gc_protocol.gc_div_log(
                st_k[0], st_k[1],
                st_star_shares[0], st_star_shares[1]
            )
            
            # Create full share list
            w_shares = [w_share_0, w_share_1]
            for i in range(2, self.num_satellites):
                w_shares.append(Share(
                    party_id=i,
                    value=0,
                    field_modulus=self.prime_modulus
                ))
            
            updated_weights[k] = w_shares
            self.providers[k].weight_shares = w_shares
        
        return updated_weights
    
    def run_epoch(
        self,
        sensing_values: List[float]
    ) -> EpochResult:
        """
        Run one epoch of the truth discovery protocol.
        
        This is the main entry point for processing a batch of sensing values.
        
        Args:
            sensing_values: List of sensing values from all data providers
        
        Returns:
            EpochResult containing the discovered truth and updated weights
        """
        import time
        start_time = time.time()
        
        if len(sensing_values) != self.num_data_providers:
            raise ValueError(
                f"Expected {self.num_data_providers} values, got {len(sensing_values)}"
            )
        
        self.current_epoch += 1
        
        # Step 1: Data providers submit secret-shared values
        sensing_shares = {}
        all_triples = {}
        
        for k, value in enumerate(sensing_values):
            shares, triples = self.submit_sensing_value(k, value)
            sensing_shares[k] = shares
            all_triples[k] = triples[0]  # Use first triple set
        
        # Step 2: Secure truth update
        if self.current_epoch == 1:
            truth_shares = self.secure_truth_update_epoch1(sensing_shares)
        else:
            # Get weight shares from previous epoch
            weight_shares = {
                k: provider.weight_shares 
                for k, provider in self.providers.items()
            }
            truth_shares = self.secure_truth_update(
                sensing_shares, weight_shares, all_triples
            )
        
        # Step 3: Secure weight update
        weight_triples = {k: triples[1] for k, (_, triples) in 
                         [(k, self.submit_sensing_value(k, sensing_values[k])) 
                          for k in range(self.num_data_providers)]}
        
        updated_weight_shares = self.secure_weight_update(
            truth_shares, sensing_shares, 
            {k: all_triples[k] for k in all_triples}
        )
        
        # Reconstruct truth for output
        truth_value = self._field_to_scale(self.ss.reconstruct(truth_shares))
        
        # Reconstruct weights for output
        weights = {}
        for k, w_shares in updated_weight_shares.items():
            weights[k] = self._field_to_scale(self.ss.reconstruct(w_shares))
        
        processing_time = (time.time() - start_time) * 1000
        
        return EpochResult(
            epoch=self.current_epoch,
            truth_value=truth_value,
            weights=weights,
            truth_shares=truth_shares,
            processing_time_ms=processing_time
        )
    
    def reset(self):
        """Reset the protocol state for a new session."""
        self.current_epoch = 0
        for provider in self.providers.values():
            provider.weight = 1.0
            provider.accumulated_distance = 0.0
            provider.weight_shares = []
            provider.distance_shares = []


class SimplifiedTruthDiscovery:
    """
    Simplified (non-private) truth discovery for comparison and testing.
    
    Implements the same algorithm without cryptographic protection.
    """
    
    def __init__(
        self,
        num_data_providers: int,
        decay_factor: float = 0.9
    ):
        self.num_data_providers = num_data_providers
        self.decay_factor = decay_factor
        self.weights = np.ones(num_data_providers)
        self.accumulated_distances = np.zeros(num_data_providers)
        self.current_epoch = 0
    
    def run_epoch(self, sensing_values: np.ndarray) -> Tuple[float, np.ndarray]:
        """Run one epoch of truth discovery."""
        self.current_epoch += 1
        
        # Compute weighted truth
        truth = np.sum(self.weights * sensing_values) / np.sum(self.weights)
        
        # Compute squared errors
        squared_errors = (sensing_values - truth) ** 2
        
        # Update accumulated distances
        self.accumulated_distances = (
            self.accumulated_distances * self.decay_factor + squared_errors
        )
        
        # Update weights
        total_distance = np.sum(self.accumulated_distances)
        if total_distance > 0:
            self.weights = -np.log(
                self.accumulated_distances / total_distance + 1e-10
            )
            self.weights = np.maximum(self.weights, 0.01)  # Minimum weight
        
        return truth, self.weights.copy()
    
    def reset(self):
        """Reset state."""
        self.weights = np.ones(self.num_data_providers)
        self.accumulated_distances = np.zeros(self.num_data_providers)
        self.current_epoch = 0


def demonstrate_truth_discovery():
    """Demonstrate the truth discovery protocol."""
    print("=== Privacy-Preserving Truth Discovery Demo ===\n")
    
    # Setup
    num_satellites = 3
    num_providers = 5
    num_epochs = 10
    
    print(f"Configuration:")
    print(f"  Satellites: {num_satellites}")
    print(f"  Data Providers: {num_providers}")
    print(f"  Epochs: {num_epochs}\n")
    
    # Initialize protocols
    secure_td = StreamingTruthDiscovery(
        num_satellites=num_satellites,
        num_data_providers=num_providers,
        decay_factor=0.9
    )
    
    simple_td = SimplifiedTruthDiscovery(
        num_data_providers=num_providers,
        decay_factor=0.9
    )
    
    # Simulate data with one malicious provider
    np.random.seed(42)
    true_value = 0.5
    
    print("Running truth discovery over multiple epochs:\n")
    print(f"{'Epoch':<8} {'Secure Truth':<15} {'Simple Truth':<15} {'Time (ms)':<12}")
    print("-" * 50)
    
    for epoch in range(num_epochs):
        # Generate sensing values
        # Providers 0-3 are honest (small noise), Provider 4 is malicious
        sensing_values = [
            true_value + np.random.normal(0, 0.05) for _ in range(4)
        ] + [true_value + 0.5]  # Malicious provider reports higher value
        
        # Run secure protocol
        result = secure_td.run_epoch(sensing_values)
        
        # Run simple protocol for comparison
        simple_truth, _ = simple_td.run_epoch(np.array(sensing_values))
        
        print(f"{epoch+1:<8} {result.truth_value:<15.4f} {simple_truth:<15.4f} "
              f"{result.processing_time_ms:<12.2f}")
    
    print("\n" + "=" * 50)
    print("Final weights (higher = more trusted):")
    for k, w in result.weights.items():
        status = "honest" if k < 4 else "malicious"
        print(f"  Provider {k} ({status}): {w:.4f}")


if __name__ == "__main__":
    demonstrate_truth_discovery()
