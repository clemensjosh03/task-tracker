from database import SessionLocal
import models
from datetime import datetime, timedelta
from utils import send_email

db = SessionLocal()

def should_send(user):
    now = datetime.now()

    if not user.last_sent:
        user.last_sent = now
        return True

    diff = now - user.last_sent

    if diff.total_seconds() >= user.notification_interval * 3600:
        user.last_sent = now
        return True

    return False


def run():
    now = datetime.now()

    users = db.query(models.User).all()

    for user in users:
        upcoming_limit = now + timedelta(days=user.alert_days)

        tasks = db.query(models.Task).filter(
            models.Task.user_email == user.email
        ).all()

        overdue = []
        upcoming = []

        for t in tasks:
            if t.due_date < now:
                overdue.append(t)
            elif t.due_date <= upcoming_limit:
                upcoming.append(t)

        if (overdue or upcoming) and should_send(user):

            msg = ""

            if overdue:
                msg += "OVERDUE:\n"
                for t in overdue:
                    msg += f"- {t.task_name} ({t.due_date})\n"

            if upcoming:
                msg += f"\nDUE IN {user.alert_days} DAYS:\n"
                for t in upcoming:
                    msg += f"- {t.task_name} ({t.due_date})\n"

            send_email(user.email, "Task Summary", msg)

            db.commit()  # IMPORTANT (saves last_sent)

if __name__ == "__main__":
    run()