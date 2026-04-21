from sqlalchemy import Column, Integer, String, DateTime
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True)
    password = Column(String)
    reminder_days = Column(Integer, default=3)
    email_frequency = Column(String, default="daily")
    alert_days = Column(Integer, default=3)
    notification_interval = Column(Integer, default=24)  # hours
    last_sent = Column(DateTime, default=None)  # NEW


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String)
    task_name = Column(String)
    due_date = Column(DateTime)
