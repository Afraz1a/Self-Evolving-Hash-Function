# Self-Evolving Hash Function (SEHF)

A context-bound hash construction for lightweight blockchains. Built as a Phase 2 project — working Python prototype, Flask explorer, full test suite, and benchmark suite vs SHA-256 and SHA3-256.

**Headline numbers:** 0.0024 ms per hash · 100% replay-attack detection (50/50 scenarios) · <1 ms full chain verify (10 blocks) · 1.98 KB memory for a 10-block chain.

---

## What's the idea

Bitcoin and Ethereum bind context to every hash implicitly — through Merkle roots, nonces, timestamps, and prev_hash inside full block headers. That's powerful, but heavy. Many real systems (IoT ledgers, audit logs, supply-chain trackers) want a simpler chained-hash design where this binding is incomplete or done ad-hoc.

In a naive lightweight chain, `hash = SHA-256(transaction_data)` means identical transactions in different blocks produce **identical hashes**. Tamper detection becomes indirect — you have to walk the chain to see the inconsistency.

SEHF binds context explicitly:

```
SEHF(data, n, h_prev) = SHA-256( data || str(n) || h_prev )
```

The same transaction in block 2 produces a different hash than in block 1, because `n` and `h_prev` are different. This gives the chain native replay-attack resistance with no secret keys, no extra cryptographic machinery, and ~9.5% overhead vs plain SHA-256.

---

## Why "self-evolving"

The output evolves deterministically with block context. Same data, different position → different hash. The function isn't doing anything special; what's special is what it's hashing — domain-separated, length-prefixed, context-bound input.

This is a working primitive, not a magic one. The security argument reduces to standard SHA-256 collision resistance: any SEHF collision implies a SHA-256 collision on the injectively-encoded inputs. Inherits the 2⁻¹²⁸ bound.

---

## Repository contents

```
.
├── blockchain.py        Core primitive + Block + Blockchain classes (~200 lines)
├── app.py               Flask explorer (backend + embedded frontend, ~720 lines)
├── test_suite.py        6 test groups, 60+ assertions (~260 lines)
└── benchmark_suite.py   4 benchmark groups vs SHA-256 / SHA3-256 (~220 lines)
```

Three layers:

- **Primitive layer** — `evolving_hash(data, n, h_prev)`. Pure function, stateless, eight lines of real code. The single source of truth.
- **Chain layer** — `Block` and `Blockchain` classes. Pending transaction pool, sealing, verification, replay simulation.
- **Presentation layer** — Flask dashboard, structured test runner, quantitative benchmark suite.

---

## Quick start

```bash
# Flask is the only non-stdlib dependency
pip install flask

# Run the test suite (60+ assertions, 6 categories)
python test_suite.py

# Run the benchmark suite (vs SHA-256 and SHA3-256)
python benchmark_suite.py

# Launch the interactive explorer
python app.py
# → open http://127.0.0.1:5000
```

No virtualenv setup or external services required. Everything is in-memory.

---

## The core primitive

```python
def evolving_hash(data: str, block_no: int, prev_hash: str) -> str:
    """SEHF(data, n, h_prev) = SHA-256( data || str(n) || h_prev )"""
    combined = data + str(block_no) + prev_hash
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()
```

That's it. The whole construction. Audit-friendly by design.

A hardened version using domain separation and length prefixes (`"SEHF_v1" || len(data) || data || n || h_prev`) is described in the technical report. Both are structurally equivalent for this demonstration; the hardened version is what should ship in production.

---

## What the chain does

```python
from blockchain import Blockchain

bc = Blockchain()                          # genesis block created automatically
bc.add_block(["Alice sends 50 to Bob"])    # Block 1
bc.add_block(["Bob sends 20 to Carol"])    # Block 2

print(bc.verify_chain())                   # True
bc.chain[1].transactions = ["tampered"]    # attacker edits block 1
print(bc.verify_chain())                   # False — tamper detected

# Replay simulation
result = bc.simulate_replay("Send 100 coins", source_block_idx=1, target_block_idx=2)
print(result["attack_detected"])           # True (hashes differ because context differs)
```

Methods on the `Blockchain` class:

| Method | Purpose |
|---|---|
| `add_transaction(tx)` | Queue a transaction in the pending pool |
| `make_block()` | Seal pending transactions into a new block |
| `add_block(txs)` | Convenience: skip the pool, seal directly |
| `verify_chain()` | Recompute every hash, check linkage. Returns `bool` |
| `verify_chain_detail()` | Same, but returns structured `{valid, length, message, errors[]}` |
| `simulate_replay(tx, src, tgt)` | Compute hash of `tx` in two different block contexts |

---

## The Flask explorer

`app.py` serves an interactive dashboard at `http://127.0.0.1:5000`. The whole thing — backend, frontend, styles, scripts — is in one file.

**REST endpoints:**

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Renders the dashboard HTML |
| GET | `/api/chain` | Returns full chain, length, validity flag |
| POST | `/api/add_block` | Seals a list of transactions into a new block |
| GET | `/api/verify` | Runs `verify_chain_detail()`, returns errors[] |
| POST | `/api/simulate_replay` | Returns original/replayed hashes + detection flag |

**Dashboard features:**

- Live chain visualization with auto-refresh every 5 seconds
- Color-coded breakdown of the SEHF formula with input legend
- Transaction-add flow animation showing the four inputs feeding into the hash
- Replay attack simulator with source/target block selection and verdict banner
- Chain verifier with step-by-step checkpoints and a green/red final verdict

The frontend uses no build step — vanilla JS + CSS variables, JetBrains Mono for hex digests, Syne for headers. Dark navy theme matching the cryptographic feel.

---

## Test suite

`test_suite.py` is runnable as a single command and exits with a clean PASS/FAIL summary. Six test groups:

| # | Test | What it asserts |
|---|---|---|
| 1 | Cross-Block Uniqueness | Same transaction in 3 different blocks → 3 distinct hashes |
| 2 | Determinism | Same `(data, n, h_prev)` called 3 times → 3 identical hashes |
| 3 | Chain Verify (clean) | `verify_chain()` returns `True` on an untampered 4-block chain |
| 4 | Tamper Detection | Modifying any block's transactions → `verify_chain()` returns `False` |
| 5 | Replay Attack (50 scenarios) | 50 cross-context replays across 6 categories — all detected |
| 6 | Edge Cases | Empty tx list, 10k-char tx, Unicode (Urdu), genesis prev_hash, single-block chain, 100× repeated tx (100 unique), corrupted prev_hash |

**Replay attack scenarios cover:**

- Adjacent blocks (n → n+1) — 5 scenarios
- Distant blocks (n → n+k where k ≥ 4) — 5 scenarios
- Genesis replay (block 0 → n) — 5 scenarios
- Multi-word, numeric, reverse-direction, skip-one, far-skip, short, repeated, and special-character transactions — 30 scenarios

**Result: 50/50 detected.**

---

## Benchmark suite

`benchmark_suite.py` produces the quantitative numbers reported in the writeup.

**Four benchmarks:**

1. **Per-hash timing** (10,000 iterations) — SEHF vs plain SHA-256 vs SHA3-256
2. **Chain verification timing** — `verify_chain()` wall time at chain sizes 10, 50, 100, 500
3. **Memory usage** — `tracemalloc` peak at chain sizes 10, 50, 100, 500
4. **Replay detection overhead** — average detection time over 1,000 randomized scenarios

**Headline comparison:**

| Metric | SEHF | Plain SHA-256 | SHA3-256 |
|---|---|---|---|
| Per-hash time | ~0.0023 ms | ~0.0021 ms | ~0.0031 ms |
| Overhead vs SHA-256 | +9.5% | baseline | +47.6% |
| Context uniqueness | YES (100%) | NO | NO |
| Replay attack detection | YES (100%) | NO | NO |
| Consensus compatible | YES | YES | YES |
| Secret key required | NO | NO | NO |

**Takeaway:** SEHF adds ~9.5% per-hash overhead over plain SHA-256 — a fraction of SHA3-256's cost — while uniquely providing context uniqueness and replay-attack resistance without requiring a secret key.

---

## Security properties (with argument)

**1. Context Uniqueness.** For any fixed `data`, distinct `(n, h_prev)` pairs produce distinct SEHF outputs except with negligible probability. *Argument:* injective encoding → distinct SHA-256 inputs → distinct outputs except at collision probability.

**2. Determinism.** Given fixed `(data, n, h_prev)`, all honest nodes compute the same SEHF output. *Argument:* SHA-256 is deterministic; SEHF only adds deterministic concatenation. Required for consensus.

**3. Collision Resistance.** Inherited from SHA-256 (2⁻¹²⁸ bound). *Argument:* any SEHF collision on injectively-encoded inputs reduces directly to a SHA-256 collision on those inputs.

**Threat model:**

| Threat | SEHF defense |
|---|---|
| Replay attack across blocks | Different `(n, h_prev)` → different hash. 100% detection in tests |
| In-place tampering | Stored hash ≠ recomputed hash. Detected by `verify_chain()` |
| Block reordering / swapping | Reordered blocks have broken `prev_hash` linkages |
| Long-range edit (block k of N) | Cascade requires recomputing every subsequent hash |
| Out of scope | Sybil attacks, double-spending, network-layer attacks, key compromise (no keys to compromise) |

---

## Why not HMAC or ZK-proofs

| Alternative | Why not |
|---|---|
| HMAC | Requires secret-key management — incompatible with public consensus on permissionless lightweight chains |
| ZK-Proofs | Heavy compute and memory overhead; overkill for an integrity-only use case |
| Plain SHA-256 chains | No native context binding. Identical payloads → identical hashes. Tamper detection is derived, not direct |
| Full Bitcoin/Ethereum headers | Heavyweight (Merkle roots, nonces, timestamps) — too costly for IoT / audit-log workloads |
| **SEHF** | **Public-data only, no keys, no heavy compute. ~9.5% overhead. 100% replay detection** |

---

## Theoretical grounding

| Reference | Contribution |
|---|---|
| Nakamoto (2008) | Bitcoin's prev_hash chaining established predecessor hashes as context |
| Bellare & Rogaway (1993) | Random Oracle Model — backdrop for the injective-encoding argument |
| Bellare & Rogaway (2006) | Domain separation — motivates the `"SEHF_v1"` prefix and length-prefixed encoding |
| Preneel et al. (1993) | Hash-function taxonomy validates concatenation-based constructions when injective |
| Wood — Ethereum YP (2014) | Keccak-256 used as the Phase 3 gas-cost comparison baseline |
| Dwork & Naor (1992) | Per-block computational uniqueness — conceptual ancestor of position-binding |

---

## Roadmap (Phase 3)

1. **Solidity implementation** — SEHF as a Solidity library; deploy on Hardhat testnet; gas profiling vs keccak256
2. **Fair-baseline benchmarks** — SEHF vs Bitcoin-style double-SHA256 and Ethereum keccak256 over RLP headers at 10 / 100 / 1k / 10k / 100k blocks
3. **Extended attack simulation** — tampering, reordering, long-range, and forgery scenarios with quantitative detection rates and statistical confidence intervals
4. **Formal security argument** — full reduction-style writeup of the three claims above, with explicit threat-model boundaries
5. **Workshop / arXiv submission** — target IEEE Blockchain or IEEE ICBC workshop track; arXiv preprint as the fallback artifact

---

## Project meta

**Team:** Afrazia · Ashna · Khadija
**Mentors:** Dr. Umer Janjua · Shahzaib Cheema
**Phase:** 2 (Revised Submission)
**Stack:** Python 3.10+ · Flask 2.0+ · hashlib (stdlib) · vanilla JS frontend
**Status:** Working prototype + full test suite + benchmark suite

See `SEHF_Architecture.pdf` for the full project architecture document — layer breakdowns, data flow traces, security arguments, threat model, and benchmark methodology.
