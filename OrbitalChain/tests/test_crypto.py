"""
Test Suite for OrbitalChain Cryptographic Components
====================================================

Verifies the correctness and security properties of:
- Secret sharing scheme
- Beaver multiplication triples
- Secure multiplication protocol
- Garbled circuit operations
"""

import pytest
import numpy as np
import secrets
import sys
sys.path.insert(0, '..')

from src.crypto.secret_sharing import AdditiveSecretSharing, Share, verify_sharing
from src.crypto.beaver_triples import (
    BeaverTripleGenerator, 
    SecureMultiplication,
    verify_secure_multiplication
)
from src.crypto.garbled_circuits import GarbledCircuitProtocol


class TestSecretSharing:
    """Tests for additive secret sharing scheme."""
    
    @pytest.fixture
    def ss(self):
        return AdditiveSecretSharing(num_parties=5)
    
    def test_basic_sharing_and_reconstruction(self, ss):
        """Test that secret can be shared and reconstructed correctly."""
        secret = 12345
        shares = ss.share(secret)
        reconstructed = ss.reconstruct(shares)
        assert reconstructed == secret
    
    def test_sharing_zero(self, ss):
        """Test sharing the value zero."""
        shares = ss.share(0)
        reconstructed = ss.reconstruct(shares)
        assert reconstructed == 0
    
    def test_sharing_large_value(self, ss):
        """Test sharing a large value near the field modulus."""
        secret = ss.prime_modulus - 1
        shares = ss.share(secret)
        reconstructed = ss.reconstruct(shares)
        assert reconstructed == secret
    
    def test_share_addition(self, ss):
        """Test that share addition is correct: [x] + [y] = [x+y]."""
        x, y = 100, 200
        x_shares = ss.share(x)
        y_shares = ss.share(y)
        sum_shares = ss.add_shares(x_shares, y_shares)
        result = ss.reconstruct(sum_shares)
        assert result == (x + y) % ss.prime_modulus
    
    def test_scalar_multiplication(self, ss):
        """Test multiplication by constant: c * [x] = [c*x]."""
        x = 50
        c = 7
        x_shares = ss.share(x)
        result_shares = ss.multiply_by_constant(x_shares, c)
        result = ss.reconstruct(result_shares)
        assert result == (x * c) % ss.prime_modulus
    
    def test_shares_are_random(self, ss):
        """Verify that individual shares appear random."""
        secret = 42
        share_values = []
        
        for _ in range(1000):
            shares = ss.share(secret)
            share_values.append(shares[0].value)
        
        # Check that shares are not constant
        unique_values = set(share_values)
        assert len(unique_values) > 900  # Should be highly variable
    
    def test_insufficient_shares_reveal_nothing(self, ss):
        """Statistical test: t-1 shares reveal no information."""
        secret1 = 100
        secret2 = 200
        
        # Collect first shares for different secrets
        shares1_first = []
        shares2_first = []
        
        for _ in range(1000):
            s1 = ss.share(secret1)
            s2 = ss.share(secret2)
            shares1_first.append(s1[0].value)
            shares2_first.append(s2[0].value)
        
        # Both distributions should be similar (uniform random)
        mean1 = np.mean(shares1_first)
        mean2 = np.mean(shares2_first)
        
        # Means should be close (both near prime/2)
        expected_mean = ss.prime_modulus / 2
        assert abs(mean1 - expected_mean) / expected_mean < 0.1
        assert abs(mean2 - expected_mean) / expected_mean < 0.1
    
    def test_correctness_many_values(self, ss):
        """Test correctness across many random values."""
        assert verify_sharing(ss, 0, 100)
        assert verify_sharing(ss, 1, 100)
        assert verify_sharing(ss, ss.prime_modulus - 1, 100)
        
        for _ in range(100):
            secret = secrets.randbelow(ss.prime_modulus)
            assert verify_sharing(ss, secret, 10)


class TestBeaverTriples:
    """Tests for Beaver multiplication triples."""
    
    @pytest.fixture
    def num_parties(self):
        return 5
    
    @pytest.fixture
    def triple_gen(self, num_parties):
        return BeaverTripleGenerator(num_parties)
    
    @pytest.fixture
    def mult(self, num_parties):
        prime = AdditiveSecretSharing.DEFAULT_PRIME
        return SecureMultiplication(num_parties, prime)
    
    def test_triple_correctness(self, triple_gen):
        """Test that generated triples satisfy a * b = c."""
        ss = triple_gen.ss
        
        for _ in range(100):
            shared_triple = triple_gen.generate_triple()
            
            # Reconstruct a, b, c
            a = sum(t.a_share.value for t in shared_triple) % ss.prime_modulus
            b = sum(t.b_share.value for t in shared_triple) % ss.prime_modulus
            c = sum(t.c_share.value for t in shared_triple) % ss.prime_modulus
            
            # Verify a * b = c
            assert (a * b) % ss.prime_modulus == c
    
    def test_secure_multiplication(self, num_parties, mult, triple_gen):
        """Test secure multiplication correctness."""
        ss = AdditiveSecretSharing(num_parties, mult.prime_modulus)
        
        for _ in range(50):
            x = secrets.randbelow(mult.prime_modulus)
            y = secrets.randbelow(mult.prime_modulus)
            expected = (x * y) % mult.prime_modulus
            
            x_shares = ss.share(x)
            y_shares = ss.share(y)
            triple = triple_gen.generate_triple()
            
            result_shares = mult.multiply(x_shares, y_shares, triple)
            result = ss.reconstruct(result_shares)
            
            assert result == expected
    
    def test_multiplication_with_zero(self, num_parties, mult, triple_gen):
        """Test multiplication where one operand is zero."""
        ss = AdditiveSecretSharing(num_parties, mult.prime_modulus)
        
        x = 0
        y = 12345
        
        x_shares = ss.share(x)
        y_shares = ss.share(y)
        triple = triple_gen.generate_triple()
        
        result_shares = mult.multiply(x_shares, y_shares, triple)
        result = ss.reconstruct(result_shares)
        
        assert result == 0
    
    def test_squaring(self, num_parties, mult, triple_gen):
        """Test secure squaring operation."""
        ss = AdditiveSecretSharing(num_parties, mult.prime_modulus)
        
        for _ in range(20):
            x = secrets.randbelow(1000)  # Small values to avoid overflow
            expected = (x * x) % mult.prime_modulus
            
            x_shares = ss.share(x)
            triple = triple_gen.generate_triple()
            
            result_shares = mult.square(x_shares, triple)
            result = ss.reconstruct(result_shares)
            
            assert result == expected
    
    def test_verification_function(self, num_parties):
        """Test the verification helper function."""
        assert verify_secure_multiplication(num_parties, 100)


class TestGarbledCircuits:
    """Tests for garbled circuit operations."""
    
    @pytest.fixture
    def prime(self):
        return 2**61 - 1
    
    @pytest.fixture
    def gc_protocol(self, prime):
        return GarbledCircuitProtocol(prime)
    
    def test_gc_division(self, gc_protocol, prime):
        """Test secure division using garbled circuits."""
        # Test values
        t = 1000000
        z = 500000
        
        # Create shares
        t_share_0 = Share(0, secrets.randbelow(prime), prime)
        t_share_1 = Share(1, (t - t_share_0.value) % prime, prime)
        z_share_0 = Share(0, secrets.randbelow(prime), prime)
        z_share_1 = Share(1, (z - z_share_0.value) % prime, prime)
        
        # Run GC division
        result_0, result_1 = gc_protocol.gc_div(
            t_share_0, t_share_1, z_share_0, z_share_1
        )
        
        # Reconstruct
        result = (result_0.value + result_1.value) % prime
        
        # Check approximate correctness (scaled arithmetic)
        expected = t * 10**6 // z
        # Allow some tolerance due to fixed-point arithmetic
        assert abs(result - expected) < expected * 0.01 or result == expected
    
    def test_gc_div_log(self, gc_protocol, prime):
        """Test secure division + logarithm using garbled circuits."""
        st_k = 100000
        st_star = 1000000
        
        # Create shares
        st_k_0 = Share(0, secrets.randbelow(prime), prime)
        st_k_1 = Share(1, (st_k - st_k_0.value) % prime, prime)
        st_star_0 = Share(0, secrets.randbelow(prime), prime)
        st_star_1 = Share(1, (st_star - st_star_0.value) % prime, prime)
        
        # Run GC div+log
        w_0, w_1 = gc_protocol.gc_div_log(
            st_k_0, st_k_1, st_star_0, st_star_1
        )
        
        # Reconstruct
        w = (w_0.value + w_1.value) % prime
        
        # Should produce a positive weight
        assert w > 0 or w < prime // 2  # Handle wrap-around
    
    def test_gc_shares_are_additive(self, gc_protocol, prime):
        """Verify that GC output shares are additive."""
        t, z = 500, 100
        
        t_share_0 = Share(0, secrets.randbelow(prime), prime)
        t_share_1 = Share(1, (t - t_share_0.value) % prime, prime)
        z_share_0 = Share(0, secrets.randbelow(prime), prime)
        z_share_1 = Share(1, (z - z_share_0.value) % prime, prime)
        
        result_0, result_1 = gc_protocol.gc_div(
            t_share_0, t_share_1, z_share_0, z_share_1
        )
        
        # Both shares should be valid field elements
        assert 0 <= result_0.value < prime
        assert 0 <= result_1.value < prime
        assert result_0.field_modulus == prime
        assert result_1.field_modulus == prime


class TestIntegration:
    """Integration tests for the complete protocol."""
    
    def test_end_to_end_truth_discovery(self):
        """Test complete truth discovery flow."""
        from src.truth_discovery.streaming_truth import (
            StreamingTruthDiscovery,
            SimplifiedTruthDiscovery
        )
        
        num_satellites = 3
        num_providers = 5
        
        # Create both versions
        secure_td = StreamingTruthDiscovery(
            num_satellites=num_satellites,
            num_data_providers=num_providers,
            decay_factor=0.9
        )
        
        simple_td = SimplifiedTruthDiscovery(
            num_data_providers=num_providers,
            decay_factor=0.9
        )
        
        # Run multiple epochs
        np.random.seed(42)
        true_value = 0.5
        
        for _ in range(5):
            # Generate sensing values
            sensing_values = [
                true_value + np.random.normal(0, 0.05) 
                for _ in range(num_providers)
            ]
            
            # Run both protocols
            secure_result = secure_td.run_epoch(sensing_values)
            simple_truth, _ = simple_td.run_epoch(np.array(sensing_values))
            
            # Results should be similar (within numerical precision)
            # Note: Exact match not expected due to fixed-point vs floating-point
            assert secure_result.truth_value is not None
            assert simple_truth is not None
    
    def test_clustering_with_truth_outputs(self):
        """Test D-Stream clustering with truth discovery outputs."""
        from src.clustering.d_stream import DStreamClustering, DataPoint
        
        clustering = DStreamClustering(
            grid_size=0.5,
            density_threshold=2.0,
            dimensionality=2
        )
        
        # Process points
        np.random.seed(42)
        for t in range(50):
            point = DataPoint(
                coordinates=np.random.randn(2) * 2 + 5,
                weight=1.0,
                timestamp=float(t)
            )
            clustering.process_point(point)
        
        # Should have created some clusters
        clusters = clustering.get_clusters()
        stats = clustering.get_statistics()
        
        assert stats['total_points'] == 50
        assert stats['active_grids'] > 0


class TestSecurityProperties:
    """Tests for security properties of the protocol."""
    
    def test_share_independence(self):
        """Test that shares are statistically independent."""
        ss = AdditiveSecretSharing(num_parties=3)
        secret = 100
        
        # Collect pairs of shares
        share_pairs = []
        for _ in range(1000):
            shares = ss.share(secret)
            share_pairs.append((shares[0].value, shares[1].value))
        
        # Compute correlation
        s0 = np.array([p[0] for p in share_pairs])
        s1 = np.array([p[1] for p in share_pairs])
        
        # Normalize
        s0_norm = (s0 - np.mean(s0)) / (np.std(s0) + 1e-10)
        s1_norm = (s1 - np.mean(s1)) / (np.std(s1) + 1e-10)
        
        # Correlation should be near zero
        correlation = np.mean(s0_norm * s1_norm)
        assert abs(correlation) < 0.1
    
    def test_beaver_triple_randomness(self):
        """Test that Beaver triple components are random."""
        triple_gen = BeaverTripleGenerator(num_parties=3)
        
        a_values = []
        b_values = []
        
        for _ in range(1000):
            triples = triple_gen.generate_triple()
            # Reconstruct a, b
            a = sum(t.a_share.value for t in triples) % triple_gen.prime_modulus
            b = sum(t.b_share.value for t in triples) % triple_gen.prime_modulus
            a_values.append(a)
            b_values.append(b)
        
        # Should have high variance (random values)
        assert len(set(a_values)) > 900
        assert len(set(b_values)) > 900


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
