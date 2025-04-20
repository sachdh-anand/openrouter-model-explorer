import os
import json
import pandas as pd
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv, set_key, find_dotenv
from main import (
    fetch_all_models,
    extract_specialties,
    calculate_effectiveness,
    extract_params,
    format_release_date,
    is_free_or_preview,
)
try:
    from streamlit_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
    AGGRID_AVAILABLE = True
except ImportError:
    AGGRID_AVAILABLE = False

# Load environment
load_dotenv()

# Version (keep in sync with pyproject.toml)
__version__ = "0.1.0"

# Initialize session state variables
if "model_data" not in st.session_state:
    st.session_state.model_data = []
if "selected_models" not in st.session_state:
    st.session_state.selected_models = []

# Page configuration
st.set_page_config(
    page_title="OpenRouter Model Explorer",
    page_icon="🤖",
    layout="wide",
)

# ---- Minimal CSS for header and cards ----
st.markdown(
    """
    <style>
    .header-container { display: flex; align-items: center; margin-bottom: 1rem; }
    .header-logo { font-size: 2rem; margin-right: 0.5rem; }
    .header-title { font-size: 2rem; font-weight: bold; }
    .metric-card { background-color: #2e3136; border-radius: 8px; padding: 1rem; text-align: center; }
    .metric-label { font-size: 0.85rem; color: #cccccc; }
    .metric-value { font-size: 1.5rem; font-weight: bold; color: #ffffff; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---- Sidebar ----
with st.sidebar:
    st.header("🔑 API Key")
    existing_key = os.getenv("OPENROUTER_API_KEY", "")
    
    # Initialize widget key in session state
    if "api_key_input" not in st.session_state:
        st.session_state.api_key_input = existing_key
    
    api_key = st.text_input(
        "OpenRouter API Key",
        value=st.session_state.api_key_input,
        type="password",
        key="api_key_input",
        help="Get your key from https://openrouter.ai/keys",
    )
    if st.button("Save API Key"):
        dotenv_path = find_dotenv()
        if not dotenv_path:
            # Create .env file if it doesn't exist
            dotenv_path = ".env"
            with open(dotenv_path, "w") as f:
                pass
        set_key(dotenv_path, "OPENROUTER_API_KEY", api_key)
        os.environ["OPENROUTER_API_KEY"] = api_key
        st.success("API key saved!")

    st.markdown("---")
    st.header("🔍 Filters")
    
    # Initialize filter state variables
    if "min_score" not in st.session_state:
        st.session_state.min_score = 8.5
    if "capabilities" not in st.session_state:
        st.session_state.capabilities = ["Code", "Reason", "Tools"]
    if "search" not in st.session_state:
        st.session_state.search = ""
        
    min_score = st.slider("Minimum Effectiveness Score", 0.0, 10.0, st.session_state.min_score, 0.1, key="min_score_slider")
    capabilities = st.multiselect(
        "Capabilities",
        ["Code", "Reason", "Tools"],
        default=st.session_state.capabilities,
        key="capabilities_select"
    )
    search = st.text_input("Search models", value=st.session_state.search, key="search_input")

    st.markdown("---")
    st.header("📋 Legend")
    st.markdown(
        "**Code:** 🖥️  • **Reason:** 🤔  • **Tools:** 🔧",
    )

    st.header("ℹ️ About")
    st.markdown(f"Version: {__version__}")
    st.markdown("[GitHub Repo](https://github.com/yourusername/openrouter_models)")

# ---- Main Content ----
col1, col2 = st.columns([4, 1])
with col1:
    st.markdown(
        "<div class='header-container'><div class='header-logo'>🤖</div>"
        "<div class='header-title'>OpenRouter Model Explorer</div></div>",
        unsafe_allow_html=True,
    )
with col2:
    refresh = st.button("🔄 Refresh", key="refresh_button")

# Fetch & cache models
if refresh or len(st.session_state.model_data) == 0:
    with st.spinner("Loading models..."):
        st.session_state.model_data = fetch_all_models()
models = st.session_state.model_data

# Compute key subsets
free_models = [m for m in models if is_free_or_preview(m)]
relevant_models = [
    m
    for m in free_models
    if any(
        s in extract_specialties(m.get("description", ""), m.get("architecture", {}))
        for s in ["coding", "reasoning", "tool_calling"]
    )
]

# Metrics cards
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(
        f"<div class='metric-card'><div class='metric-label'>Total Models</div>"
        f"<div class='metric-value'>{len(models)}</div></div>",
        unsafe_allow_html=True,
    )
with col2:
    st.markdown(
        f"<div class='metric-card'><div class='metric-label'>Free & Preview</div>"
        f"<div class='metric-value'>{len(free_models)}</div></div>",
        unsafe_allow_html=True,
    )
with col3:
    st.markdown(
        f"<div class='metric-card'><div class='metric-label'>Relevant Capabilities</div>"
        f"<div class='metric-value'>{len(relevant_models)}</div></div>",
        unsafe_allow_html=True,
    )
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Build DataFrame
def make_dataframe(models):
    rows = []
    for model in models:
        if not is_free_or_preview(model):
            continue
        specs = extract_specialties(model.get("description", ""), model.get("architecture", {}))
        caps = []
        if "coding" in specs:
            caps.append("🖥️ Code")
        if "reasoning" in specs:
            caps.append("🤔 Reason")
        if "tool_calling" in specs:
            caps.append("🔧 Tools")
        rows.append(
            {
                "Provider": (model.get("id", "").split("/")[0] or "").capitalize(),
                "Name": model.get("name", ""),
                "Model ID": model.get("id", ""),
                "Params": f"{extract_params(model.get('name',''), model.get('description','')) or 'N/A'}",
                "Score": round(calculate_effectiveness(model), 1),
                "Release": format_release_date(model.get("created")),
                "Capabilities": " • ".join(caps),
            }
        )
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("Score", ascending=False).reset_index(drop=True)
    return df

df = make_dataframe(models)

# Apply sidebar filters
filtered_df = df.copy()
if not filtered_df.empty:
    filtered_df = filtered_df[filtered_df["Score"] >= min_score]
    # Capability filter
    if capabilities:
        mask = pd.Series(False, index=filtered_df.index)
        for cap in capabilities:
            key = {
                "Code": "Code",
                "Reason": "Reason",
                "Tools": "Tools",
            }[cap]
            mask |= filtered_df["Capabilities"].str.contains(key)
        filtered_df = filtered_df[mask]
    # Search filter
    if search:
        s = search.lower()
        filtered_df = filtered_df[
            filtered_df["Name"].str.lower().str.contains(s)
            | filtered_df["Model ID"].str.lower().str.contains(s)
            | filtered_df["Provider"].str.lower().str.contains(s)
        ]

# ---- Export filtered results to sidebar ----
if not filtered_df.empty:
    csv_data = filtered_df.to_csv(index=False)
    st.sidebar.download_button("Download CSV", csv_data, "models.csv", "text/csv")
    json_data = filtered_df.to_json(orient="records")
    st.sidebar.download_button("Download JSON", json_data, "models.json", "application/json")

# Provider distribution chart
st.subheader("Provider Distribution")
if not filtered_df.empty:
    pd_counts = filtered_df["Provider"].value_counts().rename_axis("Provider").reset_index(name="Count")
    st.bar_chart(data=pd_counts.set_index("Provider"))
else:
    st.write("No models to display.")

# Interactive Models Table
st.subheader("Available Models")
if not filtered_df.empty:
    if AGGRID_AVAILABLE:
        gb = GridOptionsBuilder.from_dataframe(filtered_df)
        gb.configure_selection("multiple", use_checkbox=True)
        gb.configure_pagination(paginationAutoPageSize=True)
        gb.configure_default_column(filterable=True, sortable=True, resizable=True)
        grid_opts = gb.build()
        grid_resp = AgGrid(
            filtered_df,
            gridOptions=grid_opts,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            theme="streamlit",
            fit_columns_on_grid_load=True,
        )
        selected = [r.get("Model ID") for r in grid_resp.get("selected_rows", [])]
        st.session_state["selected_models"] = selected
    else:
        # Fallback without AgGrid
        df_sel = filtered_df.copy()
        if "Select" not in df_sel.columns:
            df_sel.insert(0, "Select", False)
        edited = st.data_editor(
            df_sel,
            column_config={
                "Select": st.column_config.CheckboxColumn("Select", width="small"),
            },
            hide_index=True,
            use_container_width=True,
            key="fallback_table",
        )
        try:
            selected = edited[edited["Select"] == True]["Model ID"].tolist()
            st.session_state["selected_models"] = selected
        except Exception:
            pass
else:
    st.info("No models match the filters.")

# Display selected models in .env format
sel = st.session_state.get("selected_models", [])
if sel:
    env_txt = "\n".join([f"OPENROUTER_MODEL_{i+1}={m}" for i, m in enumerate(sel)])
    st.subheader("Selected Models (.env)")
    st.code(env_txt, language="bash")
    st.download_button("Download .env", env_txt, "models.env", "text/plain")