import streamlit as st
import pandas as pd
from main import fetch_all_models, extract_specialties, calculate_effectiveness, extract_params, format_release_date, is_free_or_preview
import os
from datetime import datetime

# Page config
st.set_page_config(
    page_title="OpenRouter Model Explorer",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS for professional appearance
st.markdown("""
<style>
    /* Global styles */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    div[data-testid="stExpander"] {
        display: none;
    }
    div[data-testid="stExpander"] + div {
        display: none;
    }
    
    /* Header */
    .header-container {
        display: flex;
        align-items: center;
        margin-bottom: 1rem;
        border-bottom: 1px solid rgba(250, 250, 250, 0.2);
        padding-bottom: 1rem;
    }
    .header-logo {
        font-size: 1.25rem;
        margin-right: 0.5rem;
    }
    .header-title {
        font-size: 1.5rem;
        font-weight: 600;
        margin: 0;
    }
    
    /* Cards */
    .metric-card {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        padding: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 1rem;
    }
    .metric-label {
        font-size: 0.85rem;
        color: rgba(250, 250, 250, 0.7);
        margin-bottom: 0.25rem;
    }
    .metric-value {
        font-size: 1.5rem;
        font-weight: 600;
    }
    
    /* Section styling */
    .section-header {
        font-size: 1rem;
        font-weight: 600;
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
    }
    .section-header::before {
        content: "";
        display: block;
        width: 3px;
        height: 1rem;
        background: linear-gradient(to bottom, #4d78ef, #11c5bf);
        margin-right: 0.5rem;
        border-radius: 3px;
    }
    
    /* Table styling */
    .stDataEditor td {
        font-size: 0.85rem !important;
        padding: 0.35rem 0.5rem !important;
        color: rgba(250, 250, 250, 0.9) !important;
    }
    .stDataEditor th {
        font-size: 0.85rem !important;
        padding: 0.5rem 0.5rem !important;
        font-weight: 600 !important;
        background-color: rgba(255, 255, 255, 0.05) !important;
        color: rgba(250, 250, 250, 0.9) !important;
    }
    .stDataEditor [data-testid="column-header-name"] {
        justify-content: center !important;
    }
    
    /* Filter container */
    .filter-container {
        background-color: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1.25rem;
    }
    
    /* Hide empty elements */
    [data-testid="stVerticalBlock"] > div:empty {
        display: none !important;
    }
    .empty-section {
        display: none !important;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(to right, #4d78ef, #11c5bf);
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        font-weight: 500;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
    }
    
    /* Legend */
    .legend-container {
        background-color: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        padding: 1rem;
        margin-top: 1rem;
        font-size: 0.85rem;
    }
    .legend-item {
        display: flex;
        align-items: center;
        margin-bottom: 0.5rem;
    }
    .legend-icon {
        margin-right: 0.5rem;
        font-size: 1rem;
    }
    
    /* Code block */
    .env-container {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        padding: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        font-family: monospace;
        position: relative;
        margin-top: 1rem;
    }
    
    /* Slider */
    .stSlider [data-baseweb="slider"] {
        margin-top: 0.5rem !important;
    }
    
    /* Mobile adjustments */
    @media (max-width: 768px) {
        .metric-card {
            padding: 0.75rem;
        }
        .metric-value {
            font-size: 1.25rem;
        }
    }
</style>
""", unsafe_allow_html=True)

def extract_provider(model_id: str) -> str:
    """Extract the provider/company name from model ID."""
    if not model_id or '/' not in model_id:
        return "Unknown"
    
    provider = model_id.split('/')[0]
    
    # Capitalize provider names for better display
    provider_map = {
        "anthropic": "Anthropic",
        "google": "Google",
        "mistralai": "Mistral AI",
        "meta": "Meta",
        "openai": "OpenAI",
        "meta-llama": "Meta",
        "cohere": "Cohere",
        "perplexity": "Perplexity AI",
        "claude": "Anthropic",
        "fireworks": "Fireworks AI",
        "deepseek": "DeepSeek",
        "01-ai": "01 AI",
        "azure": "Microsoft Azure",
        "gpt4all": "GPT4All",
        "neuroengine": "Neuroengine",
        "huggingface": "Hugging Face",
        "together": "Together AI",
        "databricks": "Databricks",
        "deepinfra": "DeepInfra",
        "groq": "Groq",
        "nvidia": "NVIDIA",
        "inflection": "Inflection AI",
        "amazon": "Amazon",
        "apple": "Apple",
        "mancer": "Mancer",
        "undi95": "Undi95",
        "openchat": "OpenChat"
    }
    
    # Try to find provider in our map, or just capitalize first letter
    return provider_map.get(provider.lower(), provider.capitalize())

def create_dataframe(models):
    """Convert models data to a pandas DataFrame with formatted capabilities."""
    rows = []
    for model in models:
        if not is_free_or_preview(model):
            continue
            
        specialties = extract_specialties(model.get('description', ''), model.get('architecture', {}))
        if not any(s in specialties for s in ['coding', 'reasoning', 'tool_calling']):
            continue
        
        model_id = model.get('id', 'N/A')
        provider = extract_provider(model_id)
            
        capabilities = []
        if 'coding' in specialties:
            capabilities.append('🖥️ Code')
        if 'reasoning' in specialties:
            capabilities.append('🤔 Reason')
        if 'tool_calling' in specialties:
            capabilities.append('🔧 Tools')
            
        row = {
            'Provider': provider,
            'Model Name': model.get('name', 'Unknown'),
            'Model ID': model_id,
            'Parameters': f"{extract_params(model.get('name', ''), model.get('description', ''))}B" if extract_params(model.get('name', ''), model.get('description', '')) else "N/A",
            'Effectiveness Score': round(calculate_effectiveness(model), 1),
            'Release Date': format_release_date(model.get('created', None)),
            'Capabilities': ' • '.join(capabilities)
        }
        rows.append(row)
    
    # Create DataFrame and sort by effectiveness score
    df = pd.DataFrame(rows).sort_values('Effectiveness Score', ascending=False)
    
    # Add sequential numbering after sorting
    df.insert(0, '#', range(1, len(df) + 1))
    
    return df

def main():
    # Initialize session state early to prevent errors
    if 'selected_models' not in st.session_state:
        st.session_state.selected_models = set()
    
    # Header with logo
    st.markdown("""
    <div class="header-container">
        <div class="header-logo">🤖</div>
        <h1 class="header-title">OpenRouter Model Explorer</h1>
    </div>
    <p>Discover and compare free & preview AI models with coding, reasoning, and tool capabilities.</p>
    """, unsafe_allow_html=True)
    
    # API Key Management
    st.markdown('<div class="section-header">API Key</div>', unsafe_allow_html=True)
    
    # Check if API key exists in environment
    existing_api_key = os.getenv("OPENROUTER_API_KEY")
    
    # Create columns for API key input and save button
    api_key_cols = st.columns([3, 1])
    
    with api_key_cols[0]:
        if existing_api_key:
            # Show masked key if it exists
            masked_key = f"{existing_api_key[:5]}{'*' * 10}{existing_api_key[-4:]}"
            api_key_input = st.text_input(
                "OpenRouter API Key (saved)",
                value=masked_key,
                type="password",
                help="Enter a new key to update",
                key="api_key_input"
            )
            
            # Check if user entered a new key (not the masked one)
            if api_key_input != masked_key:
                api_key = api_key_input
                show_save_button = len(api_key) > 20  # Show save button only if key looks valid
            else:
                api_key = existing_api_key
                show_save_button = False
        else:
            # No existing key, prompt for one
            api_key = st.text_input(
                "Enter OpenRouter API Key",
                type="password",
                help="Get your key from openrouter.ai/keys",
                key="api_key_input"
            )
            show_save_button = len(api_key) > 20  # Show save button only if key looks valid
    
    with api_key_cols[1]:
        if show_save_button:
            if st.button("Save", key="save_api_key", use_container_width=True):
                try:
                    # Write to .env file
                    with open(".env", "w") as f:
                        f.write(f"OPENROUTER_API_KEY={api_key}\n")
                    
                    # Also set in current environment
                    os.environ["OPENROUTER_API_KEY"] = api_key
                    
                    # Set API_KEY in main module
                    import main
                    main.API_KEY = api_key
                    
                    st.success("✅ API key saved")
                    st.rerun()  # Refresh the app to use the new key
                except Exception as e:
                    st.error(f"Error saving API key: {str(e)}")
    
    if not api_key:
        st.warning("⚠️ Please enter your OpenRouter API key to continue")
        st.markdown("""
        <div style="margin-top: 1rem;">
            <p>Get your API key from <a href="https://openrouter.ai/keys" target="_blank">openrouter.ai/keys</a></p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Set API_KEY in main module to ensure it's available for API calls
    import main
    main.API_KEY = api_key
        
    # Refresh Button in a prominent position
    refresh_col1, refresh_col2, refresh_col3 = st.columns([2,1,2])
    with refresh_col2:
        refresh = st.button("🔄 Refresh Models", use_container_width=True)
    
    if refresh or 'model_data' not in st.session_state:
        with st.spinner("Fetching latest model data..."):
            try:
                all_models = fetch_all_models()
                st.session_state.model_data = all_models
                st.session_state.last_update = datetime.now()
            except Exception as e:
                st.error(f"Error fetching models: {str(e)}")
                return
    
    # Model Statistics in visually appealing cards
    all_models = st.session_state.model_data
    free_and_preview = [m for m in all_models if is_free_or_preview(m)]
    relevant_models = [m for m in free_and_preview if any(s in extract_specialties(m.get('description', ''), m.get('architecture', {})) 
                                                        for s in ['coding', 'reasoning', 'tool_calling'])]
    
    stats_col1, stats_col2, stats_col3 = st.columns(3)
    with stats_col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Models</div>
            <div class="metric-value">{len(all_models)}</div>
        </div>
        """, unsafe_allow_html=True)
    with stats_col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Free & Preview Models</div>
            <div class="metric-value">{len(free_and_preview)}</div>
        </div>
        """, unsafe_allow_html=True)
    with stats_col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Models with Special Capabilities</div>
            <div class="metric-value">{len(relevant_models)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Last Update Time
    st.caption(f"Last updated: {st.session_state.last_update.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Create dataframe
    df = create_dataframe(all_models)
    
    # Filters section with better visual containment - directly embedded in page
    st.markdown('<div class="section-header">Filters</div>', unsafe_allow_html=True)
    
    # Apply filters directly without container
    filter_cols = st.columns(3)
    
    with filter_cols[0]:
        min_score = st.slider("Minimum Effectiveness Score", 0.0, 10.0, 8.5, 0.1)
    
    with filter_cols[1]:
        capabilities = st.multiselect(
            "Filter by Capabilities",
            ["Code", "Reason", "Tools"],
            default=["Code", "Reason", "Tools"]
        )
    
    with filter_cols[2]:
        search = st.text_input("🔍 Search Models", "")
    
    # Apply filters
    filtered_df = df[df['Effectiveness Score'] >= min_score]
    
    if capabilities:
        filter_conditions = []
        for cap in capabilities:
            if cap == "Code":
                filter_conditions.append(filtered_df['Capabilities'].str.contains('Code'))
            elif cap == "Reason":
                filter_conditions.append(filtered_df['Capabilities'].str.contains('Reason'))
            elif cap == "Tools":
                filter_conditions.append(filtered_df['Capabilities'].str.contains('Tools'))
        
        if filter_conditions:
            combined_filter = filter_conditions[0]
            for condition in filter_conditions[1:]:
                combined_filter = combined_filter | condition
            filtered_df = filtered_df[combined_filter]
    
    if search:
        search_filter = (
            filtered_df['Model Name'].str.contains(search, case=False) |
            filtered_df['Model ID'].str.contains(search, case=False) |
            filtered_df['Provider'].str.contains(search, case=False)
        )
        filtered_df = filtered_df[search_filter]
    
    # Display table with a proper header
    st.markdown('<div class="section-header">Available Models</div>', unsafe_allow_html=True)
    
    # Add selection column
    if 'selection' not in filtered_df.columns:
        filtered_df['Select'] = False
    
    # Display interactive dataframe
    edited_df = st.data_editor(
        filtered_df,
        column_config={
            "Select": st.column_config.CheckboxColumn(
                "Select",
                help="Select model",
                default=False,
                width="small",
            ),
            "#": st.column_config.NumberColumn(
                "#",
                help="Sequential number",
                width="small",
            ),
            "Provider": st.column_config.TextColumn(
                "Provider",
                help="Company or organization that created the model",
                width="small",
            ),
            "Model Name": st.column_config.TextColumn(
                "Model Name",
                width="medium",
            ),
            "Model ID": st.column_config.TextColumn(
                "Model ID",
                width="medium",
            ),
            "Parameters": st.column_config.TextColumn(
                "Parameters",
                width="small",
            ),
            "Effectiveness Score": st.column_config.NumberColumn(
                "Effectiveness Score",
                format="%.1f",
                width="small",
            ),
            "Release Date": st.column_config.TextColumn(
                "Release Date",
                width="small",
            ),
            "Capabilities": st.column_config.TextColumn(
                "Capabilities",
                width="medium",
            ),
        },
        hide_index=True,
        height=400,
        use_container_width=True,
        key="model_table"
    )
    
    # Handle model selection from data editor
    try:
        # Get the response from the data editor
        grid_response = st.session_state.get('model_table', {})
        
        # Initialize or maintain selected_models if needed
        if "selected_models" not in st.session_state:
            st.session_state.selected_models = set()
            
        # Check if we have selected_rows in the response
        selected_rows = None
        if grid_response and isinstance(grid_response, dict):
            selected_rows = grid_response.get('selected_rows', None)
            
        # Update selection if we have valid selected_rows
        if selected_rows is not None and isinstance(selected_rows, list):
            st.session_state.selected_models = {row.get('Model ID', '') for row in selected_rows if isinstance(row, dict)}
        
        # Alternative selection method using the edited dataframe
        if edited_df is not None:
            try:
                if 'Select' in edited_df.columns:
                    selected_models = edited_df[edited_df['Select'] == True]['Model ID'].tolist()
                    if selected_models:
                        st.session_state.selected_models = set(selected_models)
            except Exception as e:
                st.warning(f"Could not update selection from dataframe: {str(e)}")
                
    except Exception as e:
        st.error(f"Error handling selection: {str(e)}")
        # Keep existing selection if there was an error
        pass
    
    # Display selected models in .env format with styling
    if st.session_state.selected_models:
        display_env_format(st.session_state.selected_models)
    
    # Enhanced Legend with icons
    st.markdown('<div class="section-header">Legend</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="legend-container">
        <div class="legend-item">
            <span class="legend-icon">🏢</span>
            <strong>Provider:</strong> Company or organization that created the model
        </div>
        <div class="legend-item">
            <span class="legend-icon">📊</span>
            <strong>Effectiveness Score:</strong> 0-10 scale based on context length, capabilities, and model size
        </div>
        <div class="legend-item">
            <span class="legend-icon">📏</span>
            <strong>Parameters:</strong> Model size in billions of parameters
        </div>
        <div class="legend-item">
            <span class="legend-icon">🔍</span>
            <strong>Capabilities:</strong>
        </div>
        <div style="margin-left: 1.5rem; margin-top: 0.5rem;">
            <div class="legend-item">
                <span class="legend-icon">🖥️</span>
                <strong>Code:</strong> Specialized in coding tasks
            </div>
            <div class="legend-item">
                <span class="legend-icon">🤔</span>
                <strong>Reason:</strong> Strong reasoning capabilities
            </div>
            <div class="legend-item">
                <span class="legend-icon">🔧</span>
                <strong>Tools:</strong> Supports tool/function calling
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def display_env_format(selected_models):
    if not selected_models:
        return
        
    env_content = "\n".join([f"OPENROUTER_MODEL_{i+1}={model_id}" for i, model_id in enumerate(selected_models)])
    
    st.subheader("Selected Models in .env Format")
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.code(env_content, language="bash")
    
    with col2:
        if st.button("Copy", key="copy_button"):
            # Use JavaScript to copy to clipboard
            js = f"""
            <script>
                const text = `{env_content}`;
                navigator.clipboard.writeText(text)
                    .then(() => {{
                        window.parent.postMessage({{
                            type: "streamlit:setComponentValue",
                            value: true
                        }}, "*");
                    }})
                    .catch(err => {{
                        console.error('Failed to copy: ', err);
                    }});
            </script>
            """
            
            st.markdown(js, unsafe_allow_html=True)
            st.toast("Copied to clipboard!", icon="✅")

if __name__ == "__main__":
    main() 