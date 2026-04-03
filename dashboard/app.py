"""
Darwinia Dashboard — visualize agent evolution in real time.
"""

import streamlit as st
import json
from pathlib import Path

st.set_page_config(
    page_title="Darwinia — Agent Evolution",
    page_icon="\U0001f9ec",
    layout="wide",
)

st.title("\U0001f9ec Darwinia — The Self-Evolving Agent Ecosystem")
st.markdown("> Agents that evolve through adversarial self-play")

st.markdown("""
### Navigation
- **Evolution**: Watch fitness improve over generations
- **Family Tree**: Trace the ancestry of champion agents
- **Arms Race**: See how attacks and defenses co-evolve
- **Discoveries**: View patterns agents discovered on their own
""")

output = Path(__file__).resolve().parent.parent / 'output'
if (output / 'evolution_summary.json').exists():
    summary = json.loads((output / 'evolution_summary.json').read_text())
    if summary:
        latest = summary[-1]
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Generations", latest['generation'] + 1)
        col2.metric("Champion Fitness", f"{latest['champion_fitness']:.4f}")
        col3.metric("Avg Fitness", f"{latest['avg_fitness']:.4f}")
        col4.metric("Genetic Diversity", f"{latest['genetic_diversity']:.4f}")
else:
    st.info("No evolution data found. Run `make evolve` first.")
