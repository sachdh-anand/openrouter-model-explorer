import os
import json
from dotenv import load_dotenv
import json
import requests
import re
from typing import Dict, List, Optional
from datetime import datetime

# Load environment variables
load_dotenv()
API_URL = "https://openrouter.ai/api/v1/models"
API_KEY = os.getenv("OPENROUTER_API_KEY")
# Load heuristics configuration
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config", "heuristics.json")
with open(CONFIG_PATH, "r") as _f:
    CONFIG = json.load(_f)

def extract_params(name: str, description: str) -> Optional[float]:
    """Extract parameter count in billions from model name or description."""
    # Extract based on configured regex patterns
    patterns = CONFIG.get("extract_params", {}).get("patterns", [])
    for pattern in patterns:
        for text in (name or "", description or ""):
            if match := re.search(pattern, text):
                try:
                    return float(match.group(1))
                except (ValueError, TypeError):
                    continue
    return None

def extract_specialties(description: str, architecture: Dict) -> List[str]:
    """Extract key specialties from model description and architecture."""
    specialties = []
    spec_cfg = CONFIG.get("specialties", {})
    text = (description or "").lower()
    arch_str = str(architecture or {}).lower()
    # Check keywords per specialty
    for category, cfg in spec_cfg.items():
        for kw in cfg.get("keywords", []):
            if kw.lower() in text:
                specialties.append(category)
                break
    # Additionally detect tool_calling via architecture config
    tool_cfg = spec_cfg.get("tool_calling", {})
    # Instruct types support
    for inst in tool_cfg.get("instruct_types", []):
        if architecture.get("instruct_type") == inst:
            if "tool_calling" not in specialties:
                specialties.append("tool_calling")
            break
    # Architecture keywords support
    for arch_kw in tool_cfg.get("architecture_keywords", []):
        if arch_kw.lower() in arch_str:
            if "tool_calling" not in specialties:
                specialties.append("tool_calling")
            break
    return specialties

def calculate_effectiveness(model: Dict) -> float:
    """Calculate a rough effectiveness score (0-10) based on various factors."""
    eff_cfg = CONFIG.get("effectiveness", {})
    score = eff_cfg.get("base_score", 0.0)
    # Context length bonuses
    ctx = model.get("context_length", 0)
    for th in eff_cfg.get("context_length", []):
        if ctx > th.get("min", 0):
            score += th.get("bonus", 0.0)
            break
    # Architecture support bonus
    arch_cfg = eff_cfg.get("architecture", {})
    arch = model.get("architecture", {})
    added = False
    for inst in arch_cfg.get("instruct_types", []):
        if arch.get("instruct_type") == inst:
            score += arch_cfg.get("bonus", 0.0)
            added = True
            break
    if not added:
        arch_str = str(arch).lower()
        for kw in arch_cfg.get("keywords", []):
            if kw.lower() in arch_str:
                score += arch_cfg.get("bonus", 0.0)
                break
    # Preview models bonus
    if "preview" in (model.get("id", "") or "").lower():
        score += eff_cfg.get("preview_bonus", 0.0)
    # Size-based bonuses
    params = extract_params(model.get("name", ""), model.get("description", "")) or 0
    for sz in eff_cfg.get("size", []):
        if params >= sz.get("min", 0):
            score += sz.get("bonus", 0.0)
            break
    # Specialty bonuses
    specs = extract_specialties(model.get("description", ""), model.get("architecture", {}))
    sb = eff_cfg.get("specialty_bonus", {})
    # Specialty bonuses
    if "coding" in specs and "reasoning" in specs:
        score += sb.get("both_coding_reasoning", 0.0)
    if "tool_calling" in specs:
        score += sb.get("tool_calling", 0.0)

    # Recency bonus (newer models)
    rec_cfg = eff_cfg.get("recency", [])
    created_ts = model.get("created")
    if isinstance(created_ts, (int, float)):
        try:
            days_ago = (datetime.now() - datetime.fromtimestamp(created_ts)).days
            for rec in rec_cfg:
                if days_ago <= rec.get("max_days", 0):
                    score += rec.get("bonus", 0.0)
                    break
        except Exception:
            pass

    # Quantization penalty for smaller/quantized variants
    quant_cfg = eff_cfg.get("quantization", {})
    text = ((model.get("name", "") or "") + " " + (model.get("description", "") or "")).lower()
    for pat in quant_cfg.get("patterns", []):
        if pat.lower() in text:
            score -= quant_cfg.get("penalty", 0.0)
            break

    # Family bonus for known strong model families
    fam_cfg = eff_cfg.get("family_bonus", {})
    for fam, bonus in fam_cfg.items():
        if fam.lower() in text:
            score += bonus
            break

    # Multimodal capability bonus
    mm_cfg = eff_cfg.get("multimodal", {})
    for kw in mm_cfg.get("keywords", []):
        if kw.lower() in text:
            score += mm_cfg.get("bonus", 0.0)
            break

    # Clamp score to [0, 10]
    return min(10, max(0, score))

def format_release_date(created: int) -> str:
    """Format Unix timestamp to readable date."""
    try:
        return datetime.fromtimestamp(created).strftime('%Y-%m-%d')
    except (TypeError, ValueError):
        return 'N/A'

def is_free_or_preview(model: Dict) -> bool:
    """Check if model is free or preview version."""
    model_id = (model.get('id') or '').lower()
    model_name = (model.get('name') or '').lower()
    # Preview or free tag
    if 'preview' in model_id or 'preview' in model_name:
        return True
    if ':free' in model_id:
        return True
    # Zero pricing
    pricing = model.get('pricing') or {}
    if isinstance(pricing, dict):
        try:
            if all(float(v) == 0 for v in pricing.values() if v is not None):
                return True
        except (ValueError, TypeError):
            pass
    return False

def fetch_all_models(retries: int = 3, backoff: float = 1.0, timeout: tuple = (5, 30)) -> List[Dict]:
    """Fetch all models with retry/backoff. Returns list of model dicts."""
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    session = requests.Session()
    retry_strategy = Retry(
        total=retries,
        backoff_factor=backoff,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    headers = {"Authorization": f"Bearer {API_KEY}"}
    try:
        resp = session.get(API_URL, headers=headers, timeout=timeout)
        resp.raise_for_status()
        data = resp.json().get("data", [])
        if isinstance(data, list):
            return data
    except Exception:
        pass
    return []
