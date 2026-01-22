# OrbitalChain

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Paper](https://img.shields.io/badge/Paper-Tsinghua%20Science%20and%20Technology-green.svg)](link-to-paper)

> **Truth Discovery Mechanisms for Dynamic Data Streams in Inter-Satellite Communication**

## Overview

OrbitalChain is a decentralized blockchain-based data streaming system designed for LEO (Low Earth Orbit) satellite networks. It implements privacy-preserving truth discovery mechanisms to ensure data integrity and trust in inter-satellite communication without relying on intermediate trust entities.

![System Architecture](docs/images/architecture.png)

## Key Features

- 🛰️ **Sharded Blockchain Architecture**: Scalable network partitioning for parallel transaction processing across satellite shards
- 🔐 **Privacy-Preserving Truth Discovery**: Secure multi-party computation using secret sharing, Beaver triples, and garbled circuits
- 📊 **D-Stream Clustering**: Efficient real-time data stream clustering for data aggregation
- ⚡ **SA-SBFT Consensus**: Satellite-Adapted Smart Byzantine Fault Tolerant consensus with orbital awareness
- 🌍 **Orbital-Aware Operations**: Predictive view changes and energy-aware role assignment

## Performance Highlights

| Metric | Value |
|--------|-------|
| Transaction Throughput | 1,500 TPS |
| Average Consensus Latency | 100-150 ms |
| Maximum Nodes Supported | 5,000 |
| Byzantine Fault Tolerance | n/3 |
| Truth Discovery F1-Score | 91.47% |

## Repository Structure

```
OrbitalChain/
├── README.md                           # This file
├── LICENSE                             # MIT License
├── requirements.txt                    # Python dependencies
├── setup.py                            # Package installation
├── .gitignore                          # Git ignore rules
│
├── src/                                # Source code
│   ├── __init__.py
│   ├── crypto/                         # Cryptographic primitives
│   │   ├── __init__.py
│   │   ├── secret_sharing.py           # Additive secret sharing
│   │   ├── beaver_triples.py           # Beaver multiplication triples
│   │   └── garbled_circuits.py         # Garbled circuits for division/log
│   │
│   ├── truth_discovery/                # Privacy-preserving truth discovery
│   │   ├── __init__.py
│   │   └── streaming_truth.py          # Algorithm 2 implementation
│   │
│   ├── clustering/                     # Data stream clustering
│   │   ├── __init__.py
│   │   └── d_stream.py                 # Algorithm 1 (D-Stream)
│   │
│   ├── consensus/                      # Consensus mechanisms
│   │   ├── __init__.py
│   │   └── sa_sbft.py                  # Satellite-Adapted SBFT
│   │
│   └── satellite/                      # Satellite network utilities
│       ├── __init__.py
│       ├── orbital_mechanics.py        # Keplerian orbit calculations
│       └── channel_model.py            # Rician fading channel model
│
├── tests/                              # Test suite
│   ├── __init__.py
│   ├── test_crypto.py                  # Cryptographic tests
│   ├── test_truth_discovery.py         # Truth discovery tests
│   └── test_consensus.py               # Consensus tests
│
├── experiments/                        # Experimental scripts
│   ├── consensus_evaluation.py         # Figures 6-8
│   ├── weight_convergence.py           # Figures 9-12
│   ├── transmission_analysis.py        # Figures 14-16
│   └── scalability_test.py             # Figures 17-19
│
├── docs/                               # Documentation
│   ├── API.md                          # API reference
│   ├── EXPERIMENTS.md                  # Experiment guide
│   ├── SA_SBFT_IMPROVEMENTS.md         # SA-SBFT technical details
│   └── RESPONSE_LETTER.md              # Reviewer response template
│
├── latex/                              # LaTeX files for paper
│   ├── security_proofs.tex             # Formal security proofs
│   └── sa_sbft_consensus.tex           # SA-SBFT consensus section
│
├── config/                             # Configuration files
│   └── default_config.yaml             # Default parameters
│
└── data/                               # Sample data
    └── tle_samples/                    # TLE orbital data samples
        └── README.md
```

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Quick Install

```bash
# Clone the repository
git clone https://github.com/yourusername/OrbitalChain.git
cd OrbitalChain

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install package in development mode
pip install -e .
```

## Quick Start

### 1. Privacy-Preserving Truth Discovery

```python
from src.truth_discovery import StreamingTruthDiscovery

# Initialize truth discovery protocol
td = StreamingTruthDiscovery(
    num_satellites=10,
    num_data_providers=5,
    decay_factor=0.9
)

# Process sensing values
sensing_values = [0.5, 0.52, 0.48, 0.51, 0.49]
result = td.run_epoch(sensing_values)

print(f"Discovered Truth: {result.truth_value}")
print(f"Provider Weights: {result.weights}")
```

### 2. SA-SBFT Consensus

```python
from src.consensus import SASBFTConsensus, Satellite
import numpy as np

# Create satellite constellation
satellites = [Satellite(sat_id=i) for i in range(20)]

# Initialize consensus
consensus = SASBFTConsensus(
    satellites=satellites,
    shard_center=np.array([6371, 0, 0])
)

# Run consensus round
transactions = [{'tx_id': 'tx_001', 'data': 'value'}]
success, block = consensus.run_consensus(transactions, current_time=0)
```

### 3. D-Stream Clustering

```python
from src.clustering import DStreamClustering, DataPoint

# Initialize clustering
clustering = DStreamClustering(
    grid_size=0.5,
    density_threshold=2.0,
    dimensionality=2
)

# Process data stream
for i in range(100):
    point = DataPoint(
        coordinates=[np.random.randn(), np.random.randn()],
        weight=1.0,
        timestamp=float(i)
    )
    clustering.process_point(point)

# Get clusters
clusters = clustering.get_clusters()
```

## Running Experiments

```bash
# Run all experiments
python -m experiments.run_all

# Individual experiments
python -m experiments.consensus_evaluation
python -m experiments.weight_convergence
python -m experiments.transmission_analysis
```

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_crypto.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

## Core Algorithms

### Algorithm 1: D-Stream Clustering
Density-based clustering for real-time data stream processing with support for weighted data points.

### Algorithm 2: Privacy-Preserving Truth Discovery
Secure multi-party computation protocol using:
- Additive secret sharing
- Beaver multiplication triples
- Garbled circuits for division and logarithm

### Algorithm 3: SA-SBFT Consensus
Satellite-Adapted Smart Byzantine Fault Tolerant consensus with:
- Orbital-aware primary selection
- Predictive view changes
- Energy-aware role assignment
- BLS signature aggregation

## Security Properties

- **Privacy**: Individual sensing values remain hidden (Theorem 5.1-5.2)
- **Protocol Security**: Secure realization of ideal functionality (Theorem 5.3)
- **Composition Security**: Safe composition with D-Stream (Theorem 5.4)
- **Byzantine Tolerance**: Tolerates f < n/3 faulty nodes

## Citation

If you use OrbitalChain in your research, please cite:

```bibtex
@article{orbitalchain2025,
  title={OrbitalChain: Truth Discovery Mechanisms for Dynamic Data Streams 
         in Inter-Satellite Communication},
  author={Author Names},
  journal={Tsinghua Science and Technology},
  year={2025},
  volume={30},
  number={X},
  pages={XXX-XXX},
  doi={XX.XXXX/XXX}
}
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Acknowledgments

- CelesTrak for providing TLE orbital data
- National Natural Science Foundation of China (Grant No. XXXXXXXX)

## Contact

- **Authors**: [Your Name]
- **Email**: [your.email@university.edu]
- **Institution**: Chengdu University of Technology

---

**Note**: This is the official implementation accompanying the paper. For questions about the research, please contact the corresponding author.
