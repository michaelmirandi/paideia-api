from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from db.session import Base

# ACTIVITY LOG


class Activity(Base):
    __tablename__ = "activity_log"

    id = Column(Integer, primary_key=True, index=True)
    user_details_id = Column(Integer)
    action = Column(String)
    value = Column(String)
    secondary_action = Column(String)
    secondary_value = Column(String)
    date = Column(DateTime(timezone=True), server_default=func.now())
    category = Column(String)


class vw_activity_log(Base):
    __tablename__ = "vw_activity_log"

    id = Column(Integer, primary_key=True, index=True)
    user_details_id = Column(Integer)
    name = Column(String)
    img_url = Column(String)
    action = Column(String)
    value = Column(String)
    secondary_action = Column(String)
    secondary_value = Column(String)
    date = Column(DateTime(timezone=True))
    category = Column(String)
