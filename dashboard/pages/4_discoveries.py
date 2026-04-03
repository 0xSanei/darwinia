"""Discoveries — patterns agents discovered on their own."""

import streamlit as st
import plotly.graph_objects as go
import json
from pathlib import Path

st.set_page_config(page_title="Discoveries", layout="wide")
st.title("\U0001f52c Pattern Discovery")

output = Path(__file__).resolve().parent.parent.parent / 'output'
report_path = output / 'final_report.json'

if not report_path.exists():
    st.warning("No evolution data. Run `make evolve` first.")
    st.stop()

report = json.loads(report_path.read_text())
patterns = report.get('patterns_discovered', [])

if not patterns:
    st.info("No patterns discovered in this run.")
    st.stop()

st.metric("Patterns Discovered", len(patterns))

# Patterns table
st.subheader("Discovered Patterns")
table_data = []
for p in patterns:
    table_data.append({
        'Name': p['name'],
        'Predictive Power': f"{p['predictive_power']:.2f}",
        'Human Equivalent': p.get('human_equivalent', 'N/A'),
        'Discovered By': p.get('discovered_by', 'N/A'),
        'Generation': p.get('generation', 'N/A'),
    })

st.dataframe(table_data, use_container_width=True)

# Convergence radar chart
st.subheader("Gene Convergence Radar")

convergence_patterns = [p for p in patterns if p['name'].startswith('converged_')]
if convergence_patterns:
    gene_names = []
    convergence_vals = []

    for p in convergence_patterns:
        for gene, val in p['features'].items():
            gene_names.append(gene.replace('weight_', '').replace('_', ' ').title())
            convergence_vals.append(p['predictive_power'])

    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=convergence_vals,
        theta=gene_names,
        fill='toself',
        name='Convergence Strength',
        line=dict(color='gold'),
        fillcolor='rgba(255, 215, 0, 0.2)',
    ))
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 1]),
            bgcolor='rgba(0,0,0,0)',
        ),
        template='plotly_dark',
        height=500,
        title='Gene Convergence — What Survivors Agree On',
    )
    st.plotly_chart(fig_radar, use_container_width=True)

# Gene combinations
st.subheader("Linked Gene Pairs")
linked = [p for p in patterns if p['name'].startswith('linked_')]
if linked:
    for p in linked:
        genes = list(p.get('features', {}).keys())
        if len(genes) < 2:
            continue
        power = p['predictive_power']
        equiv = p.get('human_equivalent', '')
        st.markdown(f"- **{genes[0]}** <-> **{genes[1]}** (r={power:.2f}) — {equiv}")
else:
    st.info("No strongly linked gene pairs found.")
