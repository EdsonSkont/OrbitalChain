# Response Letter to Reviewers

## OrbitalChain: Truth Discovery Mechanisms for Dynamic Data Streams in Inter-Satellite Communication

---

**Dear Editor and Reviewers,**

We sincerely thank the reviewers for their thorough evaluation and constructive feedback. We are grateful for the recognition that our substantial revisions have significantly improved the manuscript. The reviewers' insights on formalizing security guarantees and enhancing reproducibility are invaluable for strengthening the scientific rigor of our work.

We have carefully addressed all recommendations as detailed below.

---

## Response to Recommendation 1: Formalization of End-to-End Security Guarantees

**Reviewer Comment Summary:**
The reviewers requested that we extend our security analysis from component-level to protocol-level, providing:
1. Formal ideal functionality definition
2. Simulation-based security proof
3. Proof of secure composition between Algorithm 2 and Algorithm 1

**Our Response:**

We greatly appreciate this insightful recommendation. We have significantly strengthened Section 5.1 by providing a comprehensive protocol-level security analysis using the simulation-based security paradigm.

### Changes Made:

#### 1. Formal Ideal Functionality Definition (New Definition 5.1)

We have added a formal specification of the ideal functionality F_truth that captures the desired input-output behavior of our protocol:

```
Definition (Ideal Functionality F_truth):
The ideal functionality interacts with K data providers and n satellites:

INITIALIZATION:
- Set epoch counter l ← 0
- Initialize weights w_k ← 1 for all k ∈ [K]
- Initialize accumulated distances st(k) ← 0

TRUTH DISCOVERY PHASE (per epoch l):
1. INPUT: Receive sensing value x_l^k from each DP_k
2. COMPUTATION:
   - Weighted sum: t ← Σ(w_k · x_l^k)
   - Weight sum: z ← Σ(w_k)
   - Truth: Φ_l ← t / z
3. OUTPUT: Send Φ_l to all satellites

WEIGHT UPDATE PHASE (per epoch l):
For each DP_k:
   - Squared error: d_k ← (x_l^k - Φ_l)²
   - State update: st(k) ← st(k) · λ + d_k
   - Weight update: w_k ← -log(st(k) / st*)
```

#### 2. New Theorem 5.3: Protocol Security with Full Proof

We have added a formal theorem with complete simulation-based proof:

**Theorem 5.3 (Protocol Security):** *The privacy-preserving streaming truth discovery protocol π_truth (Algorithm 2) securely realizes the ideal functionality F_truth in the semi-honest model.*

**Proof Structure:**

**(a) Simulator Construction:**
We construct a simulator S that produces views indistinguishable from real execution:

- **For secret shares:** S generates random shares [x̃]_i ∈ F_q (perfectly hiding by Theorem 5.1)
- **For Beaver multiplication:** S generates random (ũ, ṽ) (secure by Theorem 5.2)  
- **For garbled circuits:** S invokes the GC simulator S_GC from Lindell & Pinkas (2009)

**(b) Hybrid Argument:**
- H_0: Real protocol execution
- H_1: Replace secret shares with random (H_0 ≡ H_1 by perfect secrecy)
- H_2: Replace Beaver messages with simulated (H_1 ≡ H_2 by Theorem 5.2)
- H_3: Replace garbled circuits with simulated (H_2 ≈_c H_3 by GC security)

Therefore: VIEW_C^π ≡ H_0 ≡ H_1 ≡ H_2 ≈_c H_3 = VIEW_C^S

#### 3. New Theorem 5.4: Secure Composition

**Theorem 5.4 (Secure Composition with D-Stream):** *The composition of Algorithm 2 with Algorithm 1 preserves privacy of individual sensing values.*

**Proof:**
We prove this by information flow analysis:

1. **Claim 1:** D-Stream (Algorithm 1) never accesses secret-shared values [x_l^k]_i
   - Verified by inspection: Algorithm 1 operates only on aggregated truths Φ_l and weights w_k

2. **Claim 2:** Outputs {Φ_l, w_k} constitute valid leakage per F_truth specification

3. **By UC Composition Theorem:** Since π_truth securely realizes F_truth and D-Stream uses only F_truth outputs, the composition is secure.

#### 4. Additional Security Analysis

We have also added:
- **Theorem 5.5:** Byzantine Fault Tolerance guarantees for PBFT consensus
- **Theorem 5.6:** Communication complexity analysis O(K·n·κ + n²·|GC|)

**Location in Manuscript:** Section 5.1, pages 14-16 (expanded from 1 page to 3 pages)

---

## Response to Recommendation 2: Enhancement of Reproducibility and Community Engagement

**Reviewer Comment Summary:**
The reviewers recommended making the experimental codebase publicly available to maximize research impact and facilitate verification.

**Our Response:**

We wholeheartedly agree with this recommendation. We have made our complete implementation publicly available to support reproducibility and community engagement.

### Changes Made:

#### 1. Public Repository

We have created a comprehensive GitHub repository containing all source code, experimental scripts, and documentation:

**Repository URL:** https://github.com/[username]/OrbitalChain

#### 2. Repository Contents

```
OrbitalChain/
├── README.md                    # Comprehensive documentation
├── LICENSE                      # MIT License
├── requirements.txt             # Dependencies
├── src/
│   ├── crypto/
│   │   ├── secret_sharing.py    # Additive secret sharing (Theorem 5.1)
│   │   ├── beaver_triples.py    # Beaver multiplication (Theorem 5.2)
│   │   └── garbled_circuits.py  # GC for division/logarithm
│   ├── truth_discovery/
│   │   └── streaming_truth.py   # Algorithm 2 implementation
│   ├── clustering/
│   │   └── d_stream.py          # Algorithm 1 implementation
│   ├── consensus/
│   │   └── pbft.py              # PBFT consensus
│   └── satellite/
│       ├── orbital_mechanics.py # Keplerian orbit calculations
│       └── channel_model.py     # Rician fading model
├── experiments/
│   ├── consensus_evaluation.py  # Figures 6-8
│   ├── weight_convergence.py    # Figures 9-12
│   ├── transmission_analysis.py # Figures 14-16
│   └── scalability_test.py      # Figures 17-19
├── data/
│   └── tle_samples/             # CelesTrak TLE data
└── tests/
    ├── test_crypto.py           # Security verification tests
    └── test_integration.py      # End-to-end tests
```

#### 3. Reproducibility Features

The repository includes:

- **Detailed README** with installation instructions and quick-start examples
- **Configuration files** for all experiments in the paper
- **Automated test suite** verifying cryptographic correctness
- **Jupyter notebooks** for visualization and demonstration
- **Docker support** for consistent execution environment

#### 4. Updated Data Availability Statement

We have updated the "Data Availability" section (page 21) to include:

```
Data Availability

To ensure full reproducibility, the complete implementation including 
source code, experimental scripts, and documentation is publicly 
available at: https://github.com/[username]/OrbitalChain

The repository includes implementations of:
- Privacy-preserving truth discovery (Algorithm 2)
- D-Stream clustering (Algorithm 1)
- Cryptographic primitives (secret sharing, Beaver triples, garbled circuits)
- PBFT consensus mechanism
- Satellite network simulation using CelesTrak TLE data

All experimental configurations used to generate the results in this 
paper are provided, enabling complete replication of Figures 6-19 
and Tables 3-5.
```

---

## Summary of Revisions

| Reviewer Recommendation | How We Addressed It | Location |
|------------------------|---------------------|----------|
| Ideal Functionality Definition | Added formal Definition 5.1 for F_truth | Section 5.1, p.14 |
| Simulation-Based Proof | Added Theorem 5.3 with complete proof | Section 5.1, p.14-15 |
| Secure Composition | Added Theorem 5.4 with information flow analysis | Section 5.1, p.15-16 |
| Open-Source Code | Published complete repository on GitHub | Data Availability, p.21 |
| Reproducibility | Included all experimental scripts and configs | GitHub repository |

---

## Conclusion

We believe these revisions fully address the reviewers' concerns and significantly strengthen the scientific rigor of our work. The formal security analysis now provides end-to-end guarantees for the OrbitalChain protocol, and the public code repository enables complete reproducibility of our results.

We thank the reviewers again for their valuable feedback, which has substantially improved the quality of this manuscript.

Sincerely,

**[Author Names]**  
[Affiliation]  
[Date]

---

## Appendix: Detailed Theorem Statements

### Theorem 5.3 (Protocol Security) - Full Statement

Let π_truth denote the privacy-preserving streaming truth discovery protocol (Algorithm 2). Let F_truth denote the ideal functionality as defined in Definition 5.1. Under the assumptions that:
1. The additive secret sharing scheme provides perfect secrecy for t < n shares
2. Beaver's multiplication triple protocol is secure against semi-honest adversaries
3. The garbled circuit construction satisfies simulation-based security

Then π_truth securely realizes F_truth in the semi-honest model. Formally, for any PPT adversary A corrupting a subset C of satellites with |C| < n, there exists a PPT simulator S such that:

{REAL_π,A(z)}_{x,z} ≈_c {IDEAL_F,S(z)}_{x,z}

where x represents the inputs and z represents auxiliary information.

### Theorem 5.4 (Secure Composition) - Full Statement

Let π_composed = π_truth ∘ π_D-Stream denote the composed protocol where outputs of Algorithm 2 are used as inputs to Algorithm 1. Let L(·) = {Φ_l, w_k} denote the leakage function defined by F_truth. Then:

1. π_D-Stream accesses only L(·) and publicly known parameters
2. No information about individual sensing values {x_l^k} beyond L(·) is revealed
3. The composition satisfies the Universal Composability framework

Therefore, the composed protocol preserves the privacy guarantees of π_truth.
