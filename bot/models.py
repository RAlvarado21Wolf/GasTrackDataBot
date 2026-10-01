from typing import Literal

from pydantic import BaseModel


class PriceRecord(BaseModel):

    department: str

    superior: float | None = None

    regular: float | None = None

    diesel: float | None = None

    price_date: str | None = None

    modality: Literal["autoservicio", "servicio completo"] | None = None

    source: str | None = None

    source_type: Literal["mem", "government", "media"] | None = None

    source_url: str | None = None


class ResearchReport(BaseModel):

    research_date: str

    records: list[PriceRecord]
