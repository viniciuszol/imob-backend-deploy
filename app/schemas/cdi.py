from typing import Optional
from pydantic import BaseModel
from datetime import date
from decimal import Decimal

class CDICreate(BaseModel):
    data: date
    porcentagem: Decimal | None = Decimal("100.00")
    cdi_am: Decimal | None = None
    cdi_percentual_am: Decimal | None = None

class CDIUpdate(BaseModel):
    porcentagem: Decimal | None = None
    cdi_am: Decimal | None = None
    cdi_percentual_am: Decimal | None = None
    taxa: Optional[float] = None

class CDIOut(CDICreate):
    id: int

    model_config = {
        "from_attributes": True
    }
