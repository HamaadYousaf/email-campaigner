# 📧 Email-Campaigner

A distributed email campaign platform that lets users create campaigns, upload recipient lists, and track delivery status in real time. Built to demonstrate async job processing, queue-based architecture, and production-grade observability.

---

## 🔍 What It Does

- Create and manage email campaigns
- Upload a list of recipient email addresses
- Trigger bulk sends with a single click
- Track each email through its lifecycle: `Pending → Queued → Delivered / Failed`
- Monitor system performance through live Prometheus metrics and Grafana dashboards

## 🛠️ Technologies

| Layer          | Technology       |
| -------------- | ---------------- |
| Frontend       | React            |
| Backend API    | FastAPI (Python) |
| Database       | Supabase         |
| Queue          | Redis            |
| Worker         | Python           |
| Metrics        | Prometheus       |
| Dashboards     | Grafana          |
| Infrastructure | Docker Compose   |
| Email Delivery | Resend API       |
