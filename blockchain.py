import hashlib
import json
import time
import sys

def evolving_hash(data, block_no, prev_hash):
    text = data + str(block_no) + prev_hash
    return hashlib.sha256(text.encode()).hexdigest()

class Block:
    def __init__(self, index, transactions, prev_hash):
        self.index = index
        self.timestamp = time.time()
        self.transactions = transactions
        self.prev_hash = prev_hash
        self.hash = evolving_hash(json.dumps(transactions, sort_keys=True), index, prev_hash)

class Blockchain:
    def __init__(self):
        genesis = Block(0, ['Genesis'], '0' * 64)
        self.chain = [genesis]

    def add_block(self, transactions):
        prev = self.chain[-1]
        new_block = Block(len(self.chain), transactions, prev.hash)
        self.chain.append(new_block)

    def verify_chain(self):
        for i in range(1, len(self.chain)):
            b = self.chain[i]
            recomputed = evolving_hash(json.dumps(b.transactions, sort_keys=True), b.index, b.prev_hash)
            if recomputed != b.hash:
                return False
        return True


# ── TESTS ──────────────────────────────────────────────

bc = Blockchain()
bc.add_block(["Send 100 coins"])
bc.add_block(["Send 100 coins"])
bc.add_block(["Send 50 coins"])

print("=" * 60)
print("ALL BLOCK HASHES")
print("=" * 60)
for block in bc.chain:
    print(f"Block {block.index} | Hash: {block.hash[:20]}...")

print()
print("=" * 60)
print("TEST 1: Cross-block uniqueness (same tx, different blocks)")
print("=" * 60)
h_block1 = bc.chain[1].hash
h_block2 = bc.chain[2].hash
print(f"Block 1 hash: {h_block1[:20]}...")
print(f"Block 2 hash: {h_block2[:20]}...")
print(f"Hashes are different: {h_block1 != h_block2}")

print()
print("=" * 60)
print("TEST 2: Determinism (same inputs = same hash)")
print("=" * 60)
h1 = evolving_hash("Send 100 coins", 1, bc.chain[0].hash)
h2 = evolving_hash("Send 100 coins", 1, bc.chain[0].hash)
print(f"Hash attempt 1: {h1[:20]}...")
print(f"Hash attempt 2: {h2[:20]}...")
print(f"Both hashes are equal: {h1 == h2}")

print()
print("=" * 60)
print("TEST 3: Chain verification (untampered)")
print("=" * 60)
print(f"Chain valid: {bc.verify_chain()}")

print()
print("=" * 60)
print("TEST 4: Tamper detection")
print("=" * 60)
bc.chain[1].transactions = ["Send 999 coins"]
print(f"Chain valid after tampering: {bc.verify_chain()}")

print()
print("=" * 60)
print("TEST 5: Performance Metrics")
print("=" * 60)

# Hash generation speed
start = time.time()
for i in range(1000):
    evolving_hash("Send 100 coins", i, "0" * 64)
end = time.time()
avg_ms = ((end - start) / 1000) * 1000
print(f"Hash generation (avg over 1000 runs): {avg_ms:.4f} ms per hash")

# Chain verification speed
bc2 = Blockchain()
for i in range(10):
    bc2.add_block([f"Transaction {i}"])

start = time.time()
bc2.verify_chain()
end = time.time()
verify_ms = (end - start) * 1000
print(f"Chain verification (10 blocks): {verify_ms:.4f} ms")

# Memory usage
chain_size = sum(sys.getsizeof(b.__dict__) for b in bc2.chain)
print(f"Memory usage (10 block chain): {chain_size / 1024:.2f} KB")

# Uniqueness check across 5 blocks
hashes = [evolving_hash("Send 100 coins", i, "0" * 64) for i in range(5)]
all_unique = len(hashes) == len(set(hashes))
print(f"Uniqueness across 5 blocks: {all_unique}")