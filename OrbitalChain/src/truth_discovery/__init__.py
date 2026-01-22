# Truth Discovery module for OrbitalChain
"""
Privacy-preserving streaming truth discovery protocol.

Implements Algorithm 2 from the OrbitalChain paper.
"""

from .streaming_truth import (
    StreamingTruthDiscovery,
    SimplifiedTruthDiscovery,
    EpochResult,
    DataProviderState
)

__all__ = [
    'StreamingTruthDiscovery',
    'SimplifiedTruthDiscovery',
    'EpochResult',
    'DataProviderState'
]
