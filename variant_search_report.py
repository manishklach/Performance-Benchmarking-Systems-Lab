from __future__ import annotations

import json
from pathlib import Path

from triton_adapter import default_matmul_variant_specs


BASE_DIR = Path(__file__).resolve().parent
DOCS_DIR = BASE_DIR / "docs"
RUNS_DIR = BASE_DIR / "runs"
DEFAULT_BATCH_DIR = RUNS_DIR / "batch_outputs" / "triton_matmul_generated"
DEFAULT_OUTPUT = DOCS_DIR / "variant_search_report.html"


def load_batch_summary(batch_dir: Path) -> dict[str, object] | None:
    summary_path = batch_dir / "triton_batch_summary.json"
    if not summary_path.exists():
        return None
    return json.loads(summary_path.read_text(encoding="utf-8"))


def render_html(batch_dir: Path, payload: dict[str, object] | None) -> str:
    variants = default_matmul_variant_specs()

    summary_table = "<p>No Triton batch results found yet. Run <code>python triton_batch_runner.py --runs 12 --workload matmul --candidate-mode generated</code> on a GPU machine to populate this section.</p>"
    decision_table = ""
    artifact_links = "<li>No GPU batch bundle present yet.</li>"

    if payload is not None:
        summary = payload["summary"]
        summary_rows = []
        for key, value in summary.items():
            summary_rows.append(f"<tr><th>{key}</th><td>{value}</td></tr>")
        summary_table = f"""
        <table>
          <tbody>
            {''.join(summary_rows)}
          </tbody>
        </table>
        """

        decision_rows = []
        for record in payload["records"][:12]:
            decision_rows.append(
                "<tr>"
                f"<td>{record['seed']}</td>"
                f"<td>{record['naive_winner']}</td>"
                f"<td>{record['decision']}</td>"
                f"<td>{record['final_finalist_analysis']['winner_name']}</td>"
                f"<td>{record['final_finalist_analysis']['rel_gain_pct']:.3f}</td>"
                f"<td>{record['final_finalist_analysis']['lower_confidence_bound_pct']:.3f}</td>"
                "</tr>"
            )
        decision_table = f"""
        <h2>Sample GPU Batch Decisions</h2>
        <table>
          <thead>
            <tr>
              <th>Seed</th>
              <th>Naive Winner</th>
              <th>Decision</th>
              <th>Final Winner</th>
              <th>Gain %</th>
              <th>LCB %</th>
            </tr>
          </thead>
          <tbody>
            {''.join(decision_rows)}
          </tbody>
        </table>
        """

        artifact_links = """
        <li><a href="../runs/batch_outputs/triton_matmul_generated/triton_batch_summary.html">runs/batch_outputs/triton_matmul_generated/triton_batch_summary.html</a></li>
        <li><a href="../runs/batch_outputs/triton_matmul_generated/triton_batch_summary.json">runs/batch_outputs/triton_matmul_generated/triton_batch_summary.json</a></li>
        <li><a href="../runs/batch_outputs/triton_matmul_generated/triton_batch_results.csv">runs/batch_outputs/triton_matmul_generated/triton_batch_results.csv</a></li>
        <li><a href="../runs/batch_outputs/triton_matmul_generated/plots/selection_outcomes.png">runs/batch_outputs/triton_matmul_generated/plots/selection_outcomes.png</a></li>
        <li><a href="../runs/batch_outputs/triton_matmul_generated/plots/final_gain_vs_lcb.png">runs/batch_outputs/triton_matmul_generated/plots/final_gain_vs_lcb.png</a></li>
        <li><a href="../runs/batch_outputs/triton_matmul_generated/plots/decision_timeline.png">runs/batch_outputs/triton_matmul_generated/plots/decision_timeline.png</a></li>
        """

    variant_rows = []
    for variant in variants:
        variant_rows.append(
            "<tr>"
            f"<td><code>{variant.name}</code></td>"
            f"<td>{variant.block_size_m}</td>"
            f"<td>{variant.block_size_n}</td>"
            f"<td>{variant.block_size_k}</td>"
            f"<td>{variant.group_size_m}</td>"
            f"<td>{variant.num_warps}</td>"
            f"<td>{variant.num_stages}</td>"
            f"<td><code>{variant.activation or 'none'}</code></td>"
            "</tr>"
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Variant Search Report</title>
  <style>
    :root {{
      --bg: #f3eee6;
      --paper: #fffdf8;
      --ink: #211d1a;
      --muted: #6c6258;
      --line: #d8cfc4;
      --accent: #2a6f97;
    }}
    body {{ margin: 0; background: var(--bg); color: var(--ink); font-family: Georgia, "Times New Roman", serif; }}
    main {{ max-width: 1120px; margin: 24px auto; padding: 30px 36px 44px; background: var(--paper); border: 1px solid var(--line); box-shadow: 0 16px 40px rgba(0,0,0,.08); }}
    h1, h2, h3 {{ margin-top: 0; }}
    h2 {{ margin-top: 28px; padding-top: 10px; border-top: 1px solid var(--line); }}
    p, li {{ line-height: 1.45; }}
    .hero {{ border-left: 4px solid #8c2f39; background: #f8f1ea; padding: 14px 16px; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }}
    .card {{ border: 1px solid var(--line); background: #fffaf2; padding: 16px 18px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 14px; }}
    th, td {{ border: 1px solid var(--line); padding: 8px 10px; text-align: left; vertical-align: top; }}
    th {{ background: #f4ede3; }}
    img {{ max-width: 100%; border: 1px solid var(--line); background: white; }}
    code {{ font-family: "Courier New", monospace; }}
    a {{ color: var(--accent); }}
  </style>
</head>
<body>
  <main>
    <h1>Variant Search Report</h1>
    <p class="hero"><strong>Purpose.</strong> This report enumerates the fixed generated Triton matmul candidate set and, when available, summarizes repeated GPU batch results for those variants.</p>

    <div class="grid">
      <div class="card">
        <h3>Generated candidate source</h3>
        <p>The current generated variants are defined in <code>triton_adapter.py</code> as a small, explicit subset of the official Triton matmul search space.</p>
      </div>
      <div class="card">
        <h3>Batch result source</h3>
        <p>Expected GPU output directory:</p>
        <p><code>{batch_dir}</code></p>
      </div>
    </div>

    <h2>Generated Candidate Set</h2>
    <table>
      <thead>
        <tr>
          <th>Variant</th>
          <th>BLOCK_SIZE_M</th>
          <th>BLOCK_SIZE_N</th>
          <th>BLOCK_SIZE_K</th>
          <th>GROUP_SIZE_M</th>
          <th>num_warps</th>
          <th>num_stages</th>
          <th>activation</th>
        </tr>
      </thead>
      <tbody>
        {''.join(variant_rows)}
      </tbody>
    </table>

    <h2>Why These Variants</h2>
    <ul>
      <li><code>balanced</code> is a middle-of-the-range square tiling choice.</li>
      <li><code>wide_n</code> favors larger output-N tiles.</li>
      <li><code>aggressive</code> uses larger tiles and more warps to probe higher-throughput regimes.</li>
      <li><code>compact</code> uses smaller tiles and fewer warps to probe lighter-weight execution regimes.</li>
    </ul>

    <h2>GPU Batch Summary</h2>
    {summary_table}

    {decision_table}

    <h2>Artifacts</h2>
    <ul>
      {artifact_links}
    </ul>
  </main>
</body>
</html>
"""


def main() -> None:
    payload = load_batch_summary(DEFAULT_BATCH_DIR)
    html = render_html(DEFAULT_BATCH_DIR, payload)
    DEFAULT_OUTPUT.write_text(html, encoding="utf-8")
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Saved variant search report to {DEFAULT_OUTPUT}")


if __name__ == "__main__":
    main()
