"""
HTML Report Generator
Styled after github.com/ThariqS/html-effectiveness design system
"""
from pathlib import Path
from typing import Dict, List
import pandas as pd
from datetime import date


def _cer_color(cer: float) -> str:
    if cer <= 0.05:  return "var(--olive)"
    if cer <= 0.10:  return "var(--clay)"
    return "var(--rust)"

def _wer_color(wer: float) -> str:
    if wer <= 0.10:  return "var(--olive)"
    if wer <= 0.20:  return "var(--clay)"
    return "var(--rust)"

def _delta_color(delta: float) -> str:
    if delta <= 0.01:  return "var(--olive)"
    if delta <= 0.03:  return "var(--clay)"
    return "var(--rust)"

MODEL_ACCENTS = ["var(--clay)", "var(--olive)", "var(--slate)"]


def generate_html_report(
    ranked_df: pd.DataFrame,
    top_models: List[str],
    per_model_samples: Dict[str, List[dict]] = None,
    cost_data: Dict[str, dict] = None,
    metadata: Dict = None,
) -> str:

    per_model_samples = per_model_samples or {}
    cost_data = cost_data or {}
    num_samples = metadata.get("num_samples", "—") if metadata else "—"
    today = date.today().strftime("%B %d, %Y")

    # ── Stat cards ─────────────────────────────────────────────────────────────
    stat_cards_html = ""
    for i, model_name in enumerate(top_models):
        if model_name not in ranked_df['model'].values:
            continue
        row = ranked_df[ranked_df['model'] == model_name].iloc[0]
        cost = cost_data.get(model_name, {})
        accent = MODEL_ACCENTS[i % len(MODEL_ACCENTS)]
        rank_label = f"#{int(row['rank'])}"

        stat_cards_html += f"""
        <div class="model-card">
          <div class="model-rank" style="color:{accent}">{rank_label}</div>
          <div class="model-name">{model_name}</div>
          <div class="model-stats">
            <div class="stat-block">
              <div class="stat-num" style="color:{_cer_color(row['cer'])}">{row['cer']:.4f}</div>
              <div class="stat-label">CER</div>
            </div>
            <div class="stat-block">
              <div class="stat-num" style="color:{_wer_color(row['wer'])}">{row['wer']:.4f}</div>
              <div class="stat-label">WER</div>
            </div>
            <div class="stat-block">
              <div class="stat-num">{row['loanword_accuracy']:.4f}</div>
              <div class="stat-label">Loanword Acc</div>
            </div>
            <div class="stat-block">
              <div class="stat-num">{row['composite_score']:.4f}</div>
              <div class="stat-label">Composite</div>
            </div>
          </div>
          {"" if not cost else f'''
          <div class="model-meta">
            <span class="pill neutral"><span class="k">latency</span><span class="v">{cost.get("avg_latency", 0):.2f}s avg</span></span>
            <span class="pill neutral"><span class="k">cost</span><span class="v">${cost.get("estimated_cost", 0):.5f}</span></span>
            <span class="pill neutral"><span class="k">$/min</span><span class="v">${cost.get("cost_per_minute", 0):.4f}</span></span>
          </div>'''}
        </div>
        """

    # ── Per-sample table ────────────────────────────────────────────────────────
    all_ids = []
    for name in top_models:
        for s in per_model_samples.get(name, []):
            if s['id'] not in all_ids:
                all_ids.append(s['id'])

    lookup = {name: {s['id']: s for s in per_model_samples.get(name, [])} for name in top_models}

    # Table header — one CER+WER pair per model
    th_models = "".join(
        f'<th colspan="3" style="border-left:2px solid var(--gray-300);color:{MODEL_ACCENTS[i % len(MODEL_ACCENTS)]}">{name}</th>'
        for i, name in enumerate(top_models)
    )
    th_sub = "".join(
        '<th style="border-left:2px solid var(--gray-300)">CER</th><th>WER</th><th>Lat</th>'
        for _ in top_models
    )

    sample_rows = ""
    for sid in all_ids:
        is_noisy = "noise" in sid
        row_class = "noisy-row" if is_noisy else ""
        noise_badge = '<span class="pill noise-pill">noisy</span>' if is_noisy else ""

        cells = ""
        for name in top_models:
            s = lookup[name].get(sid)
            if s:
                cells += f"""
                  <td style="border-left:2px solid var(--gray-300);color:{_cer_color(s['cer'])};font-weight:600;font-family:var(--mono)">{s['cer']:.4f}</td>
                  <td style="color:{_wer_color(s['wer'])};font-weight:600;font-family:var(--mono)">{s['wer']:.4f}</td>
                  <td style="color:var(--gray-500);font-family:var(--mono)">{s.get('latency_sec','—')}s</td>
                """
            else:
                cells += '<td colspan="3" style="border-left:2px solid var(--gray-300);color:var(--gray-300)">—</td>'

        sample_rows += f"""
        <tr class="{row_class}">
          <td style="font-family:var(--mono);font-size:13px;white-space:nowrap">
            {sid} {noise_badge}
          </td>
          {cells}
        </tr>
        """

    # ── Noise impact ────────────────────────────────────────────────────────────
    noise_rows = ""
    for i, model_name in enumerate(top_models):
        samples = per_model_samples.get(model_name, [])
        clean = [s for s in samples if not s.get("noise")]
        noisy = [s for s in samples if s.get("noise")]
        if not clean or not noisy:
            continue
        clean_cer = sum(s["cer"] for s in clean) / len(clean)
        noisy_cer = sum(s["cer"] for s in noisy) / len(noisy)
        delta = noisy_cer - clean_cer
        accent = MODEL_ACCENTS[i % len(MODEL_ACCENTS)]
        noise_rows += f"""
        <tr>
          <td style="color:{accent};font-weight:600">{model_name}</td>
          <td style="font-family:var(--mono);color:var(--olive)">{clean_cer:.4f}</td>
          <td style="font-family:var(--mono);color:var(--rust)">{noisy_cer:.4f}</td>
          <td style="font-family:var(--mono);font-weight:700;color:{_delta_color(delta)}">+{delta:.4f}</td>
        </tr>
        """

    # ── Cost table ──────────────────────────────────────────────────────────────
    cost_rows = ""
    for i, model_name in enumerate(top_models):
        cost = cost_data.get(model_name, {})
        if not cost:
            continue
        accent = MODEL_ACCENTS[i % len(MODEL_ACCENTS)]
        cost_rows += f"""
        <tr>
          <td style="color:{accent};font-weight:600">{model_name}</td>
          <td style="font-family:var(--mono)">${cost.get('cost_per_minute',0):.4f}</td>
          <td style="font-family:var(--mono)">{cost.get('audio_minutes',0):.2f} min</td>
          <td style="font-family:var(--mono);font-weight:600">${cost.get('estimated_cost',0):.6f}</td>
          <td style="font-family:var(--mono)">{cost.get('avg_latency',0):.2f}s</td>
          <td style="font-family:var(--mono)">{cost.get('total_latency',0):.2f}s</td>
        </tr>
        """

    # ── Winner summary ──────────────────────────────────────────────────────────
    winner_cer = winner_cost = winner_speed = "—"
    if len(top_models) >= 2 and not ranked_df.empty:
        rows = {m: ranked_df[ranked_df['model'] == m].iloc[0] for m in top_models if m in ranked_df['model'].values}
        if rows:
            winner_cer = min(rows, key=lambda m: rows[m]['cer'])
            if cost_data:
                winner_cost = min(
                    (m for m in top_models if m in cost_data),
                    key=lambda m: cost_data[m].get('cost_per_minute', 999)
                )
                winner_speed = min(
                    (m for m in top_models if m in cost_data),
                    key=lambda m: cost_data[m].get('avg_latency', 999)
                )

    tldr_lines = []
    if winner_cer != "—":
        tldr_lines.append(f"<strong>{winner_cer}</strong> wins on accuracy (lowest CER).")
    if winner_cost != "—" and winner_cost != winner_cer:
        tldr_lines.append(f"<strong>{winner_cost}</strong> is cheapest per minute.")
    if winner_speed != "—":
        tldr_lines.append(f"<strong>{winner_speed}</strong> has the lowest latency.")
    tldr_text = " ".join(tldr_lines) if tldr_lines else "Run both models to generate a comparison."

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ASR Benchmark — OpenAI vs Deepgram</title>
<style>
  :root {{
    --ivory: #FAF9F5;
    --slate: #141413;
    --clay:  #D97757;
    --oat:   #E3DACC;
    --olive: #788C5D;
    --rust:  #B04A3F;
    --gray-100: #F0EEE6;
    --gray-300: #D1CFC5;
    --gray-500: #87867F;
    --gray-700: #3D3D3A;
    --white: #FFFFFF;
    --serif: ui-serif, Georgia, serif;
    --sans:  system-ui, -apple-system, sans-serif;
    --mono:  ui-monospace, 'SF Mono', Menlo, monospace;
    --radius-panel: 12px;
    --border: 1.5px solid var(--gray-300);
  }}

  * {{ box-sizing: border-box; }}
  html {{ scroll-behavior: smooth; }}

  body {{
    margin: 0;
    padding: 56px 24px 120px;
    background: var(--ivory);
    color: var(--slate);
    font-family: var(--sans);
    font-size: 15px;
    line-height: 1.6;
    -webkit-font-smoothing: antialiased;
  }}

  .page {{ max-width: 920px; margin: 0 auto; }}

  /* Header */
  header {{ margin-bottom: 36px; }}
  .header-label {{
    font-family: var(--mono);
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--gray-500);
    margin-bottom: 10px;
  }}
  h1 {{
    font-family: var(--serif);
    font-weight: 500;
    font-size: 40px;
    letter-spacing: -0.01em;
    margin: 0 0 14px;
    line-height: 1.15;
  }}
  .meta-row {{
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px 10px;
  }}
  .pill {{
    display: inline-flex;
    align-items: baseline;
    gap: 5px;
    font-size: 12px;
    font-weight: 600;
    border-radius: 999px;
    padding: 4px 11px;
    line-height: 1;
  }}
  .pill .k {{ font-weight: 400; opacity: 0.75; }}
  .pill .v {{ font-family: var(--mono); }}
  .pill.neutral {{
    background: var(--gray-100);
    color: var(--gray-700);
    border: var(--border);
  }}
  .pill.noise-pill {{
    background: #FEF3C7;
    color: #92400E;
    font-size: 10px;
    padding: 2px 7px;
    font-weight: 500;
  }}

  /* TL;DR */
  .tldr {{
    background: var(--slate);
    color: var(--ivory);
    border-radius: var(--radius-panel);
    padding: 22px 26px;
    margin-bottom: 48px;
  }}
  .tldr-label {{
    font-family: var(--mono);
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--oat);
    margin-bottom: 10px;
  }}
  .tldr p {{ margin: 0; font-size: 15.5px; line-height: 1.65; }}

  /* Sections */
  section {{ margin-bottom: 52px; scroll-margin-top: 24px; }}
  h2 {{
    font-family: var(--serif);
    font-weight: 500;
    font-size: 26px;
    letter-spacing: -0.01em;
    margin: 0 0 6px;
  }}
  hr.rule {{
    border: none;
    border-top: 1px solid var(--gray-300);
    margin: 0 0 24px;
  }}

  /* Model cards */
  .model-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 16px;
  }}
  .model-card {{
    background: var(--white);
    border: var(--border);
    border-radius: var(--radius-panel);
    padding: 24px 24px 20px;
  }}
  .model-rank {{
    font-family: var(--mono);
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 5px;
  }}
  .model-name {{
    font-family: var(--mono);
    font-size: 15px;
    font-weight: 600;
    color: var(--slate);
    margin-bottom: 20px;
    word-break: break-all;
  }}
  .model-stats {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-bottom: 18px;
  }}
  .stat-block {{ }}
  .stat-num {{
    font-family: var(--serif);
    font-size: 36px;
    font-weight: 500;
    line-height: 1;
    margin-bottom: 5px;
  }}
  .stat-label {{
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--gray-500);
  }}
  .model-meta {{
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    padding-top: 16px;
    border-top: 1px solid var(--gray-100);
  }}

  /* Tables */
  .table-wrap {{
    background: var(--white);
    border: var(--border);
    border-radius: var(--radius-panel);
    overflow: hidden;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
  }}
  thead th {{
    background: var(--gray-100);
    text-align: left;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--gray-500);
    padding: 11px 16px;
    border-bottom: 1px solid var(--gray-300);
  }}
  tbody td {{
    padding: 11px 16px;
    border-bottom: 1px solid var(--gray-100);
    font-size: 14px;
    color: var(--gray-700);
  }}
  tbody tr:last-child td {{ border-bottom: none; }}
  tbody tr:hover td {{ background: var(--gray-100); transition: background 0.1s; }}
  .noisy-row td {{ background: #FFFBEB; }}
  .noisy-row:hover td {{ background: #FEF3C7; }}

  /* Legend */
  .legend {{
    display: flex;
    gap: 20px;
    margin-top: 12px;
    font-size: 12px;
    color: var(--gray-500);
    flex-wrap: wrap;
  }}
  .legend-dot {{
    width: 9px; height: 9px;
    border-radius: 50%;
    display: inline-block;
    margin-right: 5px;
    vertical-align: middle;
  }}

  /* Footer */
  footer {{
    text-align: center;
    color: var(--gray-500);
    font-size: 12px;
    margin-top: 64px;
    font-family: var(--mono);
  }}

  @media (max-width: 640px) {{
    h1 {{ font-size: 28px; }}
    .model-stats {{ grid-template-columns: 1fr 1fr; }}
  }}
</style>
</head>
<body>
<div class="page">

  <!-- Header -->
  <header>
    <div class="header-label">ASR Benchmark Report</div>
    <h1>OpenAI vs Deepgram<br>Multilingual Kitchen Audio</h1>
    <div class="meta-row">
      <span class="pill neutral"><span class="k">date</span><span class="v">{today}</span></span>
      <span class="pill neutral"><span class="k">clips</span><span class="v">{num_samples}</span></span>
      <span class="pill neutral"><span class="k">languages</span><span class="v">EN · KO</span></span>
      <span class="pill neutral"><span class="k">models</span><span class="v">{len(top_models)}</span></span>
    </div>
  </header>

  <!-- TL;DR -->
  <div class="tldr">
    <div class="tldr-label">Summary</div>
    <p>{tldr_text}</p>
  </div>

  <!-- Model Results -->
  <section>
    <h2>Model Results</h2>
    <hr class="rule">
    <div class="model-grid">
      {stat_cards_html}
    </div>
    <div class="legend" style="margin-top:16px">
      <span><span class="legend-dot" style="background:var(--olive)"></span>Excellent (CER ≤ 0.05)</span>
      <span><span class="legend-dot" style="background:var(--clay)"></span>Good (CER ≤ 0.10)</span>
      <span><span class="legend-dot" style="background:var(--rust)"></span>Needs improvement (&gt; 0.10)</span>
    </div>
  </section>

  <!-- Per-sample breakdown -->
  <section>
    <h2>Per-Sample Breakdown</h2>
    <hr class="rule">
    <p style="font-size:13px;color:var(--gray-500);margin-bottom:16px">
      <span style="display:inline-block;width:10px;height:10px;background:#FFFBEB;border:1px solid var(--gray-300);border-radius:2px;margin-right:5px;vertical-align:middle"></span>
      Highlighted rows are noisy clips. Lat = API latency in seconds.
    </p>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Sample</th>
            {th_models}
          </tr>
          <tr>
            <th style="color:var(--gray-300)"></th>
            {th_sub}
          </tr>
        </thead>
        <tbody>
          {sample_rows}
        </tbody>
      </table>
    </div>
  </section>

  <!-- Noise impact -->
  <section>
    <h2>Noise Impact</h2>
    <hr class="rule">
    <p style="font-size:13px;color:var(--gray-500);margin-bottom:16px">Average CER on clean vs noisy clips. Lower Δ = more noise-robust.</p>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Model</th>
            <th>Clean avg CER</th>
            <th>Noisy avg CER</th>
            <th>Degradation Δ</th>
          </tr>
        </thead>
        <tbody>{noise_rows}</tbody>
      </table>
    </div>
  </section>

  <!-- Cost & Latency -->
  <section>
    <h2>Cost &amp; Latency</h2>
    <hr class="rule">
    <p style="font-size:13px;color:var(--gray-500);margin-bottom:16px">
      Cost = audio duration × price/min. Latency = API response time only — rate-limit pauses excluded.
    </p>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Model</th>
            <th>$/min</th>
            <th>Audio</th>
            <th>Est. cost</th>
            <th>Avg latency</th>
            <th>Total latency</th>
          </tr>
        </thead>
        <tbody>{cost_rows}</tbody>
      </table>
    </div>
  </section>

  <!-- Methodology -->
  <section>
    <h2>Methodology</h2>
    <hr class="rule">
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px 32px">
      <div>
        <p style="font-weight:600;margin-bottom:4px;color:var(--slate)">CER — Character Error Rate</p>
        <p style="font-size:13px;color:var(--gray-500);margin:0">Primary metric for Korean. Spaces stripped before comparison — Korean spacing is inconsistent across models. Follows KsponSpeech evaluation standard.</p>
      </div>
      <div>
        <p style="font-weight:600;margin-bottom:4px;color:var(--slate)">WER — Word Error Rate</p>
        <p style="font-size:13px;color:var(--gray-500);margin:0">Secondary metric. Less reliable for Korean due to ambiguous word boundaries. Use CER as primary for Korean content.</p>
      </div>
      <div>
        <p style="font-weight:600;margin-bottom:4px;color:var(--slate)">Loanword Accuracy</p>
        <p style="font-size:13px;color:var(--gray-500);margin:0">Accuracy on English loanwords and code-switched terms (오븐, 레시피, 간 맞추기). Critical for kitchen use case.</p>
      </div>
      <div>
        <p style="font-weight:600;margin-bottom:4px;color:var(--slate)">Composite Score</p>
        <p style="font-size:13px;color:var(--gray-500);margin:0">Weighted: CER 55% + WER 30% + Loanword 15%. Relative between models. Speed excluded — measures API latency, not model quality.</p>
      </div>
    </div>
  </section>

  <footer>
    korean-asr-benchmark &nbsp;·&nbsp; {today}
  </footer>

</div>
</body>
</html>"""

    return html


def save_html_report(
    output_dir: str,
    ranked_df: pd.DataFrame,
    top_models: List[str],
    per_model_samples: Dict[str, List[dict]] = None,
    cost_data: Dict[str, dict] = None,
    metadata: Dict = None,
    filename: str = "benchmark_report.html",
):
    html = generate_html_report(ranked_df, top_models, per_model_samples, cost_data, metadata)
    path = Path(output_dir) / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    print(f"HTML report saved to {path}")
    return path
