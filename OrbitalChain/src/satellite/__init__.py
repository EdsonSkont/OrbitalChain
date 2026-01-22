# Satellite module for OrbitalChain
"""
Satellite network utilities including orbital mechanics and channel modeling.

Modules:
    - orbital_mechanics: Keplerian orbit calculations and SGP4 propagation
    - channel_model: Rician fading channel model for satellite links
"""

from .orbital_mechanics import (
    KeplerianOrbit,
    OrbitalPropagator,
    VisibilityCalculator,
    compute_orbital_period,
    compute_visibility_window
)

from .channel_model import (
    RicianChannel,
    ISLChannel,
    compute_path_loss,
    compute_link_budget
)

__all__ = [
    'KeplerianOrbit',
    'OrbitalPropagator',
    'VisibilityCalculator',
    'compute_orbital_period',
    'compute_visibility_window',
    'RicianChannel',
    'ISLChannel',
    'compute_path_loss',
    'compute_link_budget'
]
