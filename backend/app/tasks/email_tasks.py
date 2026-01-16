"""Celery tasks for email notifications.

Async tasks for sending email alerts including daily digests,
new opportunity notifications, and weekly summaries.
"""

import os
import sys
from datetime import UTC, datetime, timedelta

from celery import Task

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.celery_app import celery_app
from app.db import SessionLocal
from app.models import Opportunity, User
from app.services.email_service import EmailService


class EmailTask(Task):
    """Base task for email operations."""

    def __init__(self):
        self._db = None

    @property
    def db(self):
        """Lazy database session."""
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def after_return(self, *args, **kwargs):
        """Close database session after task completes."""
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(base=EmailTask, bind=True)
def send_alert_email(self, user_id: str, opportunity_id: str, alert_type: str = 'new_validated'):
    """Send alert email to user about new opportunity.

    Args:
        self: Task instance
        user_id: User ID
        opportunity_id: Opportunity ID
        alert_type: Type of alert (new_validated, high_score, etc.)

    Returns:
        Email send result
    """
    db = self.db

    user = db.query(User).filter(User.id == user_id).first()
    opportunity = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()

    if not user or not opportunity:
        return {'error': 'User or opportunity not found'}

    EmailService()

    if alert_type == 'new_validated':
        subject = f"New Validated Opportunity: {opportunity.title}"
        f"""
        A new validated opportunity has been discovered!

        Title: {opportunity.title}
        Score: {opportunity.score}/100
        Competition: {opportunity.competitor_count} competitors
        Mentions: {opportunity.mention_count}

        Description: {opportunity.description[:200]}...

        Login to view more details and track this opportunity.
        """
    else:
        subject = f"New Opportunity: {opportunity.title}"

    # For now, just log - actual email sending would use EmailService
    print(f"Email to {user.email}: {subject}")

    return {
        'user_id': user_id,
        'opportunity_id': opportunity_id,
        'alert_type': alert_type,
        'sent': True
    }


@celery_app.task(base=EmailTask, bind=True)
def send_daily_digest(self):
    """Send daily digest email to all users.

    Scheduled task that runs at 9 AM UTC daily.

    Args:
        self: Task instance

    Returns:
        Summary of sent emails
    """
    db = self.db

    # Get all verified users
    users = db.query(User).filter(
        User.email_verified is True
    ).all()

    sent_count = 0
    failed_count = 0

    # Get new opportunities from last 24 hours
    yesterday = datetime.now(UTC) - timedelta(days=1)
    new_opportunities = db.query(Opportunity).filter(
        Opportunity.created_at >= yesterday
    ).order_by(Opportunity.score.desc()).limit(10).all()

    if not new_opportunities:
        return {'sent': 0, 'message': 'No new opportunities to send'}

    for user in users:
        try:
            # Build digest email
            "\n\n".join([
                f"- {opp.title} (Score: {opp.score}/100)"
                for opp in new_opportunities
            ])

            EmailService()

            # For now, just log
            print(f"Daily digest for {user.email}: {len(new_opportunities)} new opportunities")

            sent_count += 1

        except Exception as e:
            print(f"Error sending digest to {user.email}: {e}")
            failed_count += 1

    return {
        'sent': sent_count,
        'failed': failed_count,
        'total_users': len(users),
        'opportunity_count': len(new_opportunities)
    }


@celery_app.task(base=EmailTask, bind=True)
def send_weekly_summary(self):
    """Send weekly summary email to all users.

    Args:
        self: Task instance

    Returns:
        Summary of sent emails
    """
    db = self.db

    users = db.query(User).filter(
        User.email_verified is True
    ).all()

    sent_count = 0

    # Get stats from last week
    week_ago = datetime.now(UTC) - timedelta(days=7)

    total_new = db.query(Opportunity).filter(
        Opportunity.created_at >= week_ago
    ).count()

    total_validated = db.query(Opportunity).filter(
        and_(
            Opportunity.created_at >= week_ago,
            Opportunity.is_validated is True
        )
    ).count()

    avg_score = db.query(func.avg(Opportunity.score)).filter(
        and_(
            Opportunity.created_at >= week_ago,
            Opportunity.score.isnot(None)
        )
    ).scalar() or 0

    for user in users:
        try:
            print(f"Weekly summary for {user.email}")
            print(f"  New opportunities: {total_new}")
            print(f"  Validated: {total_validated}")
            print(f"  Avg score: {avg_score:.1f}")

            sent_count += 1

        except Exception as e:
            print(f"Error sending weekly summary to {user.email}: {e}")

    return {
        'sent': sent_count,
        'total_new': total_new,
        'total_validated': total_validated,
        'avg_score': round(avg_score, 2)
    }


# Add missing import
from sqlalchemy import and_, func
