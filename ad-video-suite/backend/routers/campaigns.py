from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.campaigns import (
    create_campaign,
    get_campaign,
    list_campaigns,
    update_settings,
)
from agents.config import get_settings

router = APIRouter()


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

class SettingsBody(BaseModel):
    base_path: Optional[str] = None
    max_active_campaigns: Optional[int] = None


@router.get("/api/settings")
async def get_settings_endpoint():
    s = get_settings()
    return {
        "base_path":            s.get("base_path", ""),
        "max_active_campaigns": s.get("max_active_campaigns", 3),
    }


@router.put("/api/settings")
async def put_settings(body: SettingsBody):
    return update_settings(base_path=body.base_path, max_active_campaigns=body.max_active_campaigns)


# ---------------------------------------------------------------------------
# Campaigns
# ---------------------------------------------------------------------------

class CreateBody(BaseModel):
    name: Optional[str] = None


@router.get("/api/campaigns")
async def get_campaigns():
    """List all C### campaigns in base_path."""
    return list_campaigns()


@router.post("/api/campaigns")
async def post_campaign(body: CreateBody):
    """Create a new campaign with an auto-generated C### slug."""
    return create_campaign(body.name)


@router.get("/api/campaigns/{slug}")
async def get_campaign_detail(slug: str):
    meta = get_campaign(slug)
    if meta is None:
        raise HTTPException(status_code=404, detail=f"Campaign '{slug}' not found")
    return meta
