"""Configuration API routes"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
import yaml
import os
import json
from datetime import datetime

from app.database.connection import get_db
from app.models.config import ConfigResponse, ConfigUpdate, ScoringWeights

router = APIRouter(prefix="/api/config", tags=["config"])

# Path to config file
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "config", "config.yaml")


def load_config():
    """Load config from YAML file"""
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        # Return default config
        return {
            "scoring": {
                "weights": {"money": 0.33, "passion": 0.34, "location": 0.33},
                "money": {
                    "salary_thresholds": {"excellent": 80000, "great": 65000, "good": 50000, "average": 40000}
                },
                "passion": {
                    "energy_keywords": ["energy", "renewable", "grid", "power"],
                    "ml_keywords": ["machine learning", "deep learning", "ai", "data science"],
                    "tech_keywords": ["startup", "innovation", "research"]
                },
                "location": {
                    "tier1_bavaria": {"score": 10, "keywords": ["munich", "münchen", "augsburg"]},
                    "tier2_preferred_germany": {"score": 8, "keywords": ["berlin", "leipzig"]},
                }
            }
        }


def save_config(config: dict):
    """Save config to YAML file"""
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)


@router.get("", response_model=ConfigResponse)
async def get_config():
    """Get current configuration"""
    config = load_config()
    scoring = config.get("scoring", {})
    
    weights = scoring.get("weights", {})
    money_config = scoring.get("money", {})
    passion_config = scoring.get("passion", {})
    location_config = scoring.get("location", {})
    
    return ConfigResponse(
        scoring_weights=ScoringWeights(
            money=weights.get("money", 0.33),
            passion=weights.get("passion", 0.34),
            location=weights.get("location", 0.33)
        ),
        money_thresholds=money_config.get("salary_thresholds", {}),
        passion_keywords={
            "energy": passion_config.get("energy_keywords", []),
            "ml": passion_config.get("ml_keywords", []),
            "tech": passion_config.get("tech_keywords", [])
        },
        location_tiers={
            "tier1_bavaria": location_config.get("tier1_bavaria", {}),
            "tier2_preferred_germany": location_config.get("tier2_preferred_germany", {}),
            "tier3_germany": location_config.get("tier3_germany", {}),
            "tier4_remote": location_config.get("tier4_remote", {}),
        }
    )


@router.put("")
async def update_config(
    update: ConfigUpdate,
    db: Session = Depends(get_db)
):
    """Update configuration and optionally recalculate scores"""
    config = load_config()
    
    if update.scoring_weights:
        # Validate weights sum to 1.0
        total = update.scoring_weights.money + update.scoring_weights.passion + update.scoring_weights.location
        if abs(total - 1.0) > 0.01:
            raise HTTPException(status_code=400, detail=f"Weights must sum to 1.0, got {total}")
        
        config["scoring"]["weights"] = {
            "money": update.scoring_weights.money,
            "passion": update.scoring_weights.passion,
            "location": update.scoring_weights.location
        }
    
    # Save config
    save_config(config)
    
    # Save snapshot to database
    db.execute(text("""
        INSERT INTO config_snapshots (config, description)
        VALUES (:config, :description)
    """), {
        "config": json.dumps(config),
        "description": "Updated scoring weights"
    })
    db.commit()
    
    # Recalculate total scores for all jobs
    weights = config["scoring"]["weights"]
    db.execute(text("""
        UPDATE jobs
        SET total_score = (
            :money_weight * COALESCE(money_score, 0) +
            :passion_weight * COALESCE(passion_score, 0) +
            :location_weight * COALESCE(location_score, 0)
        )
    """), {
        "money_weight": weights["money"],
        "passion_weight": weights["passion"],
        "location_weight": weights["location"]
    })
    db.commit()
    
    # Count updated jobs
    result = db.execute(text("SELECT COUNT(*) FROM jobs"))
    updated_count = result.scalar()
    
    return {
        "success": True,
        "updated": updated_count,
        "config": config["scoring"]["weights"]
    }
