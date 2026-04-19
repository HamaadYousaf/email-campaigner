🎯 The 8 Core Metrics You Should Implement
📬 1️⃣ Emails Processed Total (Counter)
emails_processed_total

What it shows:

Total successfully delivered emails

Why it matters:

Measures throughput
Used to compute rate

In Grafana:

rate(emails_processed_total[1m])

This gives emails/sec.

❌ 2️⃣ Emails Failed Total (Counter)
emails_failed_total

What it shows:

Total failed emails

Why it matters:

Reliability tracking

In Grafana:

rate(emails_failed_total[1m])
📊 3️⃣ Email Processing Duration (Histogram)
email_processing_duration_seconds

Why:

Measures latency
Lets you compute p95

In Grafana:

histogram_quantile(0.95, rate(email_processing_duration_seconds_bucket[1m]))

This is very impressive in interviews.

📦 4️⃣ Queue Length (Gauge)
email_queue_length

Why:

Shows backlog
Detects overload

If queue length keeps rising → workers can't keep up.

This is a key SRE metric.

🌐 5️⃣ HTTP Requests Total (Counter)
http_requests_total

Why:

Measures traffic
Shows system usage

Grafana:

rate(http_requests_total[1m])
⏱ 6️⃣ HTTP Request Duration (Histogram)
http_request_duration_seconds

Why:

API latency tracking
Detects backend slowdowns

Grafana:

histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[1m]))
🔄 7️⃣ Worker Running Indicator (Gauge)
worker_up

Set to:

1 if worker alive
0 if not

Why:

Detect worker crashes
Enables alerting
🧮 8️⃣ Success Rate (Derived Metric)

You don’t implement this directly — you compute it in Grafana:

rate(emails_processed_total[1m])
/
(rate(emails_processed_total[1m]) + rate(emails_failed_total[1m]))

This gives success percentage.

That’s production-level reliability monitoring.
