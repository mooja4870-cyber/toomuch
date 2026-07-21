import streamlit as st
import plotly.graph_objects as go
import pandas as pd

fig = go.Figure()
fig.add_trace(go.Bar(x=['A', 'B', 'C'], y=[1, 3, 2], marker_color=['red', 'blue', 'green']))
fig.add_shape(
    type="line", x0='B', y0=0, x1='B', y1=4,
    line=dict(color="White", width=3, dash="dash"),
    name="target_line"
)
st.plotly_chart(fig)

st.markdown("""
<style>
/* Try to target SVG line */
path[stroke-dasharray] {
    animation: blinker 1s linear infinite;
}
@keyframes blinker {
    50% { opacity: 0; }
}
</style>
""", unsafe_allow_html=True)
