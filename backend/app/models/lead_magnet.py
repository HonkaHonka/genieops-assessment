from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, Boolean # <--- ADDED Boolean
from app.db.base import Base
import datetime

class LeadMagnet(Base):
    __tablename__ = "lead_magnets"
    id = Column(Integer, primary_key=True, index=True)
    icp_profile = Column(Text)
    pain_points = Column(Text)
    brand_voice = Column(String)
    offer_type = Column(String)
    conversion_goal = Column(String)
    
    idea_title = Column(String)
    idea_type = Column(String)
    value_promise = Column(Text)
    
    asset_data = Column(JSON)
    landing_page_html = Column(Text)
    thank_you_html = Column(Text)
    linkedin_post = Column(Text)
    email_nurture_sequence = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    conversion_score = Column(Integer) # 1-100
    linkedin_img = Column(Text)       # Pexels URL for the post
    upgrade_offer_copy = Column(Text)  # Urgent offer text

class Lead(Base):
    __tablename__ = "leads"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    magnet_id = Column(Integer)
    # --- COMPLIANCE & TRIGGER FIELDS ---
    agreed_to_terms = Column(Boolean, default=True) # <--- This caused the error
    subscribed_to_newsletter = Column(Boolean, default=False) 
    nurture_stage = Column(Integer, default=0) 
    last_email_sent_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)