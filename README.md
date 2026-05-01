# Self-Evolving Hash Function for Blockchain

A blockchain implementation where the same transaction produces a different hash in every block.

## What is this?

Normal hash functions always give the same output for the same input. This project implements a Self-Evolving Hash Function (SEHF) that includes the block number and previous block hash as part of the hashing process, making every hash unique to its block context.

**Formula:**

```
SHA-256( data + block\_number + prev\_hash )
```

## Why is this useful?

* Same transaction hashed in Block 1 and Block 2 gives different results
* Makes replay attacks harder
* No external libraries needed
* Works on top of standard SHA-256

## Requirements

* Python 3.x
* No external libraries (uses hashlib, json, time, sys — all standard)

## How to Run

```bash
git clone http://github.com/Afraz1a/Self-Evolving-Hash-Function
python blockchain.py
```

## What the Output Shows

* All block hashes
* Test 1: Cross-block uniqueness
* Test 2: Determinism
* Test 3: Chain verification
* Test 4: Tamper detection
* Test 5: Performance metrics

## Test Results

|Test|Result|
|-|-|
|Same tx in Block 1 and Block 2|Different hashes |
|Same tx twice in Block 1|Same hash |
|Tamper detection|Returns False |
|Genesis block creation|Valid hash |

## Performance

|Metric|Result|
|-|-|
|Hash generation (avg over 1000 runs)|0.0023 ms|
|Chain verification (10 blocks)|< 1 ms|
|Memory usage (10 block chain)|1.98 KB|
|Uniqueness across 5 blocks|True|

## Project Structure

```
blockchain.py   — main file with all code and tests
README.md       — this file
```

## 

