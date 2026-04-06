from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from typing import List, Dict
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)


app = FastAPI()


class CampaignCreate(BaseModel):
    name: str
    subject: str
    body: str


class EmailsCreate(BaseModel):
    emails: List[EmailStr]


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/campaigns")
async def create_campaign(payload: CampaignCreate):
    """Create a campaign."""
    campaign_payload = {
        "name": payload.name,
        "subject": payload.subject,
        "body": payload.body,
        "status": "draft",
    }

    try:
        response = supabase.table("campaigns").insert(campaign_payload).execute()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to create campaign: {exc}")

    if not response or not getattr(response, "data", None):
        raise HTTPException(
            status_code=500, detail="Failed to create campaign, empty response"
        )

    return response.data


@app.post("/campaigns/{campaign_id}/emails")
async def add_emails(campaign_id: int, payload: EmailsCreate):
    """Add emails to a campaign."""
    try:
        camp_response = (
            supabase.table("campaigns")
            .select("id")
            .eq("id", campaign_id)
            .maybe_single()
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to query campaign: {exc}")

    if not camp_response or not camp_response.data:
        raise HTTPException(status_code=404, detail="Campaign not found")

    emails_payload = [
        {
            "campaign_id": campaign_id,
            "address": address,
            "status": "pending",
        }
        for address in payload.emails
    ]

    try:
        response = supabase.table("emails").insert(emails_payload).execute()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to insert emails: {exc}")

    if not response or not getattr(response, "data", None):
        raise HTTPException(status_code=500, detail="Failed to insert emails")

    return {"added": len(payload.emails)}


@app.post("/campaigns/{campaign_id}/send")
async def send_campaign(campaign_id: int):
    """Queue campaign emails for sending."""
    try:
        camp_response = (
            supabase.table("campaigns")
            .select("id")
            .eq("id", campaign_id)
            .maybe_single()
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to query campaign: {exc}")

    if not camp_response or not camp_response.data:
        raise HTTPException(status_code=404, detail="Campaign not found")

    try:
        emails_response = (
            supabase.table("emails")
            .select("id")
            .eq("campaign_id", campaign_id)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to query campaign emails: {exc}"
        )

    queued_count = (
        len(emails_response.data) if emails_response and emails_response.data else 0
    )

    if queued_count == 0:
        raise HTTPException(
            status_code=400, detail="Cannot send campaign with no emails"
        )

    try:
        update_response = (
            supabase.table("campaigns")
            .update({"status": "queued"})
            .eq("id", campaign_id)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to update campaign status: {exc}"
        )

    if not update_response or not getattr(update_response, "data", None):
        raise HTTPException(status_code=500, detail="Failed to update campaign status")

    return {"queued": queued_count}


@app.get("/campaigns/{campaign_id}")
async def get_campaign(campaign_id: str):
    try:
        response = (
            supabase.table("campaigns")
            .select("*")
            .eq("id", campaign_id)
            .maybe_single()
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to query campaign: {exc}")

    if not response or not response.data:
        raise HTTPException(status_code=404, detail="Campaign not found")

    campaign = response.data

    try:
        emails_response = (
            supabase.table("emails")
            .select("address, status, sent_at")
            .eq("campaign_id", campaign_id)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to query campaign emails: {exc}"
        )

    emails = emails_response.data if emails_response and emails_response.data else []

    return {
        "id": campaign["id"],
        "name": campaign["name"],
        "status": campaign["status"],
        "emails": emails,
    }
