# OrbitalChain Experiments Guide

This guide explains how to reproduce the experimental results from the paper.

## Overview

The experiments evaluate:
1. **Consensus Performance** (Figures 6-8): SA-SBFT vs PBFT
2. **Weight Convergence** (Figures 9-12): Truth discovery reliability
3. **Transmission Analysis** (Figures 14-16): Channel and latency characteristics
4. **Scalability** (Figures 17-19): Performance under varying network sizes

## Requirements

```bash
pip install -r requirements.txt
```

## Running All Experiments

```bash
# Run all experiments with default parameters
python -m experiments.run_all

# Results will be saved in experiments/outputs/
```

## Individual Experiments

### 1. Consensus Evaluation

Compares SA-SBFT with PBFT consensus.

```bash
python -m experiments.consensus_evaluation
```

**Parameters:**
- `--nodes`: Number of nodes (default: [10, 20, 50, 100])
- `--rounds`: Consensus rounds per configuration (default: 100)
- `--output`: Output directory (default: experiments/outputs/)

**Metrics:**
- Message complexity
- Consensus latency
- Energy consumption
- View change frequency

### 2. Weight Convergence

Evaluates truth discovery accuracy.

```bash
python -m experiments.weight_convergence
```

**Parameters:**
- `--providers`: Number of data providers (default: 10)
- `--epochs`: Number of epochs (default: 50)
- `--malicious_ratio`: Ratio of malicious providers (default: 0.2)

**Metrics:**
- Truth estimation error
- Weight convergence rate
- Malicious provider detection accuracy

### 3. Transmission Analysis

Analyzes channel characteristics.

```bash
python -m experiments.transmission_analysis
```

**Parameters:**
- `--elevations`: Elevation angles (default: [10, 30, 60, 90])
- `--distances`: Link distances in km

**Metrics:**
- Path loss
- SNR distribution
- Data rate achievable
- Bit error rate

### 4. Scalability Test

Tests system scalability.

```bash
python -m experiments.scalability_test
```

**Parameters:**
- `--max_nodes`: Maximum nodes (default: 5000)
- `--shard_sizes`: Shard sizes to test

**Metrics:**
- Throughput (TPS)
- Latency percentiles
- Resource utilization

## Configuration

Edit `config/default_config.yaml` or pass parameters via command line.

Example with custom config:
```bash
python -m experiments.consensus_evaluation --config config/custom_config.yaml
```

## Output Format

Results are saved as:
- CSV files for numerical data
- PNG/PDF for figures
- JSON for metadata

```
experiments/outputs/
├── consensus/
│   ├── latency.csv
│   ├── message_complexity.csv
│   └── figures/
├── weight_convergence/
│   ├── convergence.csv
│   └── figures/
├── transmission/
│   └── ...
└── scalability/
    └── ...
```

## Reproducing Paper Figures

Each figure can be regenerated:

```bash
# Figure 6: Message complexity
python -m experiments.consensus_evaluation --figure 6

# Figure 9: Weight convergence
python -m experiments.weight_convergence --figure 9

# All figures
python -m experiments.generate_figures
```

## Notes

- Set random seed for reproducibility: `--seed 42`
- Use `--dry-run` to check parameters without running
- Results may vary slightly due to random sampling
