import time

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, EmailStr
from typing import List, Dict, Optional
import os
from supabase import create_client, Client
from dotenv import load_dotenv
import redis
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

redis_client = redis.Redis(host="redis", port=6379, db=0)


app = FastAPI()

emails_processed_total = Counter(
    "emails_processed_total",
    "Total successfully delivered emails",
)
emails_failed_total = Counter(
    "emails_failed_total",
    "Total failed emails",
)
email_processing_duration_seconds = Histogram(
    "email_processing_duration_seconds",
    "Email processing duration in seconds",
)
email_queue_length = Gauge(
    "email_queue_length",
    "Current number of messages waiting in the email queue",
)
http_requests_total = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "http_status"],
)
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        elapsed = time.time() - start_time
        endpoint = request.url.path
        method = request.method
        status_code = response.status_code
        http_requests_total.labels(
            method=method, endpoint=endpoint, http_status=status_code
        ).inc()
        http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint,
        ).observe(elapsed)
        return response


app.add_middleware(PrometheusMiddleware)


class CampaignCreate(BaseModel):
    name: str
    subject: str
    body: str


class EmailsCreate(BaseModel):
    emails: List[EmailStr]


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None


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


@app.put("/campaigns/{campaign_id}")
async def edit_campaign(campaign_id: int, payload: CampaignUpdate):
    """Edit a campaign (name, subject, and/or body)."""
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

    # Build update payload with only provided fields
    update_payload = {}
    if payload.name is not None:
        update_payload["name"] = payload.name
    if payload.subject is not None:
        update_payload["subject"] = payload.subject
    if payload.body is not None:
        update_payload["body"] = payload.body

    if not update_payload:
        raise HTTPException(
            status_code=400,
            detail="At least one field (name, subject, or body) must be provided",
        )

    try:
        response = (
            supabase.table("campaigns")
            .update(update_payload)
            .eq("id", campaign_id)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to update campaign: {exc}")

    if not response or not getattr(response, "data", None):
        raise HTTPException(status_code=500, detail="Failed to update campaign")

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


@app.delete("/emails/{email_id}")
async def delete_email(email_id: int):
    """Delete an email by ID."""
    try:
        email_response = (
            supabase.table("emails")
            .select("id")
            .eq("id", email_id)
            .maybe_single()
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to query email: {exc}")

    if not email_response or not email_response.data:
        raise HTTPException(status_code=404, detail="Email not found")

    try:
        response = supabase.table("emails").delete().eq("id", email_id).execute()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to delete email: {exc}")

    return {"deleted": email_id}


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

    if not emails_response or not emails_response.data:
        raise HTTPException(
            status_code=400, detail="Cannot send campaign with no emails"
        )

    try:
        for email in emails_response.data:
            redis_client.rpush("email_queue", email["id"])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to queue emails: {exc}")

    queued_count = len(emails_response.data)
    email_queue_length.set(redis_client.llen("email_queue"))

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
        "subject": campaign["subject"],
        "body": campaign["body"],
        "status": campaign["status"],
        "emails": emails,
    }


@app.get("/metrics")
async def metrics():
    try:
        email_queue_length.set(redis_client.llen("email_queue"))
    except Exception:
        email_queue_length.set(0)
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
