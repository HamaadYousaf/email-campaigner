import redis
import time
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

redis_client = redis.Redis(host="localhost", port=6379, db=0)


def process_emails():
    """Continuously read the Redis queue for emails using blocking pop and simulate sending."""
    while True:
        try:
            # blpop returns (queue_name, item) as bytes
            result = redis_client.blpop(
                "email_queue", timeout=0
            )  # timeout=0 means block forever
            if result:
                queue_name, email_id_bytes = result
                email_id = int(email_id_bytes.decode("utf-8"))

                # Fetch email details from Supabase
                try:
                    email_data = (
                        supabase.table("emails")
                        .select("campaign_id, address")
                        .eq("id", email_id)
                        .maybe_single()
                        .execute()
                    )
                    if not email_data or not email_data.data:
                        print(f"Email {email_id} not found in database")
                        continue
                    campaign_id = email_data.data["campaign_id"]
                    address = email_data.data["address"]
                except Exception as e:
                    print(f"Error fetching email data for ID {email_id}: {e}")
                    continue

                # Simulate sending email
                print(f"Sending email to {address} for campaign {campaign_id}")
                time.sleep(1)  # simulate processing time

                # Update email status in Supabase
                supabase.table("emails").update(
                    {"status": "sent", "sent_at": "now()"}
                ).eq("id", email_id).execute()

                print(f"Email {email_id} marked as sent")

        except Exception as e:
            print(f"Error processing email: {e}")
            time.sleep(5)  # wait before retrying on error


if __name__ == "__main__":
    process_emails()
