from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Literal

from pydantic import BaseModel, EmailStr, Field, computed_field


NEED_CATEGORY_VALUES = ["tandvård", "glasögon", "boende", "studier", "forskning", "allmänt_stöd"]
APPLICANT_TYPE_VALUES = ["behövande", "senior", "student", "forskare"]
URGENCY_VALUES = ["Låg", "Medel", "Hög", "Akut"]


class ApplicantProfile(BaseModel):
    full_name: str = Field(min_length=2)
    email: EmailStr
    municipality: str = Field(min_length=2)
    age: int = Field(ge=16, le=120)
    applicant_type: str
    need_category: str
    requested_amount_sek: int = Field(ge=0)
    monthly_income_sek: int = Field(ge=0)
    urgency: str
    description: str = Field(min_length=20)
    has_quote: bool = False
    has_invoice: bool = False
    has_medical_certificate: bool = False
    has_research_summary: bool = False
    consent: bool = True

    @computed_field  # type: ignore[misc]
    @property
    def document_flags(self) -> List[str]:
        documents: List[str] = []
        if self.has_quote:
            documents.append("offert")
        if self.has_invoice:
            documents.append("faktura")
        if self.has_medical_certificate:
            documents.append("medicinskt_intyg")
        if self.has_research_summary:
            documents.append("forskningssammanfattning")
        return documents


class ApplicantInsights(BaseModel):
    concise_summary: str = Field(description="Kort svensk sammanfattning av ärendet.")
    applicant_story: str = Field(description="En sammanhängande svensk beskrivning av sökandens situation.")
    normalized_need_category: Literal[
        "tandvård", "glasögon", "boende", "studier", "forskning", "allmänt_stöd"
    ]
    extra_keywords: List[str] = Field(default_factory=list, description="Nyckelord som kan hjälpa matchning.")
    priority_facts: List[str] = Field(default_factory=list, description="Viktigaste faktorerna i ansökan.")
    missing_information: List[str] = Field(default_factory=list, description="Vad som bör kompletteras.")
    caution_flags: List[str] = Field(default_factory=list, description="Saker som bör kontrolleras manuellt.")
    recommended_tone: str = Field(default="saklig och empatisk")


class Foundation(BaseModel):
    id: str
    name: str
    description: str
    target_groups: List[str]
    categories: List[str]
    geographies: List[str]
    age_min: int = 0
    age_max: int = 120
    monthly_income_cap_sek: int | None = None
    required_documents: List[str] = Field(default_factory=list)
    typical_amount_min_sek: int = 0
    typical_amount_max_sek: int = 0
    application_url: str
    notes: str = ""


@dataclass(slots=True)
class MatchResult:
    foundation: Foundation
    score: int
    reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
