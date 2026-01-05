import streamlit as st
import os
import tempfile
import yaml
import json
import pandas as pd
import plotly.express as px
import cv2
import time
import importlib
import src.pipeline.orchestrator
importlib.reload(src.pipeline.orchestrator)
from src.pipeline.orchestrator import PipelineOrchestrator
from generate_choppy_video import create_choppy_video

# Page Config
st.set_page_config(
    page_title="SyntheSight AI",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for "Research Grade" look
st.markdown("""
<style>
    .reportview-container {
        background: #0e1117;
    }
    .main {
        background: #0e1117;
    }
    h1 {
        color: #4facfe;
    }
    .stButton>button {
        background-image: linear-gradient(to right, #4facfe 0%, #00f2fe 100%);
        color: white;
        border: none;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        width: 100%;
    }
    .metric-card {
        background-color: #1e2130;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #2e3140;
    }
</style>
""", unsafe_allow_html=True)

# Load Config
@st.cache_data
def load_config():
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)

config = load_config()

# Header
st.title("SyntheSight: Explainable Video Interpolation")
st.markdown("""
**Research-Grade Frame Interpolation with Advanced XAI.**  
Select a workflow below to either experiment with degradation and restoration, or simply restore an existing video.
""")

# Sidebar
st.sidebar.header("Configuration")

# Workflow Selection
workflow = st.sidebar.radio(
    "Select Workflow",
    ["1. Experiment: Choppify & Restore", "2. Restore Existing Video"]
)

st.sidebar.markdown("---")

if workflow == "1. Experiment: Choppify & Restore":
    st.sidebar.info("Upload a **Smooth** video. We will degrade it to 10 FPS and then attempt to restore it.")
    uploaded_file = st.sidebar.file_uploader("Upload Smooth Video", type=["mp4", "mov", "avi"])
else:
    st.sidebar.info("Upload a **Choppy/Low-FPS** video. We will smooth it using AI interpolation.")
    uploaded_file = st.sidebar.file_uploader("Upload Choppy Video", type=["mp4", "mov", "avi"])

# Main Logic
if uploaded_file:
    # Save uploaded file to temp
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    tfile.write(uploaded_file.read())
    input_path = tfile.name
    
    # Sidebar Preview
    st.sidebar.subheader("Input Preview")
    st.sidebar.video(input_path)
    
    # Settings
    st.sidebar.markdown("---")
    st.sidebar.subheader("Settings")
    
    # For workflow 1, we always do multi-stage, but let user choose max quality
    # For workflow 2, user chooses target
    
    if workflow == "2. Restore Existing Video":
        target_fps_mult = st.sidebar.selectbox("Target Smoothness", ["2x (Standard)", "4x (Ultra Smooth)"])
    else:
        st.sidebar.markdown("**Experiment Settings:**")
        st.sidebar.markdown("- Choppy Target: **10 FPS**")
        st.sidebar.markdown("- Restoration: **10 -> 20 -> 40 FPS**")
        target_fps_mult = "4x (Ultra Smooth)" # Force 4x for experiment to show full range

    show_debug = st.sidebar.checkbox("Generate XAI Debug Frames", value=True)
    
    # Update Config based on UI
    config['explanation']['save_debug_frames'] = show_debug
    
    if st.sidebar.button("Run Analysis", type="primary"):
        st.markdown("---")
        
        # Layout for Progress
        st.subheader("Processing Pipeline")
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Metrics Container
        st.markdown("### Live Metrics")
        col_m1, col_m2, col_m3 = st.columns(3)
        metric_motion = col_m1.empty()
        metric_consistency = col_m2.empty()
        metric_edge = col_m3.empty()
        
        # Callback
        def progress_callback(current, total, metrics=None):
            if total > 0:
                progress = min(current / total, 1.0)
                progress_bar.progress(progress)
                if metrics:
                    metric_motion.metric("Motion Complexity", f"{metrics.get('motion_complexity', 0):.2f}")
                    metric_consistency.metric("Temporal Consistency", f"{metrics.get('temporal_consistency', 0):.2f}")
                    metric_edge.metric("Edge Preservation", f"{metrics.get('edge_preservation', 0):.2f}")

        # Run Pipeline
        orchestrator = PipelineOrchestrator(config)
        
        results = {} # Store paths to display later
        
        try:
            # --- WORKFLOW 1: CHOPPIFY & RESTORE ---
            if workflow == "1. Experiment: Choppify & Restore":
                results['original'] = input_path
                
                # Step 1: Choppify
                status_text.markdown("### [1/3] Generating Choppy Video (10 FPS)...")
                choppy_path = input_path.replace(".mp4", "_choppy.mp4")
                create_choppy_video(input_path, choppy_path, target_fps=10)
                results['choppy'] = choppy_path
                
                # Step 2: Restore Pass 1 (10 -> 20)
                status_text.markdown("### [2/3] Restoration Pass 1 (10 -> 20 FPS)...")
                pass1_path = input_path.replace(".mp4", "_restored_20fps.mp4")
                pass1_report = input_path.replace(".mp4", "_report_pass1.json")
                
                progress_bar.progress(0)
                orchestrator.process_video(choppy_path, pass1_path, pass1_report, progress_callback=progress_callback)
                results['restored_2x'] = pass1_path
                
                # Step 3: Restore Pass 2 (20 -> 40)
                status_text.markdown("### [3/3] Restoration Pass 2 (20 -> 40 FPS)...")
                pass2_path = input_path.replace(".mp4", "_restored_40fps.mp4")
                pass2_report = input_path.replace(".mp4", "_report_pass2.json")
                
                progress_bar.progress(0)
                orchestrator.process_video(pass1_path, pass2_path, pass2_report, progress_callback=progress_callback)
                results['restored_4x'] = pass2_path
                
                final_report_path = pass2_report # Use final report for dashboard

            # --- WORKFLOW 2: RESTORE EXISTING ---
            else:
                results['original'] = input_path
                
                # Pass 1
                status_text.markdown("### [1/2] Restoration Pass 1 (2x)...")
                output_path = input_path.replace(".mp4", "_out.mp4")
                report_path = input_path.replace(".mp4", "_report.json")
                
                progress_bar.progress(0)
                orchestrator.process_video(input_path, output_path, report_path, progress_callback=progress_callback)
                results['restored_2x'] = output_path
                final_report_path = report_path
                
                # Pass 2 (Optional)
                if target_fps_mult == "4x (Ultra Smooth)":
                    status_text.markdown("### [2/2] Restoration Pass 2 (4x)...")
                    input_pass2 = output_path
                    output_pass2 = output_path.replace(".mp4", "_4x.mp4")
                    report_pass2 = report_path.replace(".json", "_4x.json")
                    
                    progress_bar.progress(0)
                    orchestrator.process_video(input_pass2, output_pass2, report_pass2, progress_callback=progress_callback)
                    
                    results['restored_4x'] = output_pass2
                    final_report_path = report_pass2

            status_text.success("Processing Complete!")
            
            # --- Results Section ---
            st.markdown("---")
            st.header("Visual Results Comparison")
            
            if workflow == "1. Experiment: Choppify & Restore":
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("1. Original (Smooth)")
                    st.video(results['original'])
                    st.subheader("3. Restored (20 FPS)")
                    st.video(results['restored_2x'])
                with col2:
                    st.subheader("2. Degraded (10 FPS)")
                    st.video(results['choppy'])
                    st.subheader("4. Final Restoration (40 FPS)")
                    st.video(results['restored_4x'])
            else:
                cols = st.columns(len(results))
                idx = 0
                for key, path in results.items():
                    with cols[idx]:
                        st.subheader(f"{key.replace('_', ' ').title()}")
                        st.video(path)
                    idx += 1
                
            # Load Report Data
            with open(final_report_path, 'r') as f:
                report_data = json.load(f)
                
            # --- Dashboard Section ---
            st.markdown("---")
            st.header("Explainable AI Dashboard")
            
            # Metrics Overview
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Frames", report_data['metadata']['total_frames_processed'])
            m2.metric("Output FPS", f"{report_data['metadata']['frame_rate_output']:.2f}")
            m3.metric("Avg Severity", f"{report_data['summary']['average_severity']:.4f}")
            m4.metric("Processing Time", f"{report_data['summary']['processing_time_seconds']:.2f}s")
            
            # Graphs
            st.subheader("Temporal Quality Metrics")
            df = pd.DataFrame([f['metrics'] for f in report_data['frames']])
            df['frame'] = [f['frame_number'] for f in report_data['frames']]
            df['verdict'] = [f['verdict'] for f in report_data['frames']]
            
            fig = px.line(df, x='frame', y=['motion_complexity', 'temporal_consistency', 'edge_preservation'],
                          title="Frame-by-Frame Analysis", template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
            
            # --- XAI Inspector ---
            st.subheader("Deep Dive: Frame Inspector")
            st.markdown("Explore the AI's internal reasoning for each frame.")
            
            selected_frame_idx = st.slider("Select Frame", 0, len(report_data['frames'])-1, 0)
            frame_info = report_data['frames'][selected_frame_idx]
            
            col_xai_img, col_xai_info = st.columns([2, 1])
            
            with col_xai_img:
                debug_fname = f"debug_frames/frame_{selected_frame_idx}_xai.jpg"
                if os.path.exists(debug_fname):
                    st.image(debug_fname, caption=f"XAI Composite: Frame {selected_frame_idx}", use_column_width=True)
                else:
                    st.info("No Anomaly Detected / No Debug Frame Saved for this frame.")
            
            with col_xai_info:
                st.markdown(f"### Frame {selected_frame_idx}")
                st.markdown(f"**Verdict:** `{frame_info['verdict']}`")
                st.markdown(f"**Severity:** {frame_info['severity_score']:.2f}")
                
                st.markdown("#### Explanations:")
                for exp in frame_info['explanation']:
                    st.write(f"- {exp}")
                
                st.markdown("#### Metrics:")
                st.json(frame_info['metrics'])

        except Exception as e:
            st.error(f"An error occurred: {e}")
            st.exception(e)

else:
    st.info("Please upload a video from the sidebar to begin.")


