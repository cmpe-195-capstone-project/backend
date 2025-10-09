from pydantic import BaseModel, ConfigDict
from datetime import datetime, date


class FireSchema(BaseModel):
    id: str
    name: str
    final: bool
    updated_datetime: datetime
    start_datetime: datetime
    extinguished_datetime: str | datetime | None = None
    start_date: str | date | None = None
    county: str
    location: str
    acres_burned: float
    percent_contained: float
    control_statement: str | None = None
    longitude: float
    latitude: float
    fire_type: str
    is_active: bool
    url: str | None = None
    inserted_at: datetime | None

    model_config = ConfigDict(frozen=True)