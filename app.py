

from flask import Flask, jsonify, request, render_template_string
from blockchain import Blockchain

app = Flask(__name__)

# Global blockchain instance (in-memory for demo)
bc = Blockchain()

# Pre-populate with some sample blocks
bc.add_block(["Alice sends 50 coins to Bob"])
bc.add_block(["Bob sends 20 coins to Carol", "Dave sends 10 coins to Eve"])
bc.add_block(["Carol sends 5 coins to Frank"])


TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SEHF Blockchain Explorer</title>
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Syne:wght@400;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg:        #080b12;
      --surface:   #0e1320;
      --surface2:  #141926;
      --border:    #1e2740;
      --accent:    #3b82f6;
      --accent2:   #06b6d4;
      --gold:      #f59e0b;
      --green:     #10b981;
      --red:       #ef4444;
      --purple:    #a855f7;
      --text:      #e2e8f0;
      --muted:     #64748b;
      --mono:      'JetBrains Mono', monospace;
      --sans:      'Syne', sans-serif;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: var(--sans);
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
    }

    /* ── Header ── */
    header {
      background: linear-gradient(135deg, #0a0f1e 0%, #0f1a35 100%);
      border-bottom: 1px solid var(--border);
      padding: 18px 32px;
      display: flex; align-items: center; gap: 16px;
      position: relative; overflow: hidden;
    }
    header::after {
      content: '';
      position: absolute; top: 0; left: 0; right: 0; bottom: 0;
      background: repeating-linear-gradient(90deg, transparent, transparent 60px, rgba(59,130,246,0.03) 60px, rgba(59,130,246,0.03) 61px);
      pointer-events: none;
    }
    .header-logo {
      width: 44px; height: 44px; border-radius: 10px;
      background: linear-gradient(135deg, var(--accent), var(--accent2));
      display: flex; align-items: center; justify-content: center;
      font-size: 1.4rem; flex-shrink: 0;
      box-shadow: 0 0 20px rgba(59,130,246,0.4);
    }
    header h1 { font-size: 1.3rem; font-weight: 800; color: #fff; letter-spacing: -0.02em; }
    header p  { font-size: 0.78rem; color: var(--muted); margin-top: 2px; font-family: var(--mono); }
    .header-badge {
      margin-left: auto; background: rgba(59,130,246,0.12); border: 1px solid rgba(59,130,246,0.3);
      color: var(--accent); padding: 4px 12px; border-radius: 20px;
      font-size: 0.72rem; font-family: var(--mono); font-weight: 600;
    }

    /* ── Layout ── */
    .container { max-width: 1180px; margin: 0 auto; padding: 28px 20px; }
    .grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; margin-bottom: 18px; }
    .full { grid-column: 1 / -1; }

    /* ── Cards ── */
    .card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 22px;
      position: relative; overflow: hidden;
    }
    .card-title {
      font-size: 0.78rem; font-weight: 700; letter-spacing: 0.08em;
      text-transform: uppercase; color: var(--muted);
      margin-bottom: 16px; display: flex; align-items: center; gap: 8px;
    }
    .card-title .icon { font-size: 1rem; }

    /* ── Formula Banner ── */
    .formula-banner {
      background: linear-gradient(135deg, #0a1628, #0f1f3d);
      border: 1px solid rgba(59,130,246,0.25);
      border-radius: 14px; padding: 22px 28px;
      margin-bottom: 18px; position: relative; overflow: hidden;
    }
    .formula-banner::before {
      content: 'SEHF';
      position: absolute; right: 20px; top: 50%; transform: translateY(-50%);
      font-size: 5rem; font-weight: 800; color: rgba(59,130,246,0.06);
      font-family: var(--mono); pointer-events: none;
    }
    .formula-label { font-size: 0.72rem; color: var(--accent2); font-family: var(--mono); font-weight: 600; letter-spacing: 0.1em; margin-bottom: 10px; }
    .formula-eq {
      display: flex; align-items: center; flex-wrap: wrap; gap: 6px;
      font-family: var(--mono); font-size: 0.95rem;
    }
    .f-fn   { color: var(--accent); font-weight: 700; }
    .f-op   { color: var(--muted); }
    .f-data { color: var(--green); font-weight: 600; }
    .f-n    { color: var(--gold); font-weight: 600; }
    .f-prev { color: var(--purple); font-weight: 600; }
    .f-eq   { color: var(--muted); }
    .f-out  { color: #fff; font-weight: 600; }
    .formula-legend {
      display: flex; flex-wrap: wrap; gap: 14px; margin-top: 14px;
    }
    .legend-item { display: flex; align-items: center; gap: 6px; font-size: 0.75rem; }
    .legend-dot  { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }

    /* ── Stats row ── */
    .stat-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
    .stat-box {
      background: var(--surface2); border: 1px solid var(--border);
      border-radius: 10px; padding: 14px 16px;
    }
    .stat-num  { font-size: 1.8rem; font-weight: 800; color: var(--accent); font-family: var(--mono); line-height: 1; }
    .stat-lbl  { font-size: 0.72rem; color: var(--muted); margin-top: 4px; }
    .badge-ok  { display: inline-block; background: rgba(16,185,129,0.15); color: var(--green); border: 1px solid rgba(16,185,129,0.3); padding: 3px 10px; border-radius: 20px; font-size: 0.75rem; font-family: var(--mono); font-weight: 600; }
    .badge-err { display: inline-block; background: rgba(239,68,68,0.15); color: var(--red); border: 1px solid rgba(239,68,68,0.3); padding: 3px 10px; border-radius: 20px; font-size: 0.75rem; font-family: var(--mono); font-weight: 600; }

    /* ── Inputs ── */
    input[type=text] {
      width: 100%; background: var(--surface2); border: 1px solid var(--border);
      color: var(--text); padding: 10px 14px; border-radius: 8px;
      font-size: 0.88rem; margin-bottom: 10px; font-family: var(--sans);
      transition: border-color 0.2s;
    }
    input[type=text]:focus { outline: none; border-color: var(--accent); }
    input[type=number] {
      width: 76px; background: var(--surface2); border: 1px solid var(--border);
      color: var(--text); padding: 10px 12px; border-radius: 8px;
      font-size: 0.88rem; margin-right: 8px; font-family: var(--mono);
    }
    label { font-size: 0.75rem; color: var(--muted); display: block; margin-bottom: 5px; font-weight: 600; letter-spacing: 0.04em; }

    /* ── Buttons ── */
    .btn {
      background: var(--accent); color: #fff; border: none;
      padding: 10px 20px; border-radius: 8px; cursor: pointer;
      font-size: 0.85rem; font-weight: 700; font-family: var(--sans);
      transition: all 0.2s; letter-spacing: 0.02em;
    }
    .btn:hover { background: #2563eb; transform: translateY(-1px); box-shadow: 0 4px 12px rgba(59,130,246,0.4); }
    .btn-danger { background: var(--red); }
    .btn-danger:hover { background: #dc2626; box-shadow: 0 4px 12px rgba(239,68,68,0.4); }
    .btn-ghost {
      background: transparent; border: 1px solid var(--border); color: var(--muted);
    }
    .btn-ghost:hover { border-color: var(--accent); color: var(--accent); box-shadow: none; }

    /* ── Output console ── */
    .console {
      background: #050810; border: 1px solid var(--border);
      border-radius: 8px; padding: 14px; margin-top: 12px;
      font-size: 0.78rem; font-family: var(--mono);
      min-height: 48px; white-space: pre-wrap; color: var(--green);
      line-height: 1.6;
    }
    .console.error { color: var(--red); }

    /* ── Add tx visual flow ── */
    .tx-flow {
      display: flex; align-items: center; gap: 0; margin: 14px 0; overflow-x: auto;
    }
    .flow-step {
      background: var(--surface2); border: 1px solid var(--border);
      border-radius: 8px; padding: 10px 14px; text-align: center;
      flex-shrink: 0; min-width: 110px;
    }
    .flow-step .fs-icon { font-size: 1.3rem; }
    .flow-step .fs-label { font-size: 0.68rem; color: var(--muted); margin-top: 4px; }
    .flow-step .fs-val { font-size: 0.7rem; font-family: var(--mono); color: var(--accent); margin-top: 2px; word-break: break-all; max-width: 120px; }
    .flow-arrow { color: var(--border); font-size: 1.2rem; padding: 0 6px; flex-shrink: 0; }
    .flow-step.active { border-color: var(--accent); background: rgba(59,130,246,0.08); }
    .flow-step.active .fs-icon { animation: pulse 1s ease-in-out infinite; }
    @keyframes pulse { 0%,100% { transform: scale(1); } 50% { transform: scale(1.2); } }

    /* ── Replay visual ── */
    .replay-visual { margin-top: 16px; }
    .rv-row {
      display: flex; align-items: stretch; gap: 12px; margin-bottom: 10px;
    }
    .rv-block {
      flex: 1; background: var(--surface2); border: 1px solid var(--border);
      border-radius: 10px; padding: 12px 14px;
    }
    .rv-block.src { border-color: rgba(59,130,246,0.4); }
    .rv-block.tgt { border-color: rgba(239,68,68,0.4); }
    .rv-block-title { font-size: 0.7rem; font-weight: 700; letter-spacing: 0.06em; margin-bottom: 8px; }
    .rv-block.src .rv-block-title { color: var(--accent); }
    .rv-block.tgt .rv-block-title { color: var(--red); }
    .rv-context-row { display: flex; align-items: baseline; gap: 6px; margin-bottom: 4px; }
    .rv-ctx-label { font-size: 0.66rem; color: var(--muted); font-family: var(--mono); width: 60px; flex-shrink: 0; }
    .rv-ctx-val { font-size: 0.68rem; font-family: var(--mono); }
    .rv-ctx-val.n    { color: var(--gold); }
    .rv-ctx-val.prev { color: var(--purple); }
    .rv-ctx-val.hash { color: var(--green); word-break: break-all; }
    .rv-ctx-val.hash.replayed { color: var(--red); }
    .rv-arrow-col {
      display: flex; align-items: center; justify-content: center;
      flex-direction: column; gap: 4px; padding: 0 4px;
    }
    .rv-arrow-col .tx-label { font-size: 0.68rem; color: var(--muted); font-family: var(--mono); text-align: center; max-width: 80px; word-break: break-all; }
    .rv-arrow-col .arrow { color: var(--red); font-size: 1.6rem; }
    .rv-verdict {
      border-radius: 8px; padding: 10px 14px; margin-top: 10px;
      font-size: 0.82rem; font-family: var(--mono); font-weight: 600;
      display: flex; align-items: center; gap: 10px;
    }
    .rv-verdict.detected { background: rgba(16,185,129,0.1); border: 1px solid rgba(16,185,129,0.3); color: var(--green); }
    .rv-verdict.missed   { background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.3); color: var(--red); }
    .rv-verdict-icon { font-size: 1.3rem; }

    /* ── Block Explorer ── */
    .chain-scroll { overflow-x: auto; padding-bottom: 8px; }
    .chain-horizontal { display: flex; gap: 0; align-items: flex-start; min-width: max-content; padding: 8px 4px; }
    .block-node {
      background: var(--surface2); border: 1px solid var(--border);
      border-radius: 12px; padding: 16px; width: 240px; flex-shrink: 0;
      position: relative; transition: border-color 0.2s;
      animation: fadeIn 0.4s ease forwards;
    }
    .block-node:hover { border-color: var(--accent); }
    @keyframes fadeIn { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:translateY(0); } }
    .block-node.genesis { border-color: rgba(168,85,247,0.4); }
    .block-connector {
      display: flex; align-items: center; padding: 0 2px;
      flex-shrink: 0;
    }
    .bc-line { width: 24px; height: 2px; background: linear-gradient(90deg, var(--accent), var(--accent2)); }
    .bc-arrow { color: var(--accent2); font-size: 1rem; margin-left: -4px; }
    .bc-label {
      writing-mode: vertical-rl; font-size: 0.58rem; color: var(--muted);
      font-family: var(--mono); margin: 0 2px; letter-spacing: 0.05em;
    }

    .bn-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
    .bn-index { font-size: 0.78rem; font-weight: 700; font-family: var(--mono); }
    .bn-index.gen { color: var(--purple); }
    .bn-index.reg { color: var(--accent); }
    .bn-time  { font-size: 0.65rem; color: var(--muted); font-family: var(--mono); }

    .bn-hash-section { margin-bottom: 8px; }
    .bn-hash-label { font-size: 0.62rem; color: var(--muted); font-family: var(--mono); margin-bottom: 2px; letter-spacing: 0.06em; }
    .bn-hash-val {
      font-size: 0.65rem; font-family: var(--mono); color: var(--gold);
      word-break: break-all; line-height: 1.4;
      background: rgba(245,158,11,0.06); border-radius: 4px; padding: 4px 6px;
    }
    .bn-prev-val {
      font-size: 0.65rem; font-family: var(--mono); color: var(--purple);
      word-break: break-all; line-height: 1.4;
      background: rgba(168,85,247,0.06); border-radius: 4px; padding: 4px 6px;
    }

    .bn-tx { margin-top: 8px; }
    .bn-tx-item {
      background: rgba(59,130,246,0.08); border: 1px solid rgba(59,130,246,0.15);
      border-radius: 5px; padding: 4px 8px; font-size: 0.68rem;
      color: #93c5fd; margin-bottom: 3px; line-height: 1.3;
    }
    .bn-sehf-pill {
      margin-top: 10px; padding: 4px 8px; border-radius: 4px;
      font-size: 0.62rem; font-family: var(--mono); font-weight: 600; letter-spacing: 0.05em;
      background: rgba(6,182,212,0.08); color: var(--accent2); border: 1px solid rgba(6,182,212,0.2);
      display: flex; align-items: center; gap: 5px;
    }

    /* ── Verify card ── */
    .verify-steps { margin-top: 10px; }
    .vstep {
      display: flex; align-items: flex-start; gap: 10px; margin-bottom: 8px;
      padding: 8px 10px; border-radius: 7px; border: 1px solid var(--border);
      background: var(--surface2);
    }
    .vstep-num {
      width: 20px; height: 20px; border-radius: 50%; background: var(--border);
      color: var(--muted); font-size: 0.65rem; font-weight: 700;
      display: flex; align-items: center; justify-content: center; flex-shrink: 0;
    }
    .vstep.ok .vstep-num  { background: rgba(16,185,129,0.2); color: var(--green); }
    .vstep.err .vstep-num { background: rgba(239,68,68,0.2);  color: var(--red); }
    .vstep-text { font-size: 0.75rem; color: var(--muted); }
    .vstep.ok .vstep-text  { color: var(--text); }
    .vstep.err .vstep-text { color: var(--red); }

    /* ── Row util ── */
    .row { display: flex; gap: 10px; align-items: flex-end; flex-wrap: wrap; }
    .section-hint { font-size: 0.74rem; color: var(--muted); margin-bottom: 14px; line-height: 1.5; }
  </style>
</head>
<body>

<header>
  <div class="header-logo">⛓</div>
  <div>
    <h1>SEHF Blockchain Explorer</h1>
    <p>Self-Evolving Hash Function &nbsp;·&nbsp; Phase 3 &nbsp;·&nbsp; ITU — Afrazia, Ashna, Khadija</p>
  </div>
  <div class="header-badge">LIVE DEMO</div>
</header>

<div class="container">

  <!-- ═══ FORMULA EXPLAINER ═══ -->
  <div class="formula-banner">
    <div class="formula-label">▸ CORE FORMULA — HOW EVERY HASH IS COMPUTED</div>
    <div class="formula-eq">
      <span class="f-fn">SEHF</span><span class="f-op">(</span>
      <span class="f-data">data</span><span class="f-op">,</span>
      <span class="f-n">n</span><span class="f-op">,</span>
      <span class="f-prev">h_prev</span>
      <span class="f-op">)</span>
      <span class="f-eq">=</span>
      <span class="f-fn">SHA-256</span><span class="f-op">(</span>
      <span class="f-data">data</span>
      <span class="f-op"> ‖ </span>
      <span class="f-n">str(n)</span>
      <span class="f-op"> ‖ </span>
      <span class="f-prev">h_prev</span>
      <span class="f-op">)</span>
      <span class="f-eq">→</span>
      <span class="f-out">64-char hex</span>
    </div>
    <div class="formula-legend">
      <div class="legend-item"><div class="legend-dot" style="background:#10b981"></div><span style="color:#10b981">data</span> — transaction content</div>
      <div class="legend-item"><div class="legend-dot" style="background:#f59e0b"></div><span style="color:#f59e0b">n</span> — block index (unique per block)</div>
      <div class="legend-item"><div class="legend-dot" style="background:#a855f7"></div><span style="color:#a855f7">h_prev</span> — previous block's hash (unique per block)</div>
      <div class="legend-item" style="margin-left:auto"><span style="color:#64748b;font-size:0.72rem">⚡ Because n and h_prev differ for every block, the same transaction always produces a DIFFERENT hash — making replay attacks impossible.</span></div>
    </div>
  </div>

  <!-- ═══ STATS + ADD TX ═══ -->
  <div class="grid2">
    <div class="card">
      <div class="card-title"><span class="icon">📊</span> Chain Status</div>
      <div id="stat-grid" class="stat-grid">
        <div class="stat-box"><div class="stat-num" id="s-blocks">–</div><div class="stat-lbl">Total Blocks</div></div>
        <div class="stat-box"><div id="s-valid" style="font-size:0.95rem;font-weight:700;padding-top:4px">–</div><div class="stat-lbl">Integrity</div></div>
        <div class="stat-box"><div class="stat-num" id="s-txs" style="font-size:1.2rem">–</div><div class="stat-lbl">Latest Hash</div></div>
      </div>
    </div>

    <div class="card">
      <div class="card-title"><span class="icon">✏️</span> Add Transaction</div>
      <div class="section-hint">Type a transaction → it gets sealed into a new block with a unique SEHF hash.</div>
      <label>Transaction data</label>
      <input type="text" id="tx-input" placeholder="e.g. Alice sends 50 coins to Bob">

      <!-- Visual flow diagram -->
      <div class="tx-flow" id="tx-flow">
        <div class="flow-step" id="fs-data">
          <div class="fs-icon">📄</div>
          <div class="fs-label">Your Data</div>
          <div class="fs-val" id="fv-data">—</div>
        </div>
        <div class="flow-arrow">+</div>
        <div class="flow-step" id="fs-n">
          <div class="fs-icon">🔢</div>
          <div class="fs-label">Block Index (n)</div>
          <div class="fs-val" id="fv-n">—</div>
        </div>
        <div class="flow-arrow">+</div>
        <div class="flow-step" id="fs-prev">
          <div class="fs-icon">🔗</div>
          <div class="fs-label">Prev Hash</div>
          <div class="fs-val" id="fv-prev">—</div>
        </div>
        <div class="flow-arrow">→</div>
        <div class="flow-step" id="fs-hash">
          <div class="fs-icon">🔐</div>
          <div class="fs-label">SEHF Output</div>
          <div class="fs-val" id="fv-hash">—</div>
        </div>
      </div>

      <button class="btn" onclick="addTx()">Add &amp; Seal Block</button>
      <div class="console" id="result-box"></div>
    </div>
  </div>

  <!-- ═══ REPLAY ATTACK + VERIFY ═══ -->
  <div class="grid2">
    <div class="card">
      <div class="card-title"><span class="icon">🔁</span> Replay Attack Simulator</div>
      <div class="section-hint">
        An attacker takes a valid transaction from one block and tries to submit it again in a different block.
        SEHF detects this because the block context (n + h_prev) is different → the hash never matches.
      </div>
      <label>Transaction to replay</label>
      <input type="text" id="replay-tx" placeholder="e.g. Send 100 coins">
      <div class="row">
        <div><label>Source block</label><input type="number" id="replay-src" value="1" min="0"></div>
        <div><label>Target block</label><input type="number" id="replay-tgt" value="2" min="0"></div>
        <button class="btn btn-danger" onclick="simulateReplay()" style="margin-bottom:0">Simulate Attack</button>
      </div>
      <div class="replay-visual" id="replay-visual"></div>
    </div>

    <div class="card">
      <div class="card-title"><span class="icon">✅</span> Chain Integrity Check</div>
      <div class="section-hint">
        Recomputes the SEHF hash for every block and checks that each block's prev_hash matches the previous block's hash.
        If anything was tampered, the recomputed hash won't match the stored hash.
      </div>
      <button class="btn" onclick="verifyChain()">Run verify_chain()</button>
      <div class="verify-steps" id="verify-steps"></div>
    </div>
  </div>

  <!-- ═══ BLOCK EXPLORER ═══ -->
  <div class="card full">
    <div class="card-title"><span class="icon">⛓</span> Block Explorer — Live Chain</div>
    <div class="section-hint">
      Each block contains: its transactions, the SEHF hash of those transactions in context, and a pointer (prev_hash) to the previous block.
      The <span style="color:var(--purple)">purple</span> prev_hash in each block must exactly match the <span style="color:var(--gold)">gold</span> hash of the block before it — that's the chain.
    </div>
    <div class="chain-scroll">
      <div class="chain-horizontal" id="chain-list">Loading...</div>
    </div>
  </div>

</div>

<script>
  // ── update flow diagram inputs ──
  document.getElementById('tx-input').addEventListener('input', function() {
    const v = this.value || '—';
    document.getElementById('fv-data').textContent = v.length > 14 ? v.slice(0,12)+'…' : v;
  });

  let chainData = [];

  async function loadChain() {
    const res = await fetch('/api/chain');
    const data = await res.json();
    chainData = data.chain;
    renderStats(data);
    renderChain(data.chain);
    updateFlowN(data.length);
  }

  function updateFlowN(n) {
    document.getElementById('fv-n').textContent = n;
    if (chainData.length > 0) {
      const last = chainData[chainData.length - 1];
      document.getElementById('fv-prev').textContent = last.hash.slice(0, 8) + '…';
    }
  }

  // Allow pressing Enter in the tx input to submit
  document.getElementById('tx-input').addEventListener('keydown', function(e) {
    if (e.key === 'Enter') addTx();
  });

  // Allow pressing Enter in replay inputs to trigger simulation
  ['replay-tx', 'replay-src', 'replay-tgt'].forEach(id => {
    document.getElementById(id).addEventListener('keydown', function(e) {
      if (e.key === 'Enter') simulateReplay();
    });
  });

  function renderStats(data) {
    document.getElementById('s-blocks').textContent = data.length;
    const vEl = document.getElementById('s-valid');
    if (data.valid) {
      vEl.innerHTML = '<span class="badge-ok">Valid ✓</span>';
    } else {
      vEl.innerHTML = '<span class="badge-err">TAMPERED ✗</span>';
    }
    const last = data.chain[data.chain.length - 1];
    document.getElementById('s-txs').textContent = last.hash.slice(0, 10) + '…';
    document.getElementById('s-txs').title = last.hash;
  }

  function renderChain(chain) {
    const container = document.getElementById('chain-list');
    let html = '';
    chain.forEach((b, i) => {
      const isGenesis = b.index === 0;
      html += `
        <div class="block-node ${isGenesis ? 'genesis' : ''}" style="animation-delay:${i*0.06}s">
          <div class="bn-top">
            <span class="bn-index ${isGenesis ? 'gen' : 'reg'}">
              ${isGenesis ? '🌱 GENESIS' : '# ' + b.index}
            </span>
            <span class="bn-time">${new Date(b.timestamp * 1000).toLocaleTimeString()}</span>
          </div>

          <div class="bn-hash-section">
            <div class="bn-hash-label">HASH (this block's output)</div>
            <div class="bn-hash-val" title="${b.hash}">${b.hash}</div>
          </div>

          <div class="bn-hash-section">
            <div class="bn-hash-label">PREV_HASH (points to block ${b.index - 1 >= 0 ? b.index - 1 : '—'})</div>
            <div class="bn-prev-val" title="${b.prev_hash}">${b.prev_hash}</div>
          </div>

          <div class="bn-tx">
            ${b.transactions.map(tx => `<div class="bn-tx-item">📄 ${tx}</div>`).join('')}
          </div>

          <div class="bn-sehf-pill">
            ⚡ SEHF(data ‖ ${b.index} ‖ prev_hash)
          </div>
        </div>
      `;
      if (i < chain.length - 1) {
        html += `
          <div class="block-connector">
            <div class="bc-line"></div>
            <div class="bc-arrow">▶</div>
          </div>
        `;
      }
    });
    container.innerHTML = html;
  }

  async function addTx() {
    const tx = document.getElementById('tx-input').value.trim();
    if (!tx) return;

    // animate flow
    ['fs-data','fs-n','fs-prev','fs-hash'].forEach(id => {
      document.getElementById(id).classList.add('active');
    });

    const res = await fetch('/api/add_block', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({transactions: [tx]})
    });
    const data = await res.json();

    ['fs-data','fs-n','fs-prev','fs-hash'].forEach(id => {
      document.getElementById(id).classList.remove('active');
    });

    document.getElementById('fv-hash').textContent = data.block.hash.slice(0, 10) + '…';

    const box = document.getElementById('result-box');
    box.className = 'console';
    box.textContent =
      'Block ' + data.block.index + ' created!\\n' +
      'Hash: ' + data.block.hash + '\\n' +
      'Transactions: ' + data.block.transactions.join(', ');

    document.getElementById('tx-input').value = '';
    loadChain();
  }

  async function simulateReplay() {
    const tx  = document.getElementById('replay-tx').value.trim() || 'Send 100 coins';
    const src = parseInt(document.getElementById('replay-src').value);
    const tgt = parseInt(document.getElementById('replay-tgt').value);
    const res = await fetch('/api/simulate_replay', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({transaction: tx, source: src, target: tgt})
    });
    const data = await res.json();
    const el = document.getElementById('replay-visual');

    if (data.error) {
      el.innerHTML = '<div class="console error">' + data.error + '</div>';
      return;
    }

    const srcBlock = chainData[data.source_block] || {};
    const tgtBlock = chainData[data.target_block] || {};
    const detected = data.attack_detected;

    el.innerHTML = `
      <div style="font-size:0.7rem;color:var(--muted);font-family:var(--mono);margin-bottom:8px;">
        SAME TRANSACTION → DIFFERENT CONTEXT → DIFFERENT HASH
      </div>
      <div class="rv-row">
        <div class="rv-block src">
          <div class="rv-block-title">ORIGINAL — Block ${data.source_block}</div>
          <div class="rv-context-row"><span class="rv-ctx-label">n =</span><span class="rv-ctx-val n">${data.source_block}</span></div>
          <div class="rv-context-row"><span class="rv-ctx-label">h_prev =</span><span class="rv-ctx-val prev">${(srcBlock.prev_hash||'').slice(0,14)}…</span></div>
          <div class="rv-context-row"><span class="rv-ctx-label">hash =</span><span class="rv-ctx-val hash">${data.original_hash.slice(0,18)}…</span></div>
        </div>
        <div class="rv-arrow-col">
          <div class="tx-label">"${tx.length > 12 ? tx.slice(0,10)+'…' : tx}"</div>
          <div class="arrow">→</div>
          <div class="tx-label" style="color:var(--red);font-size:0.6rem">REPLAYED</div>
        </div>
        <div class="rv-block tgt">
          <div class="rv-block-title">REPLAYED — Block ${data.target_block}</div>
          <div class="rv-context-row"><span class="rv-ctx-label">n =</span><span class="rv-ctx-val n">${data.target_block} ← <span style="color:var(--red)">different!</span></span></div>
          <div class="rv-context-row"><span class="rv-ctx-label">h_prev =</span><span class="rv-ctx-val prev">${(tgtBlock.prev_hash||'').slice(0,14)}… <span style="color:var(--red)">← diff!</span></span></div>
          <div class="rv-context-row"><span class="rv-ctx-label">hash =</span><span class="rv-ctx-val hash replayed">${data.replayed_hash.slice(0,18)}…</span></div>
        </div>
      </div>
      <div class="rv-verdict ${detected ? 'detected' : 'missed'}">
        <span class="rv-verdict-icon">${detected ? '🛡️' : '⚠️'}</span>
        <span>${detected
          ? 'ATTACK DETECTED — Hashes differ because block context changed. Replay rejected.'
          : 'NOT DETECTED — Hashes match (same block context). This should not happen with SEHF.'
        }</span>
      </div>
    `;
  }

  async function verifyChain() {
    const el = document.getElementById('verify-steps');
    el.innerHTML = '<div style="color:var(--muted);font-size:0.78rem;padding:8px;">Verifying all blocks…</div>';
    const res = await fetch('/api/verify');
    const data = await res.json();
    const n = data.length;

    let html = '';
    const steps = [
      { text: `Recompute SEHF hash for all ${n} blocks using stored transactions, index, and prev_hash` },
      { text: `Compare recomputed hash against stored hash for each block` },
      { text: `Verify each block's prev_hash matches the preceding block's hash (chain linkage)` },
    ];
    steps.forEach((s, i) => {
      const cls = data.valid ? 'ok' : (i === 2 ? 'err' : 'ok');
      html += `<div class="vstep ${cls}">
        <div class="vstep-num">${data.valid ? '✓' : (i===2?'✗':i+1)}</div>
        <div class="vstep-text">${s.text}</div>
      </div>`;
    });

    html += `<div class="rv-verdict ${data.valid ? 'detected' : 'missed'}" style="margin-top:8px">
      <span class="rv-verdict-icon">${data.valid ? '✅' : '⛔'}</span>
      <span style="font-family:var(--mono)">${data.valid
        ? 'All ' + n + ' blocks verified — chain is intact.'
        : data.message
      }</span>
    </div>`;

    el.innerHTML = html;
  }

  loadChain();
  setInterval(loadChain, 5000);
</script>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(TEMPLATE)


@app.route('/api/chain')
def get_chain():
    return jsonify({
        "length" : len(bc),
        "valid"  : bc.verify_chain(),
        "chain"  : bc.to_dict(),
    })


@app.route('/api/add_block', methods=['POST'])
def add_block():
    data = request.get_json()
    transactions = data.get('transactions', [])
    if not transactions:
        return jsonify({"error": "No transactions provided"}), 400

    block = bc.add_block(transactions)
    return jsonify({"success": True, "block": block.to_dict()})


@app.route('/api/verify')
def verify():
    return jsonify(bc.verify_chain_detail())


@app.route('/api/simulate_replay', methods=['POST'])
def simulate_replay():
    data = request.get_json()
    tx  = data.get('transaction', 'Send 100 coins')
    src = data.get('source', 1)
    tgt = data.get('target', 2)

    try:
        result = bc.simulate_replay(tx, src, tgt)
        return jsonify(result)
    except IndexError as e:
        return jsonify({"error": str(e)}), 400


if __name__ == '__main__':
    print("\n  SEHF Blockchain Dashboard")
    print("  Open your browser at: http://127.0.0.1:5000\n")
    app.run(debug=True, port=5000)