from __future__ import annotations

from typing import Iterable, List, Sequence

from models import ApplicantProfile, Foundation, MatchResult


KEYWORDS_BY_CATEGORY = {
    "tandvård": ["tand", "tandvård", "implantat", "protes", "bett"],
    "glasögon": ["glasögon", "syn", "linser"],
    "boende": ["hyra", "boende", "bostad"],
    "studier": ["studie", "student", "utbildning", "kurs"],
    "forskning": ["forskning", "forskningsprojekt", "studie", "data", "metod"],
    "allmänt_stöd": ["ekonomi", "stöd", "bidrag", "behövande"],
}


APPLICANT_GROUP_ALIASES = {
    "behövande": ["behövande", "privatperson", "senior"],
    "senior": ["senior", "pensionär", "behövande"],
    "student": ["student"],
    "forskare": ["forskare"],
}


URGENCY_BONUS = {
    "Låg": 0,
    "Medel": 2,
    "Hög": 4,
    "Akut": 6,
}


MISSING_DOC_WARNING = "Vissa dokument saknas för att ansökan ska bli stark."


def _normalize(text: str) -> str:
    return text.strip().lower()


def _contains_any(description: str, keywords: Iterable[str]) -> bool:
    normalized = _normalize(description)
    return any(_normalize(keyword) in normalized for keyword in keywords if keyword)


def _keyword_boost(foundation: Foundation, extra_keywords: Sequence[str] | None) -> tuple[int, list[str]]:
    if not extra_keywords:
        return 0, []

    haystack = " ".join(
        [
            foundation.description,
            foundation.notes,
            " ".join(foundation.categories),
            " ".join(foundation.target_groups),
        ]
    ).lower()

    matched_keywords = []
    for keyword in extra_keywords:
        normalized = _normalize(keyword)
        if normalized and normalized not in matched_keywords and normalized in haystack:
            matched_keywords.append(normalized)

    if not matched_keywords:
        return 0, []

    boost = min(10, len(matched_keywords) * 3)
    reasons = [f"AI-tolkningen hittade relevanta nyckelord: {', '.join(matched_keywords[:4])}."]
    return boost, reasons


def score_foundation(
    applicant: ApplicantProfile,
    foundation: Foundation,
    extra_keywords: Sequence[str] | None = None,
) -> MatchResult:
    score = 0
    reasons: List[str] = []
    warnings: List[str] = []

    applicant_type = _normalize(applicant.applicant_type)
    need_category = _normalize(applicant.need_category)
    municipality = _normalize(applicant.municipality)

    aliases = APPLICANT_GROUP_ALIASES.get(applicant_type, [applicant_type])
    if any(alias in map(_normalize, foundation.target_groups) for alias in aliases):
        score += 25
        reasons.append("Rätt målgrupp för stiftelsen.")

    if need_category in map(_normalize, foundation.categories):
        score += 30
        reasons.append("Stiftelsens ändamål matchar behovet väl.")
    else:
        keywords = KEYWORDS_BY_CATEGORY.get(need_category, [])
        if keywords and _contains_any(foundation.description, keywords):
            score += 12
            reasons.append("Beskrivningen antyder att stiftelsen kan passa behovet.")

    geographies = list(map(_normalize, foundation.geographies))
    if "hela sverige" in geographies or municipality in geographies:
        score += 15
        reasons.append("Geografin matchar.")
    elif "regional" in geographies:
        score += 8
        reasons.append("Regionalt stöd kan vara möjligt.")

    if foundation.age_min <= applicant.age <= foundation.age_max:
        score += 10
        reasons.append("Ålderskraven ser ut att passa.")
    else:
        warnings.append("Åldern ligger utanför normal målgrupp.")
        score -= 15

    if foundation.monthly_income_cap_sek is None:
        score += 4
    elif applicant.monthly_income_sek <= foundation.monthly_income_cap_sek:
        score += 12
        reasons.append("Inkomstnivån verkar ligga inom kriterierna.")
    else:
        warnings.append("Inkomstnivån kan ligga över stiftelsens gräns.")
        score -= 8

    if foundation.typical_amount_min_sek <= applicant.requested_amount_sek <= foundation.typical_amount_max_sek:
        score += 10
        reasons.append("Beloppet ligger nära stiftelsens normala nivå.")
    elif applicant.requested_amount_sek < foundation.typical_amount_min_sek:
        score += 4
    else:
        warnings.append("Beloppet är högre än stiftelsens normala spann.")
        score -= 6

    if foundation.required_documents:
        missing_docs = [doc for doc in foundation.required_documents if doc not in applicant.document_flags]
        if missing_docs:
            warnings.append(f"Saknade dokument: {', '.join(missing_docs)}.")
            warnings.append(MISSING_DOC_WARNING)
            score -= 5 * len(missing_docs)
        else:
            score += 8
            reasons.append("Nödvändiga underlag verkar finnas.")

    score += URGENCY_BONUS.get(applicant.urgency, 0)

    if _contains_any(applicant.description, KEYWORDS_BY_CATEGORY.get(need_category, [])):
        score += 4

    keyword_score, keyword_reasons = _keyword_boost(foundation, extra_keywords)
    score += keyword_score
    reasons.extend(keyword_reasons)

    score = max(score, 0)
    return MatchResult(foundation=foundation, score=score, reasons=reasons, warnings=warnings)



def match_foundations(
    applicant: ApplicantProfile,
    foundations: List[Foundation],
    top_n: int = 5,
    extra_keywords: Sequence[str] | None = None,
) -> List[MatchResult]:
    matches = [score_foundation(applicant, foundation, extra_keywords=extra_keywords) for foundation in foundations]
    matches.sort(key=lambda item: item.score, reverse=True)
    return matches[:top_n]
