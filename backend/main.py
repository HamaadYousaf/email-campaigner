from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from typing import List, Dict

app = FastAPI()

# In-memory placeholder storage (replace with DB in later steps)
_campaigns: Dict[int, Dict] = {}
_emails: Dict[int, Dict] = {}
_next_campaign_id = 1
_next_email_id = 1


class CampaignCreate(BaseModel):
    name: str


class EmailsCreate(BaseModel):
    emails: List[EmailStr]


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/campaigns")
async def create_campaign(payload: CampaignCreate):
    """Create a campaign."""
    global _next_campaign_id

    campaign = {
        "id": _next_campaign_id,
        "name": payload.name,
        "status": "draft",
        "emails": [],
    }
    _campaigns[_next_campaign_id] = campaign
    _next_campaign_id += 1
    return campaign


@app.post("/campaigns/{campaign_id}/emails")
async def add_emails(campaign_id: int, payload: EmailsCreate):
    """Add emails to a campaign."""
    campaign = _campaigns.get(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    global _next_email_id
    for address in payload.emails:
        email = {
            "id": _next_email_id,
            "campaign_id": campaign_id,
            "address": address,
            "status": "pending",
        }
        _emails[_next_email_id] = email
        campaign["emails"].append(email)
        _next_email_id += 1

    return {"added": len(payload.emails)}


@app.post("/campaigns/{campaign_id}/send")
async def send_campaign(campaign_id: int):
    """Queue campaign emails for sending."""
    campaign = _campaigns.get(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # In a real implementation this would push jobs to Redis
    # For now, just update status and report how many were queued
    campaign["status"] = "queued"
    queued_count = len(campaign["emails"])
    return {"queued": queued_count}


@app.get("/campaigns/{campaign_id}")
async def get_campaign(campaign_id: int):
    """Return campaign and all its email statuses."""
    campaign = _campaigns.get(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Return only the fields the frontend expects
    emails = [
        {"address": e["address"], "status": e["status"]}
        for e in campaign.get("emails", [])
    ]

    return {
        "id": campaign["id"],
        "name": campaign["name"],
        "status": campaign["status"],
        "emails": emails,
    }
