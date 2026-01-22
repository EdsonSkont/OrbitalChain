# Consensus module for OrbitalChain
"""
Satellite-Adapted Smart Byzantine Fault Tolerant (SA-SBFT) consensus.

Implements consensus mechanisms optimized for LEO satellite networks with:
- Orbital-aware primary selection
- Predictive view changes
- Energy-aware role assignment
- BLS signature aggregation
"""

from .sa_sbft import (
    SASBFTConsensus,
    Satellite,
    SatelliteRole,
    ConsensusPhase,
    ConsensusMessage,
    MessageType,
    OrbitalState,
    Block,
    OrbitalReliabilityCalculator,
    ISLRouter
)

__all__ = [
    'SASBFTConsensus',
    'Satellite',
    'SatelliteRole',
    'ConsensusPhase',
    'ConsensusMessage',
    'MessageType',
    'OrbitalState',
    'Block',
    'OrbitalReliabilityCalculator',
    'ISLRouter'
]
