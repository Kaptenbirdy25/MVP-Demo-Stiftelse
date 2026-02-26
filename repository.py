from __future__ import annotations

import json
from typing import List

from db import get_connection, utc_now
from models import ApplicantProfile, MatchResult


def save_application(applicant: ApplicantProfile) -> int:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO applications (
                full_name,
                email,
                municipality,
                age,
                applicant_type,
                need_category,
                requested_amount_sek,
                monthly_income_sek,
                urgency,
                description,
                has_quote,
                has_invoice,
                has_medical_certificate,
                has_research_summary,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                applicant.full_name,
                applicant.email,
                applicant.municipality,
                applicant.age,
                applicant.applicant_type,
                applicant.need_category,
                applicant.requested_amount_sek,
                applicant.monthly_income_sek,
                applicant.urgency,
                applicant.description,
                int(applicant.has_quote),
                int(applicant.has_invoice),
                int(applicant.has_medical_certificate),
                int(applicant.has_research_summary),
                utc_now(),
            ),
        )
        return int(cursor.lastrowid)


def save_matches(application_id: int, matches: List[MatchResult]) -> None:
    with get_connection() as connection:
        cursor = connection.cursor()
        for match in matches:
            cursor.execute(
                """
                INSERT INTO matches (
                    application_id,
                    foundation_id,
                    foundation_name,
                    score,
                    reasons,
                    warnings,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    application_id,
                    match.foundation.id,
                    match.foundation.name,
                    match.score,
                    json.dumps(match.reasons, ensure_ascii=False),
                    json.dumps(match.warnings, ensure_ascii=False),
                    utc_now(),
                ),
            )


def list_recent_applications(limit: int = 20) -> list[dict]:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT *
            FROM applications
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [dict(row) for row in cursor.fetchall()]


def list_matches_for_application(application_id: int) -> list[dict]:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT *
            FROM matches
            WHERE application_id = ?
            ORDER BY score DESC
            """,
            (application_id,),
        )
        return [dict(row) for row in cursor.fetchall()]
