"""Evolution view — fitness curves and population stats."""

import streamlit as st
import plotly.graph_objects as go
import json
from pathlib import Path

st.set_page_config(page_title="Evolution", layout="wide")
st.title("\U0001f4c8 Evolution Progress")

output = Path(__file__).resolve().parent.parent.parent / 'output'
summary_path = output / 'evolution_summary.json'

if not summary_path.exists():
    st.warning("No evolution data. Run `make evolve` first.")
    st.stop()

summary = json.loads(summary_path.read_text())

gens = [s['generation'] for s in summary]
champ_fitness = [s['champion_fitness'] for s in summary]
avg_fitness = [s['avg_fitness'] for s in summary]
diversity = [s['genetic_diversity'] for s in summary]

# Fitness curve
fig_fitness = go.Figure()
fig_fitness.add_trace(go.Scatter(
    x=gens, y=champ_fitness, mode='lines+markers',
    name='Champion', line=dict(color='gold', width=2)
))
fig_fitness.add_trace(go.Scatter(
    x=gens, y=avg_fitness, mode='lines',
    name='Average', line=dict(color='cyan', width=1.5)
))
fig_fitness.update_layout(
    title='Fitness Over Generations',
    xaxis_title='Generation',
    yaxis_title='Fitness Score',
    template='plotly_dark',
    height=500,
)
st.plotly_chart(fig_fitness, use_container_width=True)

# Diversity curve
fig_div = go.Figure()
fig_div.add_trace(go.Scatter(
    x=gens, y=diversity, mode='lines+markers',
    name='Genetic Diversity', line=dict(color='lime', width=2),
    fill='tozeroy', fillcolor='rgba(0,255,0,0.1)'
))
fig_div.update_layout(
    title='Genetic Diversity Over Generations',
    xaxis_title='Generation',
    yaxis_title='Avg Euclidean Distance',
    template='plotly_dark',
    height=400,
)
st.plotly_chart(fig_div, use_container_width=True)

# Champion gene distribution for latest generation
st.subheader("Latest Champion DNA")
champions_dir = output / 'champions'
latest_champ_path = sorted(champions_dir.glob('*.json'), key=lambda p: int(p.stem.split('_')[-1])) if champions_dir.exists() else []
if latest_champ_path:
    champ = json.loads(latest_champ_path[-1].read_text())
    genes = champ.get('genes', {})

    fig_genes = go.Figure(go.Bar(
        x=list(genes.keys()),
        y=list(genes.values()),
        marker_color='gold',
    ))
    fig_genes.update_layout(
        title=f"Champion Genes (Gen {champ.get('generation', '?')})",
        yaxis_range=[0, 1],
        template='plotly_dark',
        height=400,
    )
    st.plotly_chart(fig_genes, use_container_width=True)
