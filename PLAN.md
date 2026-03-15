🔢 Step-by-Step Build Order
Follow this exact sequence — each step unblocks the next.
Step 1 — Docker Compose Skeleton (infra only)
Run docker-compose with just the infrastructure services you need locally:

- redis
- prometheus
- grafana

The backend, worker, and frontend will run locally (not in Docker). This proves your orchestration and observability plumbing works without forcing every component into containers.

Step 2 — Database Schema (Supabase / Postgres)
Use Supabase (or any Postgres) as the database. The backend will connect to it via a connection string.

Design just 2 tables:

campaigns — id, name, status, created_at
emails — id, campaign_id, address, status (queued/delivered/failed), sent_at

No migrations framework needed at MVP. Raw SQL CREATE TABLE in an init script is fine (can run once in Supabase SQL editor or on backend startup).Step 3 — Backend API (FastAPI)
Build 4 endpoints only:

POST /campaigns — create a campaign
POST /campaigns/{id}/emails — add emails to a campaign
POST /campaigns/{id}/send — push jobs to Redis, set status → "queued"
GET /campaigns/{id} — return campaign + email statuses

No auth. No pagination. No validation beyond basics.
Step 4 — Redis Queue
Use a simple Redis List as your queue (LPUSH to enqueue, BRPOP to dequeue). Each job is a JSON blob: { "email_id": 1, "address": "x@x.com" }. No need for Celery or RQ at MVP — raw Redis commands are cleaner to understand.
Step 5 — Worker Service
A simple loop (Python script) that:

Blocks on BRPOP from Redis
"Sends" the email (just a time.sleep(1) + print — no real SMTP yet)
Updates the DB row to delivered or failed
Increments a Prometheus counter

That's the entire worker. No threads, no concurrency yet.
Step 6 — Prometheus Metrics
Expose a /metrics endpoint from both the backend and worker using the prometheus_client Python library. Track just 3 metrics to start:

emails_queued_total (counter)
emails_delivered_total (counter)
emails_failed_total (counter)

Add a prometheus.yml config that scrapes both services.
Step 7 — Grafana Dashboard
Connect Grafana to Prometheus as a data source. Build one dashboard with 3 panels:

Emails queued over time
Emails delivered over time
Delivery success rate (delivered / queued)

Use the Grafana UI to build it manually first — you can export JSON later.
Step 8 — React Frontend
Build one page with:

A form: campaign name + textarea for emails (one per line)
A "Send Campaign" button
A status table showing each email and its current state
A polling mechanism (setInterval every 3s) to refresh statuses

No routing. No state management library. Just useState + fetch.
Step 9 — Wire Everything Together
At this point each piece works in isolation. Now you verify the full happy path:

User submits form → Backend creates campaign → Pushes to Redis → Worker picks up → Updates DB → Frontend polls and shows "Delivered"

Walk through this flow manually, fix any broken connections.
Step 10 — Observability Check
Final step: trigger 10–20 test emails and confirm Grafana dashboards update in near-real-time. This validates your entire observability stack is wired correctly.

🔗 Communication Map
React → FastAPI → PostgreSQL
↘
Redis → Worker → PostgreSQL
↘
FastAPI /metrics ← Prometheus → Grafana
Worker /metrics ↗

⚠️ Key Rules for MVP

No real email sending until everything else works (use fake/mock)
No auth — waste of time at this stage
No error handling beyond basics — just happy path first
One Docker Compose file rules everything — docker compose up should start the world
