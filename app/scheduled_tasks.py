# app/scheduled_tasks.py

from apscheduler.schedulers.background import BackgroundScheduler
from .db import Database
from .token_manager import ZohoDeskTokenManager
from datetime import datetime
import logging
import requests

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def fetch_and_update_bid_records():
    logger.info("Starting to fetch and update bid records")
    db = Database()
    token_manager = ZohoDeskTokenManager(db.db)
    collection = db.bid_records_collection
    current_time = datetime.utcnow()

    open_bid_records = collection.find({"status": {"$ne": "Closed"}})
    logger.info(f"Found {open_bid_records.count()} open bid records")
    for record in open_bid_records:
        ticket_id = record.get("ticket id")
        if not ticket_id:
            continue

        try:
            access_token = token_manager.get_access_token()
            logger.info(f"Fetching ticket info for ticket ID: {ticket_id}")
            response = requests.get(
                f"https://desk.zoho.com/api/v1/tickets/{ticket_id}",
                headers={"Authorization": f"Zoho-oauthtoken {access_token}"}
            )

            if response.status_code == 200:
                ticket_data = response.json()
                updated_data = {
                    "subject": ticket_data.get("subject"),
                    "classification": ticket_data.get("classification"),
                    "status": ticket_data.get("statusType"),
                    "QUALIFICATION": ticket_data.get("qualification"),
                    "Bid Type": ticket_data.get("departmentName"),
                    "Main Product Category": ticket_data.get("product"),
                    "category": ticket_data.get("category"),
                    "last_updated_time": current_time
                }

                result = collection.update_one(
                    {"_id": record["_id"]},
                    {"$set": updated_data}
                )
                if result.modified_count > 0:
                    logger.info(f"Updated bid record for ticket ID: {ticket_id}")
                else:
                    logger.warning(f"No bid record updated for ticket ID: {ticket_id}")
            else:
                logger.error(f"Failed to fetch ticket info for ticket ID: {ticket_id}, status code: {response.status_code}")
                logger.error(f"Response: {response.text}")

        except Exception as e:
            logger.error(f"Error updating bid record for ticket ID: {ticket_id}: {e}")

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(fetch_and_update_bid_records, 'interval', hours=1)
    scheduler.start()
    logger.info("Scheduler started")
