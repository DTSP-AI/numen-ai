"""
Scheduler Service - Automated Session Execution

Background service that:
1. Checks for pending scheduled sessions
2. Sends notifications/reminders
3. Marks sessions as executed
4. Handles recurring sessions

Run this as a background task using APScheduler or Celery.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json

from database import get_pg_pool

logger = logging.getLogger(__name__)


class SchedulerService:
    """
    Automated scheduler for affirmation and script sessions

    Runs periodically to check for pending sessions and send notifications.
    """

    def __init__(self):
        self.check_interval_seconds = 60  # Check every minute

    async def run_forever(self):
        """
        Run scheduler loop forever

        Call this from a background worker or systemd service
        """
        logger.info("🕐 Scheduler service started")

        while True:
            try:
                await self.check_and_execute_pending_sessions()
                await asyncio.sleep(self.check_interval_seconds)
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(self.check_interval_seconds)

    async def check_and_execute_pending_sessions(self):
        """
        Check for sessions scheduled in the next 5 minutes
        and send notifications
        """
        pool = get_pg_pool()
        now = datetime.utcnow()
        window_end = now + timedelta(minutes=5)

        try:
            async with pool.acquire() as conn:
                # Get pending sessions in the time window
                rows = await conn.fetch("""
                    SELECT
                        ss.id,
                        ss.user_id,
                        ss.affirmation_id,
                        ss.script_id,
                        ss.scheduled_at,
                        ss.recurrence_rule,
                        ss.notification_sent,
                        u.email,
                        u.name
                    FROM scheduled_sessions ss
                    JOIN users u ON ss.user_id = u.id
                    WHERE ss.executed_at IS NULL
                      AND ss.scheduled_at <= $1
                      AND ss.scheduled_at >= $2
                      AND ss.notification_sent = FALSE
                    ORDER BY ss.scheduled_at ASC
                """, window_end, now)

                if rows:
                    logger.info(f"📬 Found {len(rows)} pending sessions")

                for row in rows:
                    await self._send_notification(dict(row))
                    await self._mark_notification_sent(str(row['id']))

        except Exception as e:
            logger.error(f"Failed to check pending sessions: {e}")

    async def _send_notification(self, session: Dict[str, Any]):
        """
        Send notification for scheduled session

        In production, integrate with:
        - Email (SendGrid, AWS SES)
        - Push notifications (FCM, APNs)
        - SMS (Twilio)
        - Webhooks
        """
        session_id = session['id']
        user_email = session['email']
        user_name = session['name'] or "User"
        scheduled_at = session['scheduled_at']

        # Build notification message
        if session['affirmation_id']:
            content_type = "Affirmation"
            content_id = session['affirmation_id']
        elif session['script_id']:
            content_type = "Hypnosis Session"
            content_id = session['script_id']
        else:
            content_type = "Session"
            content_id = None

        message = f"""
Hi {user_name},

Your {content_type} is scheduled for {scheduled_at.strftime('%I:%M %p')}.

Take a moment to center yourself and begin your manifestation practice.

🌟 Numen AI
"""

        # Log notification (replace with actual email/push service)
        logger.info(f"📧 Notification sent to {user_email}")
        logger.info(f"   Session ID: {session_id}")
        logger.info(f"   Content: {content_type}")
        logger.info(f"   Scheduled: {scheduled_at}")

        # TODO: Integrate actual notification service
        # await email_service.send(user_email, "Your Session is Starting", message)
        # await push_service.send(user_id, "Session Reminder", message)

    async def _mark_notification_sent(self, session_id: str):
        """Mark session notification as sent"""
        pool = get_pg_pool()

        try:
            async with pool.acquire() as conn:
                await conn.execute("""
                    UPDATE scheduled_sessions
                    SET notification_sent = TRUE
                    WHERE id = $1::uuid
                """, session_id)

            logger.info(f"✅ Marked notification sent: {session_id}")

        except Exception as e:
            logger.error(f"Failed to mark notification sent: {e}")

    async def execute_past_due_sessions(self):
        """
        Mark past-due sessions as executed

        Sessions that were scheduled but are now > 1 hour past due
        """
        pool = get_pg_pool()
        cutoff = datetime.utcnow() - timedelta(hours=1)

        try:
            async with pool.acquire() as conn:
                result = await conn.execute("""
                    UPDATE scheduled_sessions
                    SET executed_at = NOW(),
                        execution_status = 'missed'
                    WHERE executed_at IS NULL
                      AND scheduled_at < $1
                """, cutoff)

                if result:
                    logger.info(f"⏰ Marked {result} past-due sessions as missed")

        except Exception as e:
            logger.error(f"Failed to execute past-due sessions: {e}")

    async def create_recurring_sessions(self):
        """
        Create next instances of recurring sessions

        For sessions with recurrence rules, create the next scheduled instance
        after execution.
        """
        pool = get_pg_pool()

        try:
            async with pool.acquire() as conn:
                # Get executed recurring sessions without a next instance
                rows = await conn.fetch("""
                    SELECT
                        ss.id,
                        ss.user_id,
                        ss.affirmation_id,
                        ss.script_id,
                        ss.scheduled_at,
                        ss.recurrence_rule
                    FROM scheduled_sessions ss
                    WHERE ss.executed_at IS NOT NULL
                      AND ss.recurrence_rule IS NOT NULL
                      AND NOT EXISTS (
                          SELECT 1 FROM scheduled_sessions ss2
                          WHERE ss2.user_id = ss.user_id
                            AND ss2.recurrence_rule = ss.recurrence_rule
                            AND ss2.executed_at IS NULL
                      )
                    LIMIT 100
                """)

                for row in rows:
                    next_scheduled_at = self._calculate_next_occurrence(
                        row['scheduled_at'],
                        row['recurrence_rule']
                    )

                    if next_scheduled_at:
                        # Create next instance
                        await conn.execute("""
                            INSERT INTO scheduled_sessions (
                                id, user_id, affirmation_id, script_id,
                                scheduled_at, recurrence_rule,
                                notification_sent, created_at, updated_at
                            )
                            VALUES (gen_random_uuid(), $1::uuid, $2::uuid, $3::uuid, $4, $5, FALSE, NOW(), NOW())
                        """,
                            row['user_id'],
                            row['affirmation_id'],
                            row['script_id'],
                            next_scheduled_at,
                            row['recurrence_rule']
                        )

                        logger.info(f"🔄 Created recurring session: {next_scheduled_at}")

        except Exception as e:
            logger.error(f"Failed to create recurring sessions: {e}")

    def _calculate_next_occurrence(self, last_occurrence: datetime, recurrence_rule: str) -> datetime:
        """
        Calculate next occurrence based on recurrence rule

        Supports simple rules:
        - FREQ=DAILY → Add 1 day
        - FREQ=WEEKLY → Add 7 days
        - FREQ=MONTHLY → Add 30 days (approximate)
        """
        if "FREQ=DAILY" in recurrence_rule:
            return last_occurrence + timedelta(days=1)
        elif "FREQ=WEEKLY" in recurrence_rule:
            return last_occurrence + timedelta(days=7)
        elif "FREQ=MONTHLY" in recurrence_rule:
            return last_occurrence + timedelta(days=30)
        else:
            return last_occurrence + timedelta(days=1)  # Default to daily


# Global scheduler instance
scheduler = SchedulerService()


async def start_scheduler():
    """
    Start the scheduler service

    Call this from a background worker script:

    ```python
    # background_worker.py
    import asyncio
    from services.scheduler import start_scheduler

    asyncio.run(start_scheduler())
    ```
    """
    logger.info("🚀 Starting scheduler service...")
    await scheduler.run_forever()


if __name__ == "__main__":
    """
    Run scheduler as standalone script:

    python backend/services/scheduler.py
    """
    import sys
    import os

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Initialize database
    from database import init_db

    async def main():
        await init_db()
        await start_scheduler()

    asyncio.run(main())
