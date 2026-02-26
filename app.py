from __future__ import annotations

from typing import Dict, List, Tuple

import streamlit as st

from config import (
    APP_SUBTITLE,
    APP_TITLE,
    ENABLE_OPENAI_BY_DEFAULT,
    ENABLE_WEB_RESEARCH_BY_DEFAULT,
    OPENAI_MODEL,
    OPENAI_WEB_MODEL,
    TOP_MATCH_COUNT,
)
from db import ensure_db
from drafting import create_application_draft
from matching import match_foundations
from models import ApplicantInsights, ApplicantProfile, MatchResult
from openai_service import (
    create_application_draft_ai,
    extract_applicant_insights,
    is_openai_available,
    research_foundations_on_web,
)
from repository import save_application, save_matches
from seed import load_foundations

st.set_page_config(page_title=APP_TITLE, page_icon='📄', layout='centered')

ensure_db()
FOUNDATIONS = load_foundations()
OPENAI_READY = is_openai_available()

SESSION_DEFAULTS = {
    'submitted_profile': None,
    'matches': [],
    'application_id': None,
    'draft': '',
    'ai_insights': None,
    'ai_enabled': False,
    'web_research': '',
    'ai_error': '',
}
for key, value in SESSION_DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


def foundation_counts() -> Dict[str, int]:
    categories: Dict[str, int] = {}
    for foundation in FOUNDATIONS:
        for category in foundation.categories:
            categories[category] = categories.get(category, 0) + 1
    return categories


def validate_form(
    full_name: str,
    email: str,
    municipality: str,
    description: str,
    consent: bool,
) -> Tuple[bool, str]:
    if len(full_name.strip()) < 2:
        return False, 'Fyll i namn.'
    if '@' not in email or len(email.strip()) < 5:
        return False, 'Fyll i en giltig e-postadress.'
    if len(municipality.strip()) < 2:
        return False, 'Fyll i kommun eller ort.'
    if len(description.strip()) < 20:
        return False, 'Beskriv din situation med minst 20 tecken.'
    if not consent:
        return False, 'Du behöver godkänna samtycket för att fortsätta i MVP:n.'
    return True, ''


def render_header() -> None:
    counts = foundation_counts()
    st.title(APP_TITLE)
    st.caption(APP_SUBTITLE)
    st.write(
        'En enkel MVP med tre steg: fyll i formuläret, se de bästa stiftelsematchningarna och visa ett bonusläge för stiftelsens handläggning.'
    )
    col1, col2, col3 = st.columns(3)
    col1.metric('Stiftelser i demo', len(FOUNDATIONS))
    col2.metric('Kategorier', len(counts))
    col3.metric('AI-stöd', 'På' if OPENAI_READY else 'Av')
    with st.expander('Teknisk info', expanded=False):
        st.write('Den lokala matchningen kör alltid mot repo:ts egen stiftelsekatalog.')
        st.write(f'Textmodell: `{OPENAI_MODEL}`')
        st.write(f'Webbmodell: `{OPENAI_WEB_MODEL}`')
        if not OPENAI_READY:
            st.info('Lägg till OPENAI_API_KEY i .env om du vill aktivera AI-tolkning och bättre utkast.')


def submit_application(profile: ApplicantProfile, use_ai: bool, use_web_research: bool) -> None:
    ai_error = ''
    insights: ApplicantInsights | None = None
    extra_keywords: list[str] = []

    if use_ai and OPENAI_READY:
        try:
            insights = extract_applicant_insights(profile)
            extra_keywords = insights.extra_keywords
        except Exception as exc:
            ai_error = f'AI-tolkningen kunde inte köras: {exc}'

    matches = match_foundations(profile, FOUNDATIONS, top_n=TOP_MATCH_COUNT, extra_keywords=extra_keywords)
    application_id = save_application(profile)
    save_matches(application_id, matches)

    if use_ai and OPENAI_READY:
        try:
            draft = create_application_draft_ai(profile, matches, insights)
        except Exception as exc:
            ai_error = (ai_error + "\n" if ai_error else "") + f"AI-utkastet kunde inte köras: {exc}"
            draft = create_application_draft(profile, matches, insights)
    else:
        draft = create_application_draft(profile, matches, insights)

    web_research = ''
    if use_ai and use_web_research and OPENAI_READY:
        try:
            web_research = research_foundations_on_web(profile, insights)
        except Exception as exc:
            ai_error = (ai_error + "\n" if ai_error else "") + f"Webbresearch kunde inte köras: {exc}"

    st.session_state.submitted_profile = profile
    st.session_state.matches = matches
    st.session_state.application_id = application_id
    st.session_state.draft = draft
    st.session_state.ai_insights = insights
    st.session_state.ai_enabled = bool(use_ai and OPENAI_READY)
    st.session_state.web_research = web_research
    st.session_state.ai_error = ai_error


def render_input_tab() -> None:
    st.subheader('1. Inmatning')
    st.write('Fyll i ett kort formulär. Resultatet visas i nästa flik.')

    with st.form('application_form', clear_on_submit=False):
        full_name = st.text_input('Namn', placeholder='Anna Andersson')
        email = st.text_input('E-post', placeholder='anna@example.se')
        municipality = st.text_input('Kommun eller ort', placeholder='Göteborg')

        col1, col2 = st.columns(2)
        with col1:
            age = st.number_input('Ålder', min_value=16, max_value=120, value=68, step=1)
            applicant_type = st.selectbox('Jag söker som', ['behövande', 'senior', 'student', 'forskare'])
            need_category = st.selectbox(
                'Vad söker du stöd för?',
                ['tandvård', 'glasögon', 'boende', 'studier', 'forskning', 'allmänt_stöd'],
            )
        with col2:
            requested_amount_sek = st.number_input(
                'Önskat belopp (SEK)', min_value=0, max_value=500_000, value=12000, step=1000
            )
            monthly_income_sek = st.number_input(
                'Månadsinkomst ungefär (SEK)', min_value=0, max_value=300_000, value=16000, step=1000
            )
            urgency = st.select_slider('Hur brådskande är behovet?', options=['Låg', 'Medel', 'Hög', 'Akut'])

        description = st.text_area(
            'Beskriv din situation',
            placeholder='Exempel: Jag är pensionär med låg inkomst och behöver hjälp med tandvård efter en kostnadsberäkning från tandläkaren.',
            height=160,
        )

        st.markdown('**Underlag som redan finns**')
        doc_col1, doc_col2 = st.columns(2)
        with doc_col1:
            has_quote = st.checkbox('Offert eller kostnadsförslag')
            has_invoice = st.checkbox('Faktura')
        with doc_col2:
            has_medical_certificate = st.checkbox('Medicinskt intyg')
            has_research_summary = st.checkbox('Forskningssammanfattning')

        with st.expander('Valfria smarta funktioner', expanded=False):
            ai_default = OPENAI_READY and ENABLE_OPENAI_BY_DEFAULT
            web_default = OPENAI_READY and ENABLE_WEB_RESEARCH_BY_DEFAULT
            use_ai = st.checkbox(
                'Använd OpenAI för smartare tolkning och bättre utkast',
                value=ai_default,
                disabled=not OPENAI_READY,
            )
            use_web_research = st.checkbox(
                'Sök även efter fler stiftelser på webben',
                value=web_default,
                disabled=not (OPENAI_READY and use_ai),
            )
        consent = st.checkbox('Jag godkänner att uppgifterna används för att hitta relevanta stiftelser.', value=True)

        submitted = st.form_submit_button('Hitta stiftelser', width='stretch')

    if not submitted:
        with st.container(border=True):
            st.markdown('**Tips för en bra MVP-demo**')
            st.write('Skriv gärna vem du är, varför du behöver stöd nu och om du redan har offert eller intyg.')
        return

    ok, message = validate_form(full_name, email, municipality, description, consent)
    if not ok:
        st.error(message)
        return

    try:
        profile = ApplicantProfile(
            full_name=full_name.strip(),
            email=email.strip(),
            municipality=municipality.strip(),
            age=int(age),
            applicant_type=applicant_type,
            need_category=need_category,
            requested_amount_sek=int(requested_amount_sek),
            monthly_income_sek=int(monthly_income_sek),
            urgency=urgency,
            description=description.strip(),
            has_quote=has_quote,
            has_invoice=has_invoice,
            has_medical_certificate=has_medical_certificate,
            has_research_summary=has_research_summary,
            consent=consent,
        )
    except Exception as exc:
        st.error(f'Kunde inte tolka formuläret: {exc}')
        return

    submit_application(profile, bool(use_ai), bool(use_web_research))
    st.success('Klart! Gå till fliken Resultat för att se dina matchningar och ansökningsutkastet.')


def render_match_card(match: MatchResult, rank: int) -> None:
    with st.container(border=True):
        top_row_left, top_row_right = st.columns([4, 1])
        top_row_left.markdown(f'### {rank}. {match.foundation.name}')
        top_row_right.metric('Match', f'{match.score}/100')
        st.write(match.foundation.description)
        st.markdown(f'**Ansökningslänk:** {match.foundation.application_url}')
        if match.reasons:
            st.markdown('**Varför den passar**')
            for reason in match.reasons[:4]:
                st.write(f'- {reason}')
        if match.warnings:
            st.markdown('**Det här saknas eller behöver kollas**')
            for warning in match.warnings[:4]:
                st.write(f'- {warning}')
        next_step = 'Öppna stiftelsen och anpassa utkastet.' if match.score >= 60 else 'Kontrollera kriterier och komplettera innan du går vidare.'
        st.info(f'Nästa steg: {next_step}')


def render_results_tab() -> None:
    st.subheader('2. Resultat')
    matches: List[MatchResult] = st.session_state.matches
    if not matches:
        st.info('Fyll i inmatningsfliken först.')
        return

    profile: ApplicantProfile = st.session_state.submitted_profile
    insights: ApplicantInsights | None = st.session_state.ai_insights

    summary_col1, summary_col2, summary_col3 = st.columns(3)
    summary_col1.metric('Sökande', profile.full_name)
    summary_col2.metric('Behov', profile.need_category)
    summary_col3.metric('Belopp', f'{profile.requested_amount_sek:,} SEK')

    if st.session_state.ai_error:
        st.warning(st.session_state.ai_error)

    if insights is not None:
        with st.expander('AI-tolkning', expanded=False):
            st.write(insights.concise_summary)
            if insights.priority_facts:
                st.markdown('**Viktiga fakta**')
                for item in insights.priority_facts:
                    st.write(f'- {item}')
            if insights.missing_information:
                st.markdown('**Bra att komplettera**')
                for item in insights.missing_information:
                    st.write(f'- {item}')

    st.markdown('### Dina tre bästa stiftelser')
    for index, match in enumerate(matches, start=1):
        render_match_card(match, rank=index)

    if st.session_state.web_research:
        with st.expander('Extra träffar från webben', expanded=False):
            st.markdown(st.session_state.web_research)
            st.info('Kontrollera alltid riktiga kriterier, deadlines och ansökningslänkar manuellt.')

    st.markdown('### Första utkast till ansökan')
    st.text_area('Redigerbart utkast', value=st.session_state.draft, height=340)


def bonus_status(match: MatchResult) -> Tuple[str, str]:
    warnings_text = ' '.join(match.warnings).lower()
    if match.score >= 60 and 'saknade dokument' not in warnings_text:
        return 'Redo för manuell granskning', 'Ansökan ser tillräckligt komplett ut för att gå vidare.'
    if 'saknade dokument' in warnings_text:
        return 'Saknar underlag', 'Vissa obligatoriska bilagor eller intyg behöver kompletteras.'
    if match.score < 40:
        return 'Troligen ej behörig', 'Grundkriterierna verkar svaga för den här stiftelsen.'
    return 'Behöver manuell kontroll', 'Det finns matchning, men handläggaren bör kontrollera kriterierna manuellt.'


def render_bonus_tab() -> None:
    st.subheader('3. Bonus – stiftelsevy')
    matches: List[MatchResult] = st.session_state.matches
    if not matches:
        st.info('Bonusvyn fylls när du har skickat in en ansökan i första fliken.')
        return

    st.write(
        'Den här bonusvyn visar ett enkelt beslutsstöd för stiftelser. Bedömningen bygger på strukturerade formulärfält och regelkontroller, inte på att AI läser hela ansökan.'
    )

    rows = []
    for match in matches:
        status, note = bonus_status(match)
        rows.append(
            {
                'Stiftelse': match.foundation.name,
                'Status': status,
                'Poäng': match.score,
                'Målgrupp': 'Ja' if any('målgrupp' in reason.lower() for reason in match.reasons) else 'Osäkert',
                'Geografi': 'Ja' if any('geografi' in reason.lower() for reason in match.reasons) else 'Osäkert',
                'Ändamål': 'Ja' if any('ändamål' in reason.lower() or 'beskrivningen antyder' in reason.lower() for reason in match.reasons) else 'Osäkert',
                'Underlag': 'Saknas' if any('saknade dokument' in warning.lower() for warning in match.warnings) else 'OK',
                'Handläggarnotering': note,
            }
        )

    st.dataframe(rows, width='stretch', hide_index=True)

    selected_name = st.selectbox('Visa detaljbedömning för stiftelse', [match.foundation.name for match in matches])
    selected_match = next(match for match in matches if match.foundation.name == selected_name)
    status, note = bonus_status(selected_match)

    with st.container(border=True):
        st.markdown(f'### {selected_match.foundation.name}')
        st.metric('Förhandsstatus', status)
        st.write(note)
        st.markdown('**Regelbaserad kontroll**')
        checks = [
            ('Målgrupp', 'Uppfyllt' if any('målgrupp' in reason.lower() for reason in selected_match.reasons) else 'Kontrollera'),
            ('Geografi', 'Uppfyllt' if any('geografi' in reason.lower() for reason in selected_match.reasons) else 'Kontrollera'),
            ('Ändamål', 'Uppfyllt' if any('ändamål' in reason.lower() or 'beskrivningen antyder' in reason.lower() for reason in selected_match.reasons) else 'Kontrollera'),
            ('Beloppsnivå', 'Uppfyllt' if any('beloppet' in reason.lower() for reason in selected_match.reasons) else 'Kontrollera'),
            ('Obligatoriska underlag', 'Saknas' if any('saknade dokument' in warning.lower() for warning in selected_match.warnings) else 'OK'),
        ]
        for label, value in checks:
            st.write(f'- **{label}:** {value}')
        if selected_match.warnings:
            st.markdown('**Flaggor för handläggare**')
            for warning in selected_match.warnings:
                st.write(f'- {warning}')
        st.info('Detta bonusläge är tänkt som ett AI-snålt och förklarbart beslutsstöd för första sortering.')


render_header()
input_tab, results_tab, bonus_tab = st.tabs(['Inmatning', 'Resultat', 'Bonus'])
with input_tab:
    render_input_tab()
with results_tab:
    render_results_tab()
with bonus_tab:
    render_bonus_tab()
