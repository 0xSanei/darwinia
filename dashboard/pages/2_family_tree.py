"""Family Tree — trace ancestry of champion agents."""

import streamlit as st
import plotly.graph_objects as go
import json
from pathlib import Path

st.set_page_config(page_title="Family Tree", layout="wide")
st.title("\U0001f333 Champion Family Tree")

output = Path('output')
champions_dir = output / 'champions'

if not champions_dir.exists() or not list(champions_dir.glob('*.json')):
    st.warning("No champion data. Run `make evolve` first.")
    st.stop()

# Load all champions
champions = []
for f in sorted(champions_dir.glob('*.json')):
    champions.append(json.loads(f.read_text()))

# Build lineage graph
ids = []
labels = []
parents_list = []
fitness_vals = []

for c in champions:
    cid = c['id']
    gen = c['generation']
    fit = c.get('fitness', 0)
    ids.append(cid)
    labels.append(f"Gen {gen}<br>ID: {cid}<br>Fit: {fit:.4f}")
    fitness_vals.append(fit)

    if c.get('parent_ids'):
        for pid in c['parent_ids']:
            if pid in ids:
                parents_list.append((pid, cid))

# Treemap visualization
if champions:
    treemap_labels = []
    treemap_parents = []
    treemap_values = []

    treemap_labels.append("Darwinia")
    treemap_parents.append("")
    treemap_values.append(0)

    for c in champions:
        gen = c['generation']
        cid = c['id']
        fit = c.get('fitness', 0)
        treemap_labels.append(f"Gen{gen}: {cid}")
        treemap_parents.append("Darwinia")
        treemap_values.append(max(0.01, fit))

    fig = go.Figure(go.Treemap(
        labels=treemap_labels,
        parents=treemap_parents,
        values=treemap_values,
        textinfo="label+value",
        marker=dict(
            colors=treemap_values,
            colorscale='Viridis',
        ),
    ))
    fig.update_layout(
        title='Champion Agents by Generation',
        template='plotly_dark',
        height=600,
    )
    st.plotly_chart(fig, use_container_width=True)

# Champion stats table
st.subheader("Champion History")
table_data = []
for c in champions:
    genes = c.get('genes', {})
    top_gene = max(genes, key=genes.get) if genes else 'N/A'
    table_data.append({
        'Generation': c['generation'],
        'ID': c['id'],
        'Fitness': f"{c.get('fitness', 0):.4f}",
        'Top Gene': top_gene,
        'Parents': ', '.join(c.get('parent_ids', [])) or 'Genesis',
    })

st.dataframe(table_data, use_container_width=True)
