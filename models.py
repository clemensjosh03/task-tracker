from sqlalchemy import Column, Integer, String, DateTime
from database import Base
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)

    # NEW SAFE FIELDS
    reminder_days = Column(Integer, default=3)
    email_frequency = Column(String, default="daily")
    alert_days = Column(Integer, default=1)
    notification_interval = Column(Integer, default=24)
    last_sent = Column(DateTime, nullable=True)


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String)
    task_name = Column(String)
    due_date = Column(DateTime)
