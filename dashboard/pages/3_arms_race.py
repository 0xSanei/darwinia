"""Arms Race — adversarial co-evolution visualization."""

import streamlit as st
import plotly.graph_objects as go
import json
from pathlib import Path

st.set_page_config(page_title="Arms Race", layout="wide")
st.title("\u2694\ufe0f Adversarial Arms Race")

output = Path('output')
report_path = output / 'final_report.json'

if not report_path.exists():
    st.warning("No evolution data. Run `make evolve` first.")
    st.stop()

report = json.loads(report_path.read_text())
generations = report.get('generations', [])

if not generations:
    st.warning("No generation data found.")
    st.stop()

# Extract arena data from generation snapshots
# We'll show survival rates and fitness progression together
gen_nums = [g['generation'] for g in generations]
champ_fitness = [g['champion_fitness'] for g in generations]
avg_fitness = [g['avg_fitness'] for g in generations]

# Survival rate over time (from fitness data)
st.subheader("Fitness + Adversarial Pressure")

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=gen_nums, y=champ_fitness,
    mode='lines+markers', name='Champion Fitness',
    line=dict(color='gold', width=2),
))
fig.add_trace(go.Scatter(
    x=gen_nums, y=avg_fitness,
    mode='lines', name='Avg Fitness',
    line=dict(color='cyan', width=1.5, dash='dash'),
))

# Mark arena start
arena_start = 5
fig.add_vline(x=arena_start, line_dash="dash", line_color="red",
              annotation_text="Arena Starts", annotation_position="top left")

fig.update_layout(
    title='Evolution Under Adversarial Pressure',
    xaxis_title='Generation',
    yaxis_title='Fitness Score',
    template='plotly_dark',
    height=500,
)
st.plotly_chart(fig, use_container_width=True)

# Attack type descriptions
st.subheader("Attack Arsenal")
attacks = {
    'Rug Pull': 'Steady rise followed by sudden 90%+ crash',
    'Fake Breakout': 'Price breaks resistance then immediately reverses',
    'Slow Bleed': 'Gradual decline with misleading bounces',
    'Whipsaw': 'Rapid alternating moves to trigger stop losses',
    'Volume Mirage': 'Volume spike with no price follow-through',
    'Pump & Dump': 'Rapid pump followed by equally rapid dump',
}

cols = st.columns(3)
for i, (name, desc) in enumerate(attacks.items()):
    with cols[i % 3]:
        st.markdown(f"**{name}**")
        st.caption(desc)

# Population diversity vs fitness scatter
st.subheader("Diversity vs Fitness Tradeoff")
diversity = [g['genetic_diversity'] for g in generations]

fig_scatter = go.Figure()
fig_scatter.add_trace(go.Scatter(
    x=diversity, y=avg_fitness,
    mode='markers',
    marker=dict(
        size=8,
        color=gen_nums,
        colorscale='Viridis',
        showscale=True,
        colorbar=dict(title="Generation"),
    ),
    text=[f"Gen {g}" for g in gen_nums],
))
fig_scatter.update_layout(
    title='Genetic Diversity vs Average Fitness',
    xaxis_title='Genetic Diversity',
    yaxis_title='Average Fitness',
    template='plotly_dark',
    height=450,
)
st.plotly_chart(fig_scatter, use_container_width=True)
