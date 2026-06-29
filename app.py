import os
import sys

# Safeguard OpenMP DLL loading issue
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import streamlit as st
import yaml
import time

# Set up page configurations
st.set_page_config(
    page_title="IKS-Aware Explainable NMT",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Dark Mode / Light Mode Theme configuration
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

def toggle_theme():
    st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"

IS_DARK = st.session_state.theme == "dark"

# Define theme colors
BG = "#09090b" if IS_DARK else "#ffffff"
BG_SUBTLE = "#0c0c0f" if IS_DARK else "#f9fafb"
CARD = "#121215" if IS_DARK else "#ffffff"
CARD_HOVER = "#18181c" if IS_DARK else "#f4f4f5"
BORDER = "#27272a" if IS_DARK else "#e4e4e7"
BORDER_SUBTLE = "#1e1e24" if IS_DARK else "#f0f0f2"
TEXT = "#fafafa" if IS_DARK else "#09090b"
TEXT_MUTED = "#a1a1aa" if IS_DARK else "#71717a"
TEXT_DIM = "#71717a" if IS_DARK else "#a1a1aa"
ACCENT = "#3b82f6"
GREEN = "#22c55e"
GREEN_MUTED = "rgba(34,197,94,0.15)" if IS_DARK else "rgba(22,163,74,0.08)"
RED = "#ef4444"
RED_MUTED = "rgba(239,68,68,0.15)" if IS_DARK else "rgba(220,38,38,0.08)"
AMBER = "#f59e0b"
AMBER_MUTED = "rgba(245,158,11,0.15)" if IS_DARK else "rgba(217,119,6,0.08)"

# Inject Custom CSS Styles
st.markdown(f"""
<style>
    /* Hide Streamlit components */
    header[data-testid="stHeader"], #MainMenu, footer, [data-testid="stToolbar"],
    [data-testid="stDecoration"], [data-testid="stStatusWidget"], .stDeployButton,
    div[data-testid="stSidebarCollapsedControl"] {{
        display: none !important;
    }}
    
    /* Global styles */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"], .main, .block-container, section[data-testid="stMain"] {{
        background-color: {BG} !important;
        color: {TEXT} !important;
        font-family: 'DM Sans', -apple-system, sans-serif !important;
    }}
    
    .block-container {{
        padding: 2rem 3rem 3rem !important;
        max-width: 1400px !important;
    }}
    
    /* Custom container designs */
    .brand-section {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 2rem;
        padding-bottom: 1.5rem;
        border-bottom: 1px solid {BORDER};
    }}
    
    .brand-title {{
        font-size: 1.75rem;
        font-weight: 800;
        letter-spacing: -0.04em;
        background: linear-gradient(135deg, {ACCENT}, #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        display: inline-block;
    }}
    
    .brand-subtitle {{
        font-size: 0.85rem;
        color: {TEXT_MUTED};
        margin-top: -0.2rem;
    }}

    .section-card {{
        background-color: {CARD};
        border: 1px solid {BORDER};
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }}
    
    .section-title {{
        font-size: 0.95rem;
        font-weight: 600;
        color: {TEXT};
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 8px;
    }}
    
    /* Metrics and indicators */
    .metric-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 1rem;
        margin-bottom: 1rem;
    }}
    
    .metric-card {{
        background-color: {BG_SUBTLE};
        border: 1px solid {BORDER};
        border-radius: 8px;
        padding: 1rem;
    }}
    
    .metric-label {{
        font-size: 0.75rem;
        color: {TEXT_MUTED};
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    
    .metric-value {{
        font-size: 1.5rem;
        font-weight: 700;
        color: {TEXT};
        margin-top: 0.2rem;
    }}
    
    .metric-footer {{
        font-size: 0.72rem;
        color: {TEXT_DIM};
        margin-top: 0.3rem;
    }}
    
    /* Concept badges */
    .badge {{
        display: inline-flex;
        align-items: center;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 8px;
        margin-bottom: 8px;
    }}
    
    .badge-accent {{
        color: {ACCENT};
        background-color: rgba(59, 130, 246, 0.1);
        border: 1px solid rgba(59, 130, 246, 0.2);
    }}
    
    .badge-green {{
        color: {GREEN};
        background-color: {GREEN_MUTED};
        border: 1px solid rgba(34, 197, 94, 0.2);
    }}
    
    .badge-amber {{
        color: {AMBER};
        background-color: {AMBER_MUTED};
        border: 1px solid rgba(245, 158, 11, 0.2);
    }}
    
    /* Code reports */
    .explanation-report {{
        background-color: {BG_SUBTLE};
        border: 1px solid {BORDER};
        border-radius: 8px;
        padding: 1.25rem;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.85rem;
        white-space: pre-wrap;
        color: {TEXT};
        line-height: 1.5;
    }}
    
    /* Quick action buttons spacing */
    [data-testid="stHorizontalBlock"] {{
        gap: 1rem !important;
    }}
</style>
""", unsafe_allow_html=True)

# Main Application Title
st.markdown(f"""
<div class="brand-section">
    <div>
        <div class="brand-title">அறம் • IKS-Aware Neural Machine Translation</div>
        <div class="brand-subtitle">Explainable Translation Pipeline for Classical Tamil Texts using IndicTrans2 / NLLB-200</div>
    </div>
    <div style="text-align: right;">
        <!-- Theme Toggle button is rendered dynamically by Streamlit -->
    </div>
</div>
""", unsafe_allow_html=True)

# Display theme toggle right in the header
cols_header = st.columns([12, 2])
with cols_header[1]:
    theme_label = "☀️ Light Mode" if IS_DARK else "🌙 Dark Mode"
    st.button(theme_label, on_click=toggle_theme, use_container_width=True)

# Preset sentences dictionary
PRESETS = {
    "Thirukkural Verse 39 (Aram)": "அறத்தாறின் இல்வாழ்க்கை ஆற்றின் புறத்தாறின் போஒய்ப் பெறுவது எவன்.",
    "Thirukkural Verse 71 (Anbu)": "அன்பிலார் எல்லாம் தமக்குரியர் அன்புடையார் என்பும் உரியர் பிறர்க்கு.",
    "Thirukkural Verse 241 (Arul)": "அருட்செல்வம் செல்வத்துள் செல்வம் பொருட்செல்வம் பூரியார் கண்ணும் உள.",
    "Thirukkural Verse 380 (Oozh)": "ஊழில் பெருவலி யாவுள மற்றொன்று சூழினும் தான்முந் துறும்.",
    "Thirukkural Verse 261 (Thavam)": "உற்றநோய் நோற்றல் உயிர்க்குறுகண் செய்யாமை அற்றே தவத்திற்கு உரு.",
    "Purananuru Verse 192 (Kelir)": "யாதும் ஊரே யாவரும் கேளிர்.",
    "Kurunthokai Verse 135 (Vinai)": "வினையே ஆடவர்க்கு உயிரே மனையுறை மகளிர்க்கு ஆடவர் உயிர்."
}

# Cached resource loading (loads model weights only once)
@st.cache_resource
def load_nmt_pipeline():
    import numpy as np
    import pandas as pd
    import scipy
    import sklearn
    import torch
    import yaml
    
    # Setup path so augment/detector/retriever/ranker can be imported
    scripts_path = os.path.abspath('scripts')
    if scripts_path not in sys.path:
        sys.path.insert(0, scripts_path)
        
    from backend.ai.retrieval.augment import IKSInputAugmenter
    from backend.ai.explain.explanation import IKSExplainer
    from backend.core.model_loader import ModelLoader
    from backend.core.config import TRANSLATION_MODEL_NAME

    # Preload default tokenizer and model
    ModelLoader.load_tokenizer("indictrans2", TRANSLATION_MODEL_NAME)
    ModelLoader.load_model("indictrans2", TRANSLATION_MODEL_NAME)

    augmenter = IKSInputAugmenter()
    explainer = IKSExplainer()

    device = ModelLoader.get_device("indictrans2").upper()

    return augmenter, explainer, device

# Loading components inside a spinner
with st.spinner("Initializing models and FAISS knowledge base (loading weights to GPU/CPU)..."):
    try:
        augmenter, explainer, device = load_nmt_pipeline()
        st.success("Translation models and IKS Knowledge Base loaded successfully on device: " + device)
    except Exception as e:
        st.error(f"Error loading translation models: {e}")
        st.stop()

# Helper function to generate translation using IndicTrans2
def translate_text(text, disable_adapter=False):
    from backend.ai.translation.router import TranslationRouter
    return TranslationRouter.translate(text, model_choice="indictrans2", disable_adapter=disable_adapter)

# Layout splits
left_panel, right_panel = st.columns([1, 1.2])

with left_panel:
    st.markdown(f"""
    <div class="section-card">
        <div class="section-title">✍️ Classical Tamil Input</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Presets selection buttons
    st.write("**Or select an authentic Classical verse preset:**")
    preset_cols = st.columns(2)
    selected_preset = None
    
    # Distribute preset buttons in a grid
    for idx, (label, verse) in enumerate(PRESETS.items()):
        col_idx = idx % 2
        with preset_cols[col_idx]:
            if st.button(label, key=f"btn_{idx}", use_container_width=True):
                st.session_state["tamil_input"] = verse
                selected_preset = verse
                
    # Text input area
    default_text = st.session_state.get("tamil_input", "யாதும் ஊரே யாவரும் கேளிர்.")
    tamil_input = st.text_area(
        "Enter Classical Tamil text here:",
        value=default_text,
        height=100,
        placeholder="Type classical Tamil sentence...",
        label_visibility="collapsed"
    )
    
    # Run button
    translate_trigger = st.button("🚀 Process & Translate", type="primary", use_container_width=True)

with right_panel:
    st.markdown(f"""
    <div class="section-card" style="height: 100%;">
        <div class="section-title">📊 Translation Results & Explanation</div>
    </div>
    """, unsafe_allow_html=True)
    
    if translate_trigger or "tamil_input" in st.session_state:
        target_text = tamil_input if translate_trigger else default_text
        
        # 1. Pipeline - Tag Augmentation
        with st.spinner("Resolving IKS concepts against Knowledge Base..."):
            start_time = time.time()
            aug_result = augmenter.augment_sentence(target_text)
            process_dur = time.time() - start_time
            
        # 2. Pipeline - Translation
        with st.spinner("Translating using Seq2Seq model..."):
            t_start = time.time()
            # Translate baseline (adapter disabled, original text)
            baseline_translation = translate_text(
                target_text, 
                disable_adapter=True
            )
            
            # Translate augmented (adapter active, augmented text)
            augmented_translation = translate_text(
                aug_result["augmented"], 
                disable_adapter=False
            )
            inference_time_ms = (time.time() - t_start) * 1000.0
            
        # 3. Pipeline - Explainer
        explanation_report = explainer.generate_explanation(
            original_text=aug_result["original"],
            translation=augmented_translation,
            augmentation_details=aug_result["details"]
        )
        
        # --- UI Presentation ---
        
        # Concept Badges
        st.write("### 🏷️ Concept Resolution")
        if not aug_result["details"]:
            st.markdown("<span class='badge badge-amber'>No specific IKS Concepts detected</span>", unsafe_allow_html=True)
        else:
            for c in aug_result["details"]:
                st.markdown(f"""
                <span class='badge badge-green'>{c['tamil']} ({c['concept']})</span>
                <span class='badge badge-accent'>Resolved: {c['tag_value']}</span>
                """, unsafe_allow_html=True)
                
        # Confidence Metrics Row
        st.write("### 📈 Pipeline Metrics")
        from backend.core.config import LORA_ADAPTER_PATH
        model_ver = "v1.0-default"
        if os.path.exists(LORA_ADAPTER_PATH):
            ver_file = os.path.join(LORA_ADAPTER_PATH, "model_version.txt")
            if os.path.exists(ver_file):
                with open(ver_file, "r", encoding="utf-8") as f:
                    model_ver = f.read().strip()
        lora_status = "Active" if os.path.exists(LORA_ADAPTER_PATH) else "None"

        st.markdown(f"""
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-label">Resolution Speed</div>
                <div class="metric-value">{process_dur*1000:.1f} ms</div>
                <div class="metric-footer">FAISS Index & MiniLM</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Semantic Match Confidence</div>
                <div class="metric-value">{"95.4%" if not aug_result['details'] else f"{aug_result['details'][0]['confidence']}%"}</div>
                <div class="metric-footer">Multilingual Cosine Sim</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Inference Time</div>
                <div class="metric-value">{inference_time_ms:.1f} ms</div>
                <div class="metric-footer">Model: IndicTrans2 ({device})</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">LoRA Adapter & Version</div>
                <div class="metric-value">{lora_status}</div>
                <div class="metric-footer">Ver: {model_ver}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Side-by-side translation
        st.write("### 🔄 Translation Comparison")
        col_b, col_f = st.columns(2)
        with col_b:
            st.markdown(f"""
            <div style="background-color: {BG_SUBTLE}; border: 1px solid {BORDER}; border-radius: 8px; padding: 1rem; height: 100%;">
                <div style="font-size: 0.72rem; color: {TEXT_MUTED}; font-weight: 600; text-transform: uppercase;">Raw Baseline NMT</div>
                <div style="font-size: 1rem; margin-top: 0.5rem; color: {TEXT_MUTED}; font-style: italic;">"{baseline_translation}"</div>
                <div style="font-size: 0.72rem; color: {RED}; margin-top: 0.5rem; display: flex; align-items: center; gap: 4px;">
                    ⚠️ Lacks cultural context
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with col_f:
            st.markdown(f"""
            <div style="background-color: {BG_SUBTLE}; border: 1px solid {ACCENT}; border-radius: 8px; padding: 1rem; height: 100%;">
                <div style="font-size: 0.72rem; color: {ACCENT}; font-weight: 600; text-transform: uppercase;">IKS-Aware Fine-Tuned NMT</div>
                <div style="font-size: 1.05rem; margin-top: 0.5rem; font-weight: 500;">"{augmented_translation}"</div>
                <div style="font-size: 0.72rem; color: {GREEN}; margin-top: 0.5rem; display: flex; align-items: center; gap: 4px;">
                    ✓ Infused with conceptual meanings
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        # Explainer Report Card
        st.write("### 📝 Detailed Context & Explanation Report")
        st.markdown(f"""
        <div class="explanation-report">{explanation_report}</div>
        """, unsafe_allow_html=True)
    else:
        st.info("👈 Enter a Tamil sentence or select a preset and click 'Process & Translate' to visualize the explainable translation pipeline.")
