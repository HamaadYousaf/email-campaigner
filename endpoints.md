The 4 Endpoints

POST /campaigns
What it does: Creates a new campaign and saves it to Supabase.
Frontend sends: { "name": "Black Friday Sale" }
Backend saves: campaigns table → id: 1, name: "Black Friday Sale", status: "draft"
Backend returns: { "id": 1, "name": "Black Friday Sale", "status": "draft" }

POST /campaigns/{id}/emails
What it does: Adds a list of email addresses to a campaign.
Frontend sends: { "emails": ["a@gmail.com", "b@gmail.com", "c@gmail.com"] }
Backend saves: emails table → 3 rows, all with campaign_id: 1, status: "pending"
Backend returns: { "added": 3 }

POST /campaigns/{id}/send
What it does: This is the most important endpoint. It does 3 things in sequence:

1. Fetch all emails for campaign_id: 1 from Supabase
2. Push each email as a job to Redis queue
3. Update campaign status → "queued"

Backend returns: { "queued": 3 }
Visually:
Backend → Redis queue: [job1, job2, job3]
Worker sees: new jobs → starts processing

GET /campaigns/{id}
What it does: Returns the campaign and all its email statuses. This is what the frontend polls every 3 seconds.
Backend fetches: campaign row + all email rows for that id
Backend returns: {
"id": 1,
"name": "Black Friday Sale",
"status": "queued",
"emails": [
{ "address": "a@gmail.com", "status": "delivered" },
{ "address": "b@gmail.com", "status": "queued" },
{ "address": "c@gmail.com", "status": "failed" }
]
}

GET /metrics
What it does: Exposes Prometheus metrics for the backend service, including queue length and HTTP performance.
Backend returns: Prometheus text exposition for all registered metrics.

Worker metrics endpoint: http://localhost:8001/metrics
What it does: Exposes worker-level metrics such as worker_up, processing duration, success/failure counts, and queue length.

The Full Flow End to End

1. POST /campaigns → creates campaign
2. POST /campaigns/1/emails → adds emails
3. POST /campaigns/1/send → pushes to Redis
   ↓
   Worker picks up jobs
   Worker sends emails
   Worker updates DB → "delivered" or "failed"
   ↓
4. GET /campaigns/1 → frontend polls, sees status updates

Status Lifecycle of an Email
pending → queued → delivered
↘ failed
StatusWhenpendingEmail added to campaign, not sent yetqueuedJob pushed to Redis, worker hasn't picked it up yetdeliveredWorker successfully sent the emailfailedWorker hit an error sending

What the Worker Sees in Redis
Each job on the Redis queue is just a small JSON blob:
json{ "email_id": 42, "address": "a@gmail.com", "campaign_id": 1 }
Worker pops it, sends the email, then updates that email_id row in Supabase. The frontend sees the change on its next poll.
