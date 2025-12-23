import streamlit as st
import json
import pandas as pd
import plotly.express as px
import os
from PIL import Image

st.set_page_config(page_title="SYNTHESIGHT Research Dashboard", layout="wide")

st.title("SYNTHESIGHT: Explainable Frame Interpolation")

REPORT_PATH = "final_report.json"

@st.cache_data
def load_data():
    if not os.path.exists(REPORT_PATH):
        return None
    with open(REPORT_PATH, 'r') as f:
        data = json.load(f)
    return data

data = load_data()

if data is None:
    st.error(f"Report file not found at {os.path.abspath(REPORT_PATH)}.")
    st.info("Please run './1_generate_data.sh' to generate the data first.")
else:
    # Sidebar
    st.sidebar.header("Controls")
    
    # Convert to DataFrame for easy plotting
    df = pd.DataFrame([
        {
            "frame": d["frame_pair"],
            "motion": d["metrics"]["motion_complexity"],
            "consistency": d["metrics"]["temporal_consistency"],
            "occlusion": d["metrics"]["occlusion_risk"],
            "verdict": d["explanation"]["verdict"]
        }
        for d in data
    ])
    
    # Global Metrics
    st.header("Global Analytics")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Frames", len(df))
    col2.metric("Avg Consistency", f"{df['consistency'].mean():.2f}")
    col3.metric("Avg Motion", f"{df['motion'].mean():.2f}")
    col4.metric("Failure Rate", f"{(df['verdict'] == 'FAIL').mean() * 100:.1f}%")
    
    # Charts
    st.subheader("Temporal Analysis")
    tab1, tab2 = st.tabs(["Consistency vs Motion", "Metric Evolution"])
    
    with tab1:
        fig = px.scatter(df, x="motion", y="consistency", color="verdict", 
                         hover_data=["frame"], title="Consistency vs Motion Complexity")
        st.plotly_chart(fig, use_container_width=True)
        
    with tab2:
        fig2 = px.line(df, x="frame", y=["consistency", "motion", "occlusion"], 
                       title="Metrics over Time")
        st.plotly_chart(fig2, use_container_width=True)

    # Frame Inspector
    st.header("Frame Inspector")
    
    if len(data) > 0:
        selected_frame_idx = st.slider("Select Frame Pair", 0, len(data)-1, 0)
        frame_data = data[selected_frame_idx]
        
        st.subheader(f"Frame Pair {frame_data['frame_pair']}")
        
        # Metrics for this frame
        m_col1, m_col2, m_col3 = st.columns(3)
        m_col1.metric("Motion", f"{frame_data['metrics']['motion_complexity']:.2f}")
        m_col2.metric("Consistency", f"{frame_data['metrics']['temporal_consistency']:.2f}")
        m_col3.metric("Occlusion Risk", f"{frame_data['metrics']['occlusion_risk']:.2f}")
        
        # Explanation
        verdict_color = "red" if frame_data['explanation']['verdict'] == "FAIL" else "green"
        st.markdown(f"**Verdict:** :{verdict_color}[{frame_data['explanation']['verdict']}]")
        st.markdown("**Explanation:**")
        for exp in frame_data['explanation']['details']:
            st.markdown(f"- {exp}")
            
        # Visuals
        paths = frame_data.get("paths", {})
        
        if paths:
            col_prev, col_interp, col_next = st.columns(3)
            
            with col_prev:
                p = paths.get("prev")
                if p and os.path.exists(p):
                    st.image(p, caption="Previous Frame", use_column_width=True)
                else:
                    st.info("Image not available")
                
            with col_interp:
                p = paths.get("interp")
                if p and os.path.exists(p):
                    st.image(p, caption="Interpolated Frame", use_column_width=True)
                else:
                    st.info("Image not available")
                
            with col_next:
                p = paths.get("next")
                if p and os.path.exists(p):
                    st.image(p, caption="Next Frame", use_column_width=True)
                else:
                    st.info("Image not available")
                
            if paths.get("heatmap") and os.path.exists(paths["heatmap"]):
                st.subheader("XAI Heatmap (Artifact Risk)")
                st.image(paths["heatmap"], caption="Artifact Heatmap", use_column_width=True)
        else:
            st.info("Debug frames were not saved for this timestamp. Check `debug_save_interval` in `config.yaml`.")
    else:
        st.warning("No data available.")
