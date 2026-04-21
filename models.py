from sqlalchemy import Column, Integer, String, DateTime
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String)
    task_name = Column(String)
    due_date = Column(DateTime)
