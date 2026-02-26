from __future__ import annotations

import json
from textwrap import dedent
from typing import Any, Sequence

from config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_REASONING_EFFORT, OPENAI_WEB_MODEL
from models import ApplicantInsights, ApplicantProfile, MatchResult

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - handled gracefully in runtime
    OpenAI = None  # type: ignore[assignment]


def is_openai_available() -> bool:
    return bool(OPENAI_API_KEY and OpenAI is not None)


def _get_client() -> Any:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY saknas. Lägg den i miljön eller i en lokal .env-fil.")
    if OpenAI is None:
        raise RuntimeError("Paketet openai är inte installerat. Kör pip install -r requirements.txt.")
    return OpenAI(api_key=OPENAI_API_KEY)


def _profile_payload(profile: ApplicantProfile) -> dict[str, Any]:
    return {
        "full_name": profile.full_name,
        "email": str(profile.email),
        "municipality": profile.municipality,
        "age": profile.age,
        "applicant_type": profile.applicant_type,
        "need_category": profile.need_category,
        "requested_amount_sek": profile.requested_amount_sek,
        "monthly_income_sek": profile.monthly_income_sek,
        "urgency": profile.urgency,
        "description": profile.description,
        "documents": profile.document_flags,
    }


def extract_applicant_insights(profile: ApplicantProfile) -> ApplicantInsights:
    client = _get_client()
    response = client.responses.parse(
        model=OPENAI_MODEL,
        reasoning={"effort": OPENAI_REASONING_EFFORT},
        input=[
            {
                "role": "system",
                "content": dedent(
                    """
                    Du analyserar ansökningar till svenska stiftelser.
                    Returnera en kort, korrekt och saklig strukturerad analys på svenska.
                    Hitta inga påhittade fakta. Utgå enbart från det användaren uppgett.
                    Extra nyckelord ska vara korta svenska ord eller fraser som kan hjälpa matchning.
                    """
                ).strip(),
            },
            {
                "role": "user",
                "content": json.dumps(_profile_payload(profile), ensure_ascii=False, indent=2),
            },
        ],
        text_format=ApplicantInsights,
    )

    parsed = response.output_parsed
    if parsed is None:
        raise RuntimeError("OpenAI returnerade ingen strukturerad analys.")
    return parsed


def create_application_draft_ai(
    profile: ApplicantProfile,
    matches: Sequence[MatchResult],
    insights: ApplicantInsights | None = None,
) -> str:
    client = _get_client()
    match_payload = [
        {
            "name": match.foundation.name,
            "score": match.score,
            "reasons": match.reasons,
            "warnings": match.warnings,
            "application_url": match.foundation.application_url,
        }
        for match in matches[:3]
    ]

    response = client.responses.create(
        model=OPENAI_MODEL,
        reasoning={"effort": OPENAI_REASONING_EFFORT},
        input=[
            {
                "role": "system",
                "content": dedent(
                    """
                    Du skriver ett första utkast till en svensk stiftelseansökan.
                    Skriv endast utkastet, ingen förklaring före eller efter.
                    Använd ett varmt men professionellt språk.
                    Hitta inte på dokument, diagnoser eller ekonomiska fakta.
                    Om något är osäkert, formulera det försiktigt.
                    Struktur:
                    - Rubrik
                    - Till
                    - Kort presentation
                    - Beskrivning av behovet
                    - Ekonomisk situation
                    - Varför stiftelsen passar
                    - Vilka underlag som finns
                    - Avslutning
                    """
                ).strip(),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "applicant": _profile_payload(profile),
                        "insights": insights.model_dump(mode="json") if insights else None,
                        "top_matches": match_payload,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
            },
        ],
    )

    text = (response.output_text or "").strip()
    if not text:
        raise RuntimeError("OpenAI returnerade inget ansökningsutkast.")
    return text


def research_foundations_on_web(
    profile: ApplicantProfile,
    insights: ApplicantInsights | None = None,
) -> str:
    client = _get_client()
    prompt = dedent(
        f"""
        Hitta 3 till 5 svenska stiftelser, fonder eller stipendieaktörer som kan vara relevanta för denna sökande.
        Fokusera på verkliga svenska källor och ange varför varje alternativ kan passa.
        Inkludera en kort varning om att användaren måste kontrollera kriterier och ansökningslänk manuellt.
        Svara på svenska i markdown med rubriken 'Ytterligare tips från webben'.

        Profil:
        {json.dumps(_profile_payload(profile), ensure_ascii=False, indent=2)}

        Extra tolkning:
        {json.dumps(insights.model_dump(mode='json'), ensure_ascii=False, indent=2) if insights else 'Ingen extra tolkning'}
        """
    ).strip()

    response = client.responses.create(
        model=OPENAI_WEB_MODEL,
        tools=[{"type": "web_search"}],
        input=prompt,
    )
    text = (response.output_text or "").strip()
    if not text:
        raise RuntimeError("Webbresearch gav inget resultat.")
    return text
