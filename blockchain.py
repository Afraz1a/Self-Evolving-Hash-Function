

import hashlib
import json
import time



def evolving_hash(data: str, block_no: int, prev_hash: str) -> str:
    """
    Self-Evolving Hash Function.

    SEHF(data, n, h_prev) = SHA-256( data + str(n) + h_prev )

    Args:
        data      : Serialized transaction content (JSON string)
        block_no  : Index of the current block (n)
        prev_hash : Hash of the previous block (h_{n-1})

    Returns:
        64-character hex digest (SHA-256 output)

    Security Properties:
        1. Context Uniqueness  : Same data → different hash in each block
        2. Determinism         : Same (data, n, h_prev) → always same hash
        3. Collision Resistance: Inherited from SHA-256 (2^128 security)
    """
    combined = data + str(block_no) + prev_hash
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()

class Block:
    """
    Represents a single block in the SEHF blockchain.

    Each block's hash is produced by evolving_hash(), which means
    the same transaction data produces a DIFFERENT hash in each block.
    """

    def __init__(self, index: int, transactions: list, prev_hash: str):
        """
        Args:
            index        : Block number (0 = genesis)
            transactions : List of transaction strings
            prev_hash    : Hash of the previous block
        """
        self.index        = index
        self.timestamp    = time.time()
        self.transactions = transactions
        self.prev_hash    = prev_hash

        serialized = json.dumps(self.transactions, sort_keys=True)

        self.hash = evolving_hash(serialized, self.index, self.prev_hash)

    def to_dict(self) -> dict:
        """Return block as a dictionary (for JSON storage & Flask API)."""
        return {
            "index"        : self.index,
            "timestamp"    : self.timestamp,
            "transactions" : self.transactions,
            "prev_hash"    : self.prev_hash,
            "hash"         : self.hash,
        }

    def __repr__(self):
        return (f"Block(index={self.index}, "
                f"hash={self.hash[:12]}..., "
                f"prev={self.prev_hash[:12]}...)")



class Blockchain:
    """
    A blockchain where every block hash is context-bound using SEHF.

    Key operations:
        add_transaction()  → queue a transaction
        make_block()       → seal pending transactions into a block
        add_block()        → shortcut: make_block() directly from tx list
        verify_chain()     → integrity check for the full chain
        simulate_replay()  → test replay attack detection
    """

    GENESIS_PREV_HASH = "0" * 64   # Standard placeholder for genesis block

    def __init__(self):
        self.pending_transactions: list = []
        self.chain: list[Block] = []
        self._create_genesis_block()

    def _create_genesis_block(self):
        """Create Block 0 with a canonical prev_hash of 64 zeros."""
        genesis = Block(
            index=0,
            transactions=["Genesis Block"],
            prev_hash=self.GENESIS_PREV_HASH
        )
        self.chain.append(genesis)


    def add_transaction(self, transaction: str) -> int:
        """
        Add a transaction to the pending pool.

        Args:
            transaction: Any string representing the transaction data.

        Returns:
            Index of the block that will include this transaction.
        """
        self.pending_transactions.append(transaction)
        return len(self.chain)  # will go into this block index


    def make_block(self) -> Block:
        """
        Seal all pending transactions into a new block.

        Returns:
            The newly created Block object.

        Raises:
            ValueError: If there are no pending transactions.
        """
        if not self.pending_transactions:
            raise ValueError("No pending transactions to seal into a block.")

        prev_block = self.chain[-1]
        new_block = Block(
            index=len(self.chain),
            transactions=self.pending_transactions.copy(),
            prev_hash=prev_block.hash
        )
        self.chain.append(new_block)
        self.pending_transactions = []   # clear the pool
        return new_block

    def add_block(self, transactions: list) -> Block:
        """
        Shortcut: add transactions and immediately seal them into a block.

        Args:
            transactions: List of transaction strings.

        Returns:
            The newly created Block object.
        """
        prev_block = self.chain[-1]
        new_block = Block(
            index=len(self.chain),
            transactions=transactions,
            prev_hash=prev_block.hash
        )
        self.chain.append(new_block)
        return new_block


    def verify_chain(self) -> bool:
        """
        Recompute every block's hash and verify chain linkage.

        Returns:
            True if the chain is unmodified, False if tampered.
        """
        for i in range(1, len(self.chain)):
            block = self.chain[i]
            prev_block = self.chain[i - 1]

            # 1. Recompute hash for this block
            serialized = json.dumps(block.transactions, sort_keys=True)
            recomputed = evolving_hash(serialized, block.index, block.prev_hash)

            # 2. Check this block's stored hash
            if recomputed != block.hash:
                print(f"  [TAMPER DETECTED] Block {block.index}: hash mismatch")
                return False

            # 3. Check linkage to previous block
            if block.prev_hash != prev_block.hash:
                print(f"  [TAMPER DETECTED] Block {block.index}: broken chain link")
                return False

        return True


    def simulate_replay(self, transaction: str,
                        source_block_idx: int,
                        target_block_idx: int) -> dict:
        """
        Simulate a replay attack: take a valid tx from one block and
        try to replay it in a different block context.

        Args:
            transaction      : The transaction data being replayed
            source_block_idx : Block where the original tx lived
            target_block_idx : Block where the attacker tries to replay it

        Returns:
            dict with original_hash, replayed_hash, and attack_detected flag
        """
        if source_block_idx >= len(self.chain):
            raise IndexError(f"Source block {source_block_idx} does not exist.")
        if target_block_idx >= len(self.chain):
            raise IndexError(f"Target block {target_block_idx} does not exist.")

        source = self.chain[source_block_idx]
        target = self.chain[target_block_idx]

        serialized = json.dumps([transaction], sort_keys=True)

        original_hash = evolving_hash(serialized, source.index, source.prev_hash)
        replayed_hash = evolving_hash(serialized, target.index, target.prev_hash)

        return {
            "transaction"    : transaction,
            "source_block"   : source_block_idx,
            "target_block"   : target_block_idx,
            "original_hash"  : original_hash,
            "replayed_hash"  : replayed_hash,
            "attack_detected": original_hash != replayed_hash,
        }


    def verify_chain_detail(self) -> dict:
        """
        Like verify_chain(), but returns a structured dict instead of a bool.
        Used by the Flask dashboard's /api/verify endpoint.

        Returns:
            {
                "valid"   : bool,
                "length"  : int,
                "message" : str,          # human-readable verdict
                "errors"  : list[str],    # empty if valid
            }
        """
        errors = []

        for i in range(1, len(self.chain)):
            block      = self.chain[i]
            prev_block = self.chain[i - 1]

            # Recompute hash
            serialized = json.dumps(block.transactions, sort_keys=True)
            recomputed = evolving_hash(serialized, block.index, block.prev_hash)

            if recomputed != block.hash:
                errors.append(
                    f"Block {block.index}: stored hash does not match recomputed SEHF hash."
                )

            if block.prev_hash != prev_block.hash:
                errors.append(
                    f"Block {block.index}: prev_hash does not match Block {prev_block.index}'s hash (chain link broken)."
                )

        valid = len(errors) == 0
        return {
            "valid"  : valid,
            "length" : len(self.chain),
            "message": (
                f"All {len(self.chain)} blocks verified — chain is intact."
                if valid
                else f"{len(errors)} integrity error(s) found."
            ),
            "errors" : errors,
        }


    def print_chain(self):
        """Pretty-print all blocks."""
        print("\n" + "=" * 60)
        print("  BLOCKCHAIN — ALL BLOCKS")
        print("=" * 60)
        for block in self.chain:
            print(f"  Block {block.index:>3} | Hash: {block.hash[:20]}... | "
                  f"Txs: {len(block.transactions)}")
        print("=" * 60)

    def to_dict(self) -> list:
        """Return entire chain as a list of dicts."""
        return [b.to_dict() for b in self.chain]

    def __len__(self):
        return len(self.chain)

    def __getitem__(self, idx):
        return self.chain[idx]