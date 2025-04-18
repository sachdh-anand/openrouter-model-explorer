import os
import sys
import requests
import re
from typing import Dict, List, Optional
from datetime import datetime

API_URL = "https://openrouter.ai/api/v1/models"
API_KEY = os.getenv("OPENROUTER_API_KEY")

def extract_params(name: str, description: str) -> Optional[float]:
    """Extract parameter count in billions from model name or description."""
    # Common patterns: 7B, 7b, 7-b, 7 billion, etc.
    patterns = [
        r'(\d+\.?\d*)[-\s]?[bB](?!\w)',  # matches 7B, 7-b, 7 b
        r'(\d+\.?\d*)\s*billion',  # matches 7 billion
    ]
    
    for pattern in patterns:
        for text in [name, description]:
            if match := re.search(pattern, text):
                return float(match.group(1))
    return None

def extract_specialties(description: str, architecture: Dict) -> List[str]:
    """Extract key specialties from model description and architecture."""
    specialties = []
    
    # Define specialty keywords and their categories
    specialty_map = {
        'coding': ['code', 'programming', 'development', 'coder', 'developer'],
        'reasoning': ['reason', 'logic', 'analytical', 'thinking', 'problem solving'],
        'tool_calling': ['tool', 'function call', 'json', 'api', 'tool use', 'tool-use'],
    }
    
    # Check description for keywords
    for category, keywords in specialty_map.items():
        if any(keyword.lower() in description.lower() for keyword in keywords):
            specialties.append(category)
    
    # Check architecture for tool/function calling support
    if architecture.get('instruct_type') in ['deepseek-r1', 'function-calling'] or \
       'tool' in str(architecture).lower() or \
       'function' in str(architecture).lower():
        if 'tool_calling' not in specialties:
            specialties.append('tool_calling')
    
    return specialties

def calculate_effectiveness(model: Dict) -> float:
    """Calculate a rough effectiveness score (0-10) based on various factors."""
    score = 5.0
    
    # Context length bonus
    context_length = model.get('context_length', 0)
    if context_length > 32768:  # 32k
        score += 1
    elif context_length > 16384:  # 16k
        score += 0.5
    
    # Architecture and capabilities bonus
    architecture = model.get('architecture', {})
    
    # Tool/function calling support
    if architecture.get('instruct_type') in ['deepseek-r1', 'function-calling'] or \
       'tool' in str(architecture).lower() or \
       'function' in str(architecture).lower():
        score += 1
    
    # Preview models bonus
    if 'preview' in model.get('id', '').lower():
        score += 0.5
    
    # Size bonus
    params = extract_params(model.get('name', ''), model.get('description', ''))
    if params:
        if params >= 70:
            score += 1.5
        elif params >= 30:
            score += 1
        elif params >= 7:
            score += 0.5
    
    # Specialty bonus
    specialties = extract_specialties(model.get('description', ''), model.get('architecture', {}))
    if 'coding' in specialties and 'reasoning' in specialties:
        score += 1
    if 'tool_calling' in specialties:
        score += 1
    
    return min(10, max(0, score))

def format_release_date(created: int) -> str:
    """Format Unix timestamp to readable date."""
    try:
        return datetime.fromtimestamp(created).strftime('%Y-%m-%d')
    except (TypeError, ValueError):
        return 'N/A'

def is_free_or_preview(model: Dict) -> bool:
    """Check if model is free or preview version."""
    model_id = model.get('id', '').lower()
    model_name = model.get('name', '').lower()
    
    # Check for preview in id or name
    is_preview = 'preview' in model_id or 'preview' in model_name
    
    # Check for free in id
    is_free = ':free' in model_id
    
    # Check if all pricing is zero
    pricing = model.get('pricing', {})
    is_zero_price = all(float(price) == 0 for price in pricing.values() if price is not None)
    
    return is_preview or is_free or is_zero_price

def format_model_info(models: List[Dict]) -> str:
    """Format model information into a table string."""
    # Filter for free and preview models only
    filtered_models = [m for m in models if is_free_or_preview(m)]
    
    # Sort models by effectiveness score
    models_with_scores = [(m, calculate_effectiveness(m)) for m in filtered_models]
    sorted_models = sorted(models_with_scores, key=lambda x: x[1], reverse=True)
    
    # Column widths
    col_widths = {
        'name': 40,
        'id': 45,
        'params': 10,
        'score': 8,
        'date': 12,
        'capabilities': 40
    }
    
    # Prepare table header
    header = (
        f"{'Model Name':{col_widths['name']}} "
        f"{'Model ID':{col_widths['id']}} "
        f"{'Params':{col_widths['params']}} "
        f"{'Score':{col_widths['score']}} "
        f"{'Released':{col_widths['date']}} "
        f"{'Capabilities':{col_widths['capabilities']}}"
    )
    
    # Calculate total width for separator
    total_width = sum(col_widths.values()) + 5  # +5 for spaces between columns
    separator = "-" * total_width
    
    rows = [header, separator]
    
    for model, score in sorted_models:
        # Only include models with relevant capabilities
        specialties = extract_specialties(model.get('description', ''), model.get('architecture', {}))
        if not any(s in specialties for s in ['coding', 'reasoning', 'tool_calling']):
            continue
            
        # Format each column with proper truncation
        name = model.get('name', 'Unknown')
        if len(name) > col_widths['name']:
            name = name[:col_widths['name']-3] + "..."
            
        model_id = model.get('id', 'N/A')
        if len(model_id) > col_widths['id']:
            model_id = model_id[:col_widths['id']-3] + "..."
            
        params = extract_params(model.get('name', ''), model.get('description', ''))
        params_str = f"{params}B" if params else "N/A"
        
        # Build capabilities string
        capabilities = []
        if 'coding' in specialties:
            capabilities.append('🖥️ Code')
        if 'reasoning' in specialties:
            capabilities.append('🤔 Reason')
        if 'tool_calling' in specialties:
            capabilities.append('🔧 Tools')
        capabilities_str = ' + '.join(capabilities)
        
        release_date = format_release_date(model.get('created', None))
        
        # Format row with fixed widths
        row = (
            f"{name:{col_widths['name']}} "
            f"{model_id:{col_widths['id']}} "
            f"{params_str:{col_widths['params']}} "
            f"{score:{col_widths['score']}.1f} "
            f"{release_date:{col_widths['date']}} "
            f"{capabilities_str:{col_widths['capabilities']}}"
        )
        rows.append(row)
    
    return "\n".join(rows)

def fetch_all_models():
    headers = {"Authorization": f"Bearer {API_KEY}"}
    resp = requests.get(API_URL, headers=headers)
    resp.raise_for_status()
    return resp.json().get("data", [])

def main():
    if not API_KEY:
        sys.stderr.write("⚠️ Please set OPENROUTER_API_KEY\n")
        sys.exit(1)

    all_models = fetch_all_models()
    free_and_preview = [m for m in all_models if is_free_or_preview(m)]
    
    # Count models with relevant capabilities
    relevant_models = []
    for model in free_and_preview:
        specialties = extract_specialties(model.get('description', ''), model.get('architecture', {}))
        if any(s in specialties for s in ['coding', 'reasoning', 'tool_calling']):
            relevant_models.append(model)
    
    print(f"Total models available: {len(all_models)}")
    print(f"Free & Preview models: {len(free_and_preview)}")
    print(f"Models with coding/reasoning/tool capabilities: {len(relevant_models)}\n")
    
    print("Model Analysis (Free & Preview Models with Coding/Reasoning/Tool Capabilities):")
    print(format_model_info(all_models))
    
    print("\nLegend:")
    print("- Score: 0-10 scale based on context length, capabilities, and model size")
    print("- Params: Model size in billions of parameters")
    print("- Released: Date when the model was made available")
    print("- Capabilities: 🖥️ Code = Coding, 🤔 Reason = Reasoning, 🔧 Tools = Tool/Function calling")

if __name__ == "__main__":
    main()
