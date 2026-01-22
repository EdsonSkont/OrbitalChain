# OrbitalChain API Reference

## Overview

This document provides API reference for the main OrbitalChain modules.

---

## Crypto Module (`src.crypto`)

### AdditiveSecretSharing

```python
from src.crypto import AdditiveSecretSharing, Share

ss = AdditiveSecretSharing(num_parties=5, prime_modulus=None)
```

**Parameters:**
- `num_parties` (int): Number of parties to share secrets among
- `prime_modulus` (int, optional): Prime for finite field. Default: 2^61 - 1

**Methods:**

#### `share(secret: int) -> List[Share]`
Split a secret into n additive shares.

#### `reconstruct(shares: List[Share]) -> int`
Reconstruct the secret from all shares.

#### `add_shares(shares_x, shares_y) -> List[Share]`
Add two secret-shared values locally.

#### `multiply_by_constant(shares, constant) -> List[Share]`
Multiply secret-shared value by a public constant.

---

### BeaverTripleGenerator

```python
from src.crypto import BeaverTripleGenerator, SecureMultiplication

gen = BeaverTripleGenerator(num_parties=5)
mult = SecureMultiplication(num_parties=5)
```

**Methods:**

#### `generate_triple() -> List[SharedTriple]`
Generate a random Beaver multiplication triple (a, b, c) where a*b = c.

#### `SecureMultiplication.multiply(x_shares, y_shares, triple) -> List[Share]`
Securely multiply two secret-shared values.

---

### GarbledCircuitProtocol

```python
from src.crypto import GarbledCircuitProtocol

gc = GarbledCircuitProtocol(prime_modulus)
```

**Methods:**

#### `gc_div(t_0, t_1, z_0, z_1) -> Tuple[Share, Share]`
Secure division: Φ = t / z

#### `gc_div_log(st_k_0, st_k_1, st_star_0, st_star_1) -> Tuple[Share, Share]`
Secure division + logarithm: w = -log(st_k / st*)

---

## Truth Discovery Module (`src.truth_discovery`)

### StreamingTruthDiscovery

```python
from src.truth_discovery import StreamingTruthDiscovery

td = StreamingTruthDiscovery(
    num_satellites=10,
    num_data_providers=5,
    decay_factor=0.9,
    prime_modulus=None
)
```

**Parameters:**
- `num_satellites` (int): Number of satellites in MPC
- `num_data_providers` (int): Number of data providers
- `decay_factor` (float): λ parameter (0 < λ ≤ 1)
- `prime_modulus` (int, optional): Prime for finite field

**Methods:**

#### `run_epoch(sensing_values: List[float]) -> EpochResult`
Run one epoch of truth discovery.

**Returns:** `EpochResult` with:
- `epoch` (int): Epoch number
- `truth_value` (float): Discovered truth
- `weights` (Dict[int, float]): Updated weights
- `processing_time_ms` (float): Processing time

#### `reset()`
Reset protocol state for new session.

---

## Clustering Module (`src.clustering`)

### DStreamClustering

```python
from src.clustering import DStreamClustering, DataPoint

clustering = DStreamClustering(
    grid_size=0.5,
    density_threshold=2.0,
    decay_factor=0.998,
    gap_time=10.0,
    dimensionality=2
)
```

**Parameters:**
- `grid_size` (float): Size of grid cells
- `density_threshold` (float): Threshold for dense grids
- `decay_factor` (float): Decay factor for density
- `gap_time` (float): Time between clustering adjustments
- `dimensionality` (int): Number of dimensions

**Methods:**

#### `process_point(point: DataPoint) -> Optional[Tuple[int, ...]]`
Process a single data point from stream.

#### `get_clusters() -> Dict[int, List[Tuple[int, ...]]]`
Get current clusters.

#### `get_cluster_centers() -> Dict[int, np.ndarray]`
Get center of mass for each cluster.

#### `predict_cluster(point: DataPoint) -> Optional[int]`
Predict cluster for new point.

---

## Consensus Module (`src.consensus`)

### SASBFTConsensus

```python
from src.consensus import SASBFTConsensus, Satellite
import numpy as np

satellites = [Satellite(sat_id=i) for i in range(20)]
consensus = SASBFTConsensus(
    satellites=satellites,
    shard_center=np.array([6371, 0, 0]),
    epsilon=1.2
)
```

**Parameters:**
- `satellites` (List[Satellite]): Satellite nodes
- `shard_center` (np.ndarray): Geographic shard center
- `epsilon` (float): Threshold adjustment (1.0-1.5)
- `checkpoint_interval` (int): Rounds between checkpoints
- `view_change_timeout` (float): Timeout in seconds

**Methods:**

#### `run_consensus(transactions, current_time) -> Tuple[bool, Optional[Block]]`
Run SA-SBFT consensus on transactions.

#### `classify_nodes(current_time) -> Dict[int, float]`
Classify satellites into Active/Semi-Active/Dormant.

#### `predictive_view_change(current_time) -> bool`
Check and execute predictive view change.

#### `create_checkpoint() -> Dict`
Create checkpoint for recovery.

---

## Satellite Module (`src.satellite`)

### KeplerianOrbit

```python
from src.satellite import KeplerianOrbit

orbit = KeplerianOrbit(
    a=6921,  # Semi-major axis (km)
    e=0.0001,  # Eccentricity
    i=0.925,  # Inclination (rad)
    omega=0,  # Arg of perigee (rad)
    Omega=0,  # RAAN (rad)
    nu=0,  # True anomaly (rad)
    epoch=2460000.5  # Julian date
)
```

**Properties:**
- `period` (float): Orbital period in seconds
- `altitude` (float): Current altitude in km

**Methods:**

#### `to_state_vector() -> Tuple[np.ndarray, np.ndarray]`
Convert to (position, velocity) in ECI frame.

#### `from_tle(tle_line1, tle_line2) -> KeplerianOrbit`
Parse TLE to Keplerian elements.

---

### SatelliteLink

```python
from src.satellite import SatelliteLink, LinkParameters

params = LinkParameters(
    frequency=26.5e9,
    transmit_power=10,
    transmit_gain=35,
    receive_gain=40,
    system_noise_temp=300,
    bandwidth=500e6
)
link = SatelliteLink(params, channel_type='rician')
```

**Methods:**

#### `compute_link_quality(distance, elevation) -> Dict`
Compute comprehensive link quality metrics.

**Returns:**
- `effective_snr_dB` (float): Effective SNR
- `data_rate_bps` (float): Achievable data rate
- `latency_ms` (float): Propagation latency
- `ber` (float): Bit error rate estimate

---

## Data Classes

### Share
```python
@dataclass
class Share:
    party_id: int
    value: int
    field_modulus: int
```

### DataPoint
```python
@dataclass
class DataPoint:
    coordinates: np.ndarray
    weight: float
    timestamp: float
```

### Satellite
```python
@dataclass
class Satellite:
    sat_id: int
    reputation: float = 1.0
    energy: float = 1.0
    orbital_state: OrbitalState = None
    role: SatelliteRole = SatelliteRole.DORMANT
```

### Block
```python
@dataclass
class Block:
    height: int
    transactions: List[Dict]
    prev_hash: str
    timestamp: float
```

---

## Examples

See `README.md` for quick start examples and `experiments/` for complete usage examples.
