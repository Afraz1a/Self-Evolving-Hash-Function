

import sys
import json
from blockchain import Blockchain, evolving_hash

# Enable ANSI colours on Windows (no-op on Linux/macOS)
if sys.platform == "win32":
    import os
    os.system("")          # triggers VT-100 mode in Windows Console

PASS = "\033[92m  PASSED\033[0m"
FAIL = "\033[91m  FAILED\033[0m"
SEP  = "=" * 60


def header(title):
    print(f"\n{SEP}")
    print(f"  {title}")
    print(SEP)


def check(label, condition):
    status = PASS if condition else FAIL
    print(f"  {label:<48}{status}")
    return condition



def test_cross_block_uniqueness():
    header("TEST 1: Cross-Block Uniqueness")
    print("  Same transaction data must produce a DIFFERENT hash in each block.\n")

    bc = Blockchain()
    tx = "Send 100 coins from Alice to Bob"

    b1 = bc.add_block([tx])
    b2 = bc.add_block([tx])
    b3 = bc.add_block([tx])

    print(f"  Block 1 hash: {b1.hash[:32]}...")
    print(f"  Block 2 hash: {b2.hash[:32]}...")
    print(f"  Block 3 hash: {b3.hash[:32]}...")

    all_unique = len({b1.hash, b2.hash, b3.hash}) == 3
    check("All three hashes are unique", all_unique)
    check("Block 1 != Block 2", b1.hash != b2.hash)
    check("Block 2 != Block 3", b2.hash != b3.hash)
    check("Block 1 != Block 3", b1.hash != b3.hash)

    return all_unique


def test_determinism():
    header("TEST 2: Determinism")
    print("  Same (data, block_no, prev_hash) must ALWAYS produce the same hash.\n")

    data      = "Send 50 coins"
    block_no  = 3
    prev_hash = "a" * 64

    h1 = evolving_hash(data, block_no, prev_hash)
    h2 = evolving_hash(data, block_no, prev_hash)
    h3 = evolving_hash(data, block_no, prev_hash)

    print(f"  Attempt 1: {h1[:32]}...")
    print(f"  Attempt 2: {h2[:32]}...")
    print(f"  Attempt 3: {h3[:32]}...")

    result = h1 == h2 == h3
    check("All three attempts produce identical hash", result)
    return result


def test_chain_verify_clean():
    header("TEST 3: Chain Verification (Untampered)")
    print("  verify_chain() must return True for an untouched chain.\n")

    bc = Blockchain()
    bc.add_block(["Alice sends 10 to Bob"])
    bc.add_block(["Bob sends 5 to Carol"])
    bc.add_block(["Carol sends 3 to Dave"])

    result = bc.verify_chain()
    print(f"  Chain length: {len(bc)} blocks")
    check("verify_chain() returns True", result)
    return result


def test_tamper_detection():
    header("TEST 4: Tamper Detection")
    print("  Modifying any block must cause verify_chain() to return False.\n")

    bc = Blockchain()
    bc.add_block(["Alice sends 10 to Bob"])
    bc.add_block(["Bob sends 5 to Carol"])
    bc.add_block(["Carol sends 3 to Dave"])

    # Tamper with block 1's transactions (simulates an attacker)
    print("  Tampering with Block 1 transactions...")
    bc.chain[1].transactions = ["Alice sends 9999 to Attacker"]

    result = not bc.verify_chain()   # expect False from verify_chain
    check("verify_chain() returns False after tampering", result)
    return result


def test_replay_attack():
    header("TEST 5: Replay Attack Simulation (50 Scenarios)")
    print("  A tx hash from block N must NEVER match the hash from block M (N != M).\n")

    bc = Blockchain()
    # Build a 10-block chain
    for i in range(1, 11):
        bc.add_block([f"Transaction {i}: Alice sends {i * 10} coins"])

    scenarios = [
        ("Adjacent blocks",          "Send 100 coins", 1, 2),
        ("Adjacent blocks",          "Send 100 coins", 2, 3),
        ("Adjacent blocks",          "Send 100 coins", 3, 4),
        ("Adjacent blocks",          "Send 100 coins", 4, 5),
        ("Adjacent blocks",          "Send 100 coins", 5, 6),
        ("Distant blocks",           "Send 100 coins", 1, 5),
        ("Distant blocks",           "Send 100 coins", 1, 9),
        ("Distant blocks",           "Send 100 coins", 2, 8),
        ("Distant blocks",           "Send 100 coins", 3, 7),
        ("Distant blocks",           "Send 100 coins", 4, 10),
        ("Genesis replay",           "Genesis Block",  0, 1),
        ("Genesis replay",           "Genesis Block",  0, 2),
        ("Genesis replay",           "Genesis Block",  0, 5),
        ("Genesis replay",           "Genesis Block",  0, 9),
        ("Genesis replay",           "Genesis Block",  0, 10),
        ("Multi-word tx",            "Pay rent March", 1, 3),
        ("Multi-word tx",            "Pay rent March", 2, 6),
        ("Multi-word tx",            "Pay rent March", 4, 8),
        ("Multi-word tx",            "Pay rent March", 5, 9),
        ("Multi-word tx",            "Pay rent March", 6, 10),
        ("Numeric tx",               "12345",          1, 2),
        ("Numeric tx",               "99999",          3, 7),
        ("Numeric tx",               "00000",          2, 8),
        ("Numeric tx",               "11111",          1, 10),
        ("Numeric tx",               "55555",          4, 9),
        ("Reverse direction",        "Send 50 coins",  5, 1),
        ("Reverse direction",        "Send 50 coins",  8, 2),
        ("Reverse direction",        "Send 50 coins",  10, 3),
        ("Reverse direction",        "Send 50 coins",  9, 4),
        ("Reverse direction",        "Send 50 coins",  7, 5),
        ("Skip one block",           "Transfer funds", 1, 3),
        ("Skip one block",           "Transfer funds", 2, 4),
        ("Skip one block",           "Transfer funds", 5, 7),
        ("Skip one block",           "Transfer funds", 6, 8),
        ("Skip one block",           "Transfer funds", 8, 10),
        ("Far skip",                 "Wire transfer",  1, 10),
        ("Far skip",                 "Wire transfer",  2, 9),
        ("Far skip",                 "Wire transfer",  3, 8),
        ("Far skip",                 "Wire transfer",  4, 7),
        ("Far skip",                 "Wire transfer",  5, 6),
        ("Empty-like short tx",      "x",              1, 2),
        ("Empty-like short tx",      "y",              3, 9),
        ("Empty-like short tx",      "z",              2, 7),
        ("Repeated character tx",    "aaa",            1, 5),
        ("Repeated character tx",    "bbb",            4, 8),
        ("Special characters",       "tx: 100%",       1, 3),
        ("Special characters",       "tx: <send>",     2, 6),
        ("Special characters",       "tx: {amt:50}",   3, 8),
        ("Special characters",       "tx: #hash!",     5, 9),
        ("Special characters",       "tx: @user",      6, 10),
    ]

    for cat, tx, src, tgt in scenarios:
        assert src != tgt, f"BUG in test data: src == tgt == {src} in category '{cat}'"

    passed = 0
    failed = 0
    categories = {}

    for category, tx, src, tgt in scenarios:
        result = bc.simulate_replay(tx, src, tgt)
        detected = result["attack_detected"]
        if detected:
            passed += 1
        else:
            failed += 1
            print(f"  [MISS] {category}: tx='{tx}' src={src} tgt={tgt}")
        categories.setdefault(category, []).append(detected)

    print(f"  {'Category':<30} {'Scenarios':>10} {'Detected':>10} {'Rate':>8}")
    print(f"  {'-'*30} {'-'*10} {'-'*10} {'-'*8}")
    for cat, results in categories.items():
        n = len(results)
        d = sum(results)
        print(f"  {cat:<30} {n:>10} {d:>10} {d/n*100:>7.0f}%")

    print(f"\n  Total: {passed}/50 replay attacks detected")
    check("All 50 replay attacks detected", passed == 50)
    return passed == 50



def test_edge_cases():
    header("TEST 6: Edge Cases")

    results = []

    # 6a — Empty transaction list
    try:
        bc = Blockchain()
        b = bc.add_block([])
        results.append(check("Empty transaction list produces valid hash", len(b.hash) == 64))
    except Exception as e:
        results.append(check(f"Empty tx list (error: {e})", False))

    # 6b — Very long transaction data
    try:
        bc = Blockchain()
        long_tx = "A" * 10_000
        b = bc.add_block([long_tx])
        results.append(check("10,000-char transaction produces valid hash", len(b.hash) == 64))
    except Exception as e:
        results.append(check(f"Long tx (error: {e})", False))

    # 6c — Unicode / Urdu characters
    try:
        bc = Blockchain()
        unicode_tx = "لین دین: ۱۰۰ سکے بھیجیں"
        b = bc.add_block([unicode_tx])
        results.append(check("Unicode (Urdu) transaction produces valid hash", len(b.hash) == 64))
    except Exception as e:
        results.append(check(f"Unicode tx (error: {e})", False))

    # 6d — Genesis block has correct prev_hash
    bc = Blockchain()
    genesis_ok = bc.chain[0].prev_hash == "0" * 64
    results.append(check("Genesis block uses '0'*64 as prev_hash", genesis_ok))

    # 6e — Single-block chain verification
    bc = Blockchain()
    results.append(check("Single-block chain verifies as True", bc.verify_chain()))

    # 6f — Same tx replayed 100 times, all hashes unique
    bc = Blockchain()
    hashes = set()
    tx = "Repeated transaction"
    for _ in range(100):
        b = bc.add_block([tx])
        hashes.add(b.hash)
    results.append(check("Same tx in 100 blocks → 100 unique hashes", len(hashes) == 100))

    # 6g — Tamper prev_hash field directly
    bc = Blockchain()
    bc.add_block(["tx1"])
    bc.chain[1].prev_hash = "f" * 64  # corrupt the linkage
    results.append(check("Corrupted prev_hash detected by verify_chain()", not bc.verify_chain()))

    return all(results)

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  SEHF BLOCKCHAIN — PHASE 3 FULL TEST SUITE")
    print("=" * 60)

    results = {
        "TEST 1 — Cross-Block Uniqueness"       : test_cross_block_uniqueness(),
        "TEST 2 — Determinism"                  : test_determinism(),
        "TEST 3 — Chain Verify (untampered)"    : test_chain_verify_clean(),
        "TEST 4 — Tamper Detection"             : test_tamper_detection(),
        "TEST 5 — Replay Attack (50 scenarios)" : test_replay_attack(),
        "TEST 6 — Edge Cases"                   : test_edge_cases(),
    }

    header("FINAL SUMMARY")
    all_passed = True
    for name, result in results.items():
        status = PASS if result else FAIL
        print(f"  {name:<45}{status}")
        if not result:
            all_passed = False

    print(f"\n  {'Overall: ALL TESTS PASSED' if all_passed else 'Overall: SOME TESTS FAILED'}")
    print(SEP + "\n")