from __future__ import annotations

from textwrap import dedent
from typing import List

from models import ApplicantInsights, ApplicantProfile, MatchResult


def create_application_draft(
    applicant: ApplicantProfile,
    matches: List[MatchResult],
    insights: ApplicantInsights | None = None,
) -> str:
    top_match = matches[0] if matches else None
    target_name = top_match.foundation.name if top_match else "vald stiftelse"

    reasons = "\n".join(f"- {reason}" for reason in (top_match.reasons[:3] if top_match else []))
    documents = applicant.document_flags or ["inga dokument angivna ännu"]
    document_list = "\n".join(f"- {doc}" for doc in documents)
    summary = insights.concise_summary if insights else applicant.description
    missing_info = insights.missing_information if insights else []
    missing_info_block = "\n".join(f"- {item}" for item in missing_info)
    completion_block = f"Följande kan behöva kompletteras:\n{missing_info_block}" if missing_info_block else ""

    return dedent(
        f"""
        Ansökningsutkast
        =================

        Till: {target_name}

        Hej,

        Jag heter {applicant.full_name} och skickar denna ansökan för att söka stöd för {applicant.need_category.lower()}.
        Jag bor i {applicant.municipality}, är {applicant.age} år och beskriver min situation så här:

        {summary}

        Jag söker {applicant.requested_amount_sek:,} SEK för detta behov. Min ungefärliga månadsinkomst är
        {applicant.monthly_income_sek:,} SEK.

        Varför denna stiftelse verkar passa:
        {reasons or '- Matchningen behöver granskas manuellt.'}

        Underlag som just nu finns:
        {document_list}

        {completion_block}

        Jag hoppas att min ansökan kan prövas och kompletterar gärna med ytterligare information vid behov.

        Vänliga hälsningar,
        {applicant.full_name}
        {applicant.email}
        """
    ).strip()
