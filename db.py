from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, String, Boolean, DateTime, Date, Float, Text
from config import settings
from sqlalchemy.sql import func

# create db engine
engine = create_engine(settings.DATABASE_URL)

# create session for db operations
SessionLocal = sessionmaker(autoflush=False, bind=engine, autocommit=False)

# base class for declarative models
Base = declarative_base()


# ===== FOR TEST DB =====
engine_test = create_engine(settings.TEST_DB_URL)
SessionLocalTest = sessionmaker(autoflush=False, bind=engine_test, autocommit=False)
# =======================

# main db session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# test db session
def get_test_db():
    test_db = SessionLocalTest()
    try:
        yield test_db
    finally:
        test_db.close()
        
# db models 
class FireModel(Base):
    __tablename__ = "fire_data"

    id = Column(String, primary_key=True, nullable=False, unique=True)

    # general info
    name = Column(String, nullable=False)
    location = Column(String, nullable=False)
    county = Column(String, nullable=False)

    # status fields
    is_active = Column(Boolean, nullable=False)
    final = Column(Boolean, nullable=False)

    # date and time fields, using timezone-aware DateTime
    updated_datetime = Column(DateTime(timezone=True), nullable=False)
    start_datetime = Column(DateTime(timezone=True), nullable=False)
    extinguished_datetime = Column(DateTime(timezone=True), nullable=True) # Optional field
    start_date = Column(Date, nullable=True) # Optional field

    # fire metrics
    acres_burned = Column(Float, nullable=False)
    percent_contained = Column(Float, nullable=False)

    # coordinates
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    # descriptive fields
    fire_type = Column(String, nullable=False)
    control_statement = Column(Text, nullable=True)
    url = Column(String, nullable=True) # Optional field

    inserted_at = Column(DateTime(timezone=True), server_default=func.now())
