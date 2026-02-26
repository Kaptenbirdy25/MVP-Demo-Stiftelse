from __future__ import annotations

import unittest

from matching import match_foundations
from models import ApplicantProfile
from seed import load_foundations


class MatchingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.foundations = load_foundations()

    def test_tandvard_senior_gets_relevant_top_match(self) -> None:
        applicant = ApplicantProfile(
            full_name="Anna Andersson",
            email="anna@example.se",
            municipality="Stockholm",
            age=72,
            applicant_type="senior",
            need_category="tandvård",
            requested_amount_sek=12000,
            monthly_income_sek=15000,
            urgency="Hög",
            description="Jag är pensionär med låg inkomst och behöver tandvård efter en kostnadsberäkning från tandläkaren.",
            has_quote=True,
            has_invoice=False,
            has_medical_certificate=False,
            has_research_summary=False,
            consent=True,
        )

        matches = match_foundations(applicant, self.foundations, top_n=3)
        self.assertGreaterEqual(len(matches), 1)
        self.assertEqual(matches[0].foundation.id, "sf-001")
        self.assertGreater(matches[0].score, 60)

    def test_researcher_gets_research_foundation(self) -> None:
        applicant = ApplicantProfile(
            full_name="Lina Berg",
            email="lina@example.se",
            municipality="Uppsala",
            age=34,
            applicant_type="forskare",
            need_category="forskning",
            requested_amount_sek=150000,
            monthly_income_sek=45000,
            urgency="Medel",
            description="Jag söker finansiering för ett forskningsprojekt inom hälsa med tydlig metod, data och forskningssammanfattning.",
            has_quote=False,
            has_invoice=False,
            has_medical_certificate=False,
            has_research_summary=True,
            consent=True,
        )

        matches = match_foundations(applicant, self.foundations, top_n=3)
        self.assertEqual(matches[0].foundation.id, "sf-006")
        self.assertGreater(matches[0].score, 70)


if __name__ == "__main__":
    unittest.main()
