"""
Beaver Multiplication Triples for OrbitalChain
==============================================

Implements Beaver's technique for secure multiplication of secret-shared values.

References:
    - Beaver, D. (1992). Efficient multiparty protocols using circuit randomization.
    - OrbitalChain Paper, Section 4.7
"""

import secrets
from typing import List, Tuple, Optional
from dataclasses import dataclass
import numpy as np

from .secret_sharing import AdditiveSecretSharing, Share


@dataclass
class BeaverTriple:
    """
    A Beaver multiplication triple (a, b, c) where a * b = c (mod q).
    
    Used to securely compute multiplication of secret-shared values
    without revealing the inputs.
    """
    a: int
    b: int
    c: int
    field_modulus: int
    
    def verify(self) -> bool:
        """Verify that a * b = c (mod q)."""
        return (self.a * self.b) % self.field_modulus == self.c
    
    def __repr__(self):
        return f"BeaverTriple(a={self.a}, b={self.b}, c={self.c})"


@dataclass 
class SharedTriple:
    """Shares of a Beaver triple held by a single party."""
    party_id: int
    a_share: Share
    b_share: Share
    c_share: Share
    
    def __repr__(self):
        return f"SharedTriple(party={self.party_id})"


class BeaverTripleGenerator:
    """
    Generator for Beaver multiplication triples.
    
    In the OrbitalChain system, data providers generate and distribute
    multiplication triples to satellites for use in secure computation.
    
    Security Property:
        Given shares of (a, b, c), no party learns anything about the
        actual values without combining all shares.
    
    Example:
        >>> gen = BeaverTripleGenerator(num_parties=3)
        >>> shared_triples = gen.generate_triple()
        >>> # Each party receives their SharedTriple
        >>> # Later, use for secure multiplication
    """
    
    def __init__(
        self, 
        num_parties: int, 
        prime_modulus: Optional[int] = None
    ):
        """
        Initialize the generator.
        
        Args:
            num_parties: Number of parties to share triples among
            prime_modulus: Prime defining the finite field
        """
        self.num_parties = num_parties
        self.ss = AdditiveSecretSharing(num_parties, prime_modulus)
        self.prime_modulus = self.ss.prime_modulus
    
    def generate_triple(self) -> List[SharedTriple]:
        """
        Generate a random Beaver triple and share it among all parties.
        
        Algorithm:
            1. Generate random a, b from F_q
            2. Compute c = a * b (mod q)
            3. Secret-share (a, b, c) among all parties
        
        Returns:
            List of SharedTriple objects, one per party
        """
        # Generate random a and b
        a = secrets.randbelow(self.prime_modulus)
        b = secrets.randbelow(self.prime_modulus)
        
        # Compute c = a * b
        c = (a * b) % self.prime_modulus
        
        # Create the triple
        triple = BeaverTriple(a, b, c, self.prime_modulus)
        assert triple.verify(), "Triple verification failed"
        
        # Share each component
        a_shares = self.ss.share(a)
        b_shares = self.ss.share(b)
        c_shares = self.ss.share(c)
        
        # Combine into SharedTriple objects
        shared_triples = [
            SharedTriple(
                party_id=i,
                a_share=a_shares[i],
                b_share=b_shares[i],
                c_share=c_shares[i]
            )
            for i in range(self.num_parties)
        ]
        
        return shared_triples
    
    def generate_batch(self, count: int) -> List[List[SharedTriple]]:
        """
        Generate multiple triples efficiently.
        
        Args:
            count: Number of triples to generate
        
        Returns:
            List of shared triple lists
        """
        return [self.generate_triple() for _ in range(count)]


class SecureMultiplication:
    """
    Secure multiplication protocol using Beaver triples.
    
    Allows two parties holding shares of x and y to compute shares
    of x * y without revealing x or y.
    
    Protocol (Beaver's Method):
        Given [x], [y], and pre-shared triple ([a], [b], [c]):
        1. Each party computes and broadcasts:
           - u_i = [x]_i - [a]_i
           - v_i = [y]_i - [b]_i
        2. All parties reconstruct u = x - a and v = y - b
        3. Each party computes their share of x*y:
           [x*y]_i = u*v/n + u*[b]_i + v*[a]_i + [c]_i
    
    Security:
        - u and v are masked by random a and b, revealing nothing about x, y
        - The protocol is secure against semi-honest adversaries
    """
    
    def __init__(
        self, 
        num_parties: int,
        prime_modulus: Optional[int] = None
    ):
        """
        Initialize the secure multiplication protocol.
        
        Args:
            num_parties: Number of parties
            prime_modulus: Field modulus
        """
        self.num_parties = num_parties
        self.ss = AdditiveSecretSharing(num_parties, prime_modulus)
        self.prime_modulus = self.ss.prime_modulus
    
    def multiply(
        self,
        x_shares: List[Share],
        y_shares: List[Share],
        triple: List[SharedTriple]
    ) -> List[Share]:
        """
        Securely multiply two secret-shared values.
        
        Args:
            x_shares: Shares of the first value [x]
            y_shares: Shares of the second value [y]  
            triple: Pre-shared Beaver triple
        
        Returns:
            Shares of the product [x * y]
        """
        n = self.num_parties
        q = self.prime_modulus
        
        # Step 1: Compute masked differences for each party
        u_shares = []  # u = x - a
        v_shares = []  # v = y - b
        
        for i in range(n):
            u_i = (x_shares[i].value - triple[i].a_share.value) % q
            v_i = (y_shares[i].value - triple[i].b_share.value) % q
            u_shares.append(u_i)
            v_shares.append(v_i)
        
        # Step 2: Simulate broadcast - all parties learn u and v
        # In real implementation, this would involve communication
        u = sum(u_shares) % q
        v = sum(v_shares) % q
        
        # Step 3: Each party computes their share of x*y
        # [x*y]_i = u*v/n + u*[b]_i + v*[a]_i + [c]_i
        # Note: We need to distribute u*v among parties
        
        result_shares = []
        uv_term = (u * v) % q
        
        for i in range(n):
            # First party gets the u*v term, others get 0
            # This is one way to handle the public term distribution
            if i == 0:
                uv_component = uv_term
            else:
                uv_component = 0
            
            # Compute the share
            share_value = (
                uv_component +
                (u * triple[i].b_share.value) % q +
                (v * triple[i].a_share.value) % q +
                triple[i].c_share.value
            ) % q
            
            result_shares.append(Share(
                party_id=i,
                value=share_value,
                field_modulus=q
            ))
        
        return result_shares
    
    def multiply_by_constant(
        self,
        shares: List[Share],
        constant: int
    ) -> List[Share]:
        """
        Multiply secret-shared value by a public constant.
        
        This is a local operation - no Beaver triple needed.
        
        Args:
            shares: Shares of the value
            constant: Public constant
        
        Returns:
            Shares of the product
        """
        return self.ss.multiply_by_constant(shares, constant)
    
    def square(
        self,
        x_shares: List[Share],
        triple: List[SharedTriple]
    ) -> List[Share]:
        """
        Securely compute the square of a secret-shared value.
        
        Args:
            x_shares: Shares of the value
            triple: Beaver triple
        
        Returns:
            Shares of x^2
        """
        return self.multiply(x_shares, x_shares, triple)


class BatchMultiplication:
    """
    Efficient batch multiplication for multiple operations.
    
    Useful when performing many multiplications in the truth discovery protocol.
    """
    
    def __init__(
        self,
        num_parties: int,
        prime_modulus: Optional[int] = None
    ):
        self.num_parties = num_parties
        self.prime_modulus = prime_modulus or AdditiveSecretSharing.DEFAULT_PRIME
        self.mult = SecureMultiplication(num_parties, prime_modulus)
        self.triple_gen = BeaverTripleGenerator(num_parties, prime_modulus)
    
    def batch_multiply(
        self,
        x_shares_list: List[List[Share]],
        y_shares_list: List[List[Share]],
        triples: List[List[SharedTriple]]
    ) -> List[List[Share]]:
        """
        Perform multiple secure multiplications.
        
        Args:
            x_shares_list: List of share lists for first operands
            y_shares_list: List of share lists for second operands
            triples: Pre-generated Beaver triples
        
        Returns:
            List of share lists for products
        """
        if len(x_shares_list) != len(y_shares_list):
            raise ValueError("Input lists must have same length")
        if len(x_shares_list) != len(triples):
            raise ValueError("Need one triple per multiplication")
        
        results = []
        for x_shares, y_shares, triple in zip(x_shares_list, y_shares_list, triples):
            product = self.mult.multiply(x_shares, y_shares, triple)
            results.append(product)
        
        return results
    
    def prepare_triples(self, count: int) -> List[List[SharedTriple]]:
        """
        Pre-generate triples for batch operations.
        
        Args:
            count: Number of triples needed
        
        Returns:
            List of shared triples
        """
        return self.triple_gen.generate_batch(count)


def verify_secure_multiplication(
    num_parties: int = 3,
    num_tests: int = 100
) -> bool:
    """
    Verify correctness of secure multiplication.
    
    Args:
        num_parties: Number of parties
        num_tests: Number of test iterations
    
    Returns:
        True if all tests pass
    """
    ss = AdditiveSecretSharing(num_parties)
    mult = SecureMultiplication(num_parties, ss.prime_modulus)
    triple_gen = BeaverTripleGenerator(num_parties, ss.prime_modulus)
    
    for _ in range(num_tests):
        # Generate random x and y
        x = secrets.randbelow(ss.prime_modulus)
        y = secrets.randbelow(ss.prime_modulus)
        
        # Expected result
        expected = (x * y) % ss.prime_modulus
        
        # Share x and y
        x_shares = ss.share(x)
        y_shares = ss.share(y)
        
        # Generate triple
        triple = triple_gen.generate_triple()
        
        # Secure multiplication
        result_shares = mult.multiply(x_shares, y_shares, triple)
        
        # Reconstruct and verify
        result = ss.reconstruct(result_shares)
        
        if result != expected:
            print(f"FAILED: {x} * {y} = {expected}, got {result}")
            return False
    
    return True


if __name__ == "__main__":
    print("=== Beaver Multiplication Triples Demo ===\n")
    
    # Setup
    num_parties = 5
    ss = AdditiveSecretSharing(num_parties)
    mult = SecureMultiplication(num_parties, ss.prime_modulus)
    triple_gen = BeaverTripleGenerator(num_parties, ss.prime_modulus)
    
    # Test values
    x = 7
    y = 6
    expected = x * y
    
    print(f"Computing {x} * {y} securely among {num_parties} parties\n")
    
    # Share values
    x_shares = ss.share(x)
    y_shares = ss.share(y)
    print(f"Shares of x={x}: {[s.value for s in x_shares]}")
    print(f"Shares of y={y}: {[s.value for s in y_shares]}\n")
    
    # Generate Beaver triple
    triple = triple_gen.generate_triple()
    print("Beaver triple generated and shared\n")
    
    # Secure multiplication
    result_shares = mult.multiply(x_shares, y_shares, triple)
    result = ss.reconstruct(result_shares)
    
    print(f"Result shares: {[s.value for s in result_shares]}")
    print(f"Reconstructed result: {result}")
    print(f"Expected: {expected}")
    print(f"Correct: {result == expected}\n")
    
    # Run verification tests
    print("Running 100 verification tests...")
    success = verify_secure_multiplication(num_parties, 100)
    print(f"All tests passed: {success}")
