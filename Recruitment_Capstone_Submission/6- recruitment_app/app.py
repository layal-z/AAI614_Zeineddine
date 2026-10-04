"""Local browser interface for the tested four-agent recruitment workflow."""
import copy
import hashlib
import json
import os
import re
from datetime import datetime
from pathlib import Path

import streamlit as st
from engine import RecruitmentEngine, STATUSES, read_document

ROOT = Path(__file__).resolve().parent
CASES = ROOT / 'data' / 'cases'
CASES.mkdir(parents=True, exist_ok=True)

st.set_page_config(page_title='Infinite | Recruitment', page_icon='◎', layout='wide')
st.title('Recruitment workspace')
st.caption('Four specialist agents · GPT-4.1 · Human-reviewed decisions')


def safe_error(error):
    message = re.sub(r'sk-[A-Za-z0-9_-]+', '[hidden key]', str(error))
    st.error(message)


def engine(path):
    return RecruitmentEngine(path, st.session_state.get('openai_key') or os.environ.get('OPENAI_API_KEY'))


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:14]


def parse_lines(value):
    return [line.strip() for line in value.splitlines() if line.strip()]


def mutate(callback, success):
    # Only commit a complete edited case after validation. Model attempt logs
    # may be saved by the tested workflow before generation finishes.
    changed = copy.deepcopy(case)
    try:
        with st.spinner('Working…'):
            callback(changed)
        st.session_state['notice'] = success
        st.rerun()
    except Exception as error:
        safe_error(error)


def confirmed_review(prefix, label):
    return st.checkbox(label, key=prefix + '_confirmed')


def trace_panel(record):
    with st.expander('Execution details'):
        st.json(record.get('trace', record.get('traces', {})))


with st.sidebar:
    st.header('Workspace')
    st.text_input('Reviewer name', key='reviewer_name')
    with st.expander('API settings'):
        st.text_input('OpenAI API key', type='password', key='openai_key',
                      help='Used in this browser session. Never saved in case files.')
        st.caption('Deidentified brief, CV and interview evidence are sent to OpenAI when you generate a draft.')
    if st.button('Open saved demonstration'):
        demo_path = ROOT / 'demo_cases' / 'hr_director_demo.json'
        if demo_path.exists():
            demo_copy = CASES / 'hr_director_demo.json'
            if not demo_copy.exists():
                demo_copy.write_bytes(demo_path.read_bytes())
            st.session_state['switch_case'] = demo_copy.name
            st.session_state['demo_opened'] = True
        else:
            st.error('The demonstration file is missing. Extract the complete app package.')
    files = sorted(CASES.glob('*.json'))
    choices = ['Create or import a case'] + [p.name for p in files]
    switch_to = st.session_state.pop('switch_case', None)
    if switch_to in choices:
        st.session_state['case_selector'] = switch_to
    if st.session_state.get('case_selector') not in choices:
        st.session_state['case_selector'] = choices[0]
    selected_case = st.selectbox('Case', choices, key='case_selector')
    st.session_state['active_case'] = selected_case
    st.caption('Local application · saved cases stay in this app folder')

if selected_case == 'Create or import a case':
    st.subheader('Start a recruitment case')
    create_tab, import_tab = st.tabs(['New vacancy', 'Import saved case'])
    with create_tab:
        with st.form('new_vacancy'):
            title = st.text_input('Case name', placeholder='HR Director — factory')
            brief = st.text_area('Client hiring brief', height=250, placeholder='Paste the hiring need and requirements here.')
            checked = st.checkbox('I checked this brief and want to generate a draft.')
            submitted = st.form_submit_button('Generate role materials', type='primary')
        if submitted:
            if not title.strip() or not checked:
                st.error('Enter a case name and confirm the brief.')
            else:
                name = re.sub(r'[^A-Za-z0-9_-]+', '_', title).strip('_')[:60] or 'vacancy'
                path = CASES / f'{name}_{datetime.now():%Y%m%d_%H%M%S_%f}.json'
                try:
                    with st.spinner('Agent 1 is preparing role materials…'):
                        e = engine(path)
                        generated = e.generate_role(brief.strip())
                        generated['case_name'] = title.strip()
                        e.save(generated)
                    st.session_state['switch_case'] = path.name
                    st.session_state['notice'] = 'Role draft generated. Review and approve it before screening.'
                    st.rerun()
                except Exception as error:
                    safe_error(error)
    with import_tab:
        st.write('Import a copy of your notebook’s saved case. The original file will not be changed.')
        uploaded = st.file_uploader('Saved recruitment case', type=['json'], key='case_import')
        if uploaded and st.button('Import case copy'):
            try:
                if uploaded.size > 10 * 1024 * 1024:
                    raise ValueError('Case file is too large.')
                imported = json.loads(uploaded.getvalue())
                required = {'source_brief', 'hiring_record', 'recruitment_materials'}
                if not isinstance(imported, dict) or not required.issubset(imported):
                    raise ValueError('Choose a recruitment case JSON file from this workflow.')
                # Prevent accidentally importing secrets embedded in an unrelated file.
                if re.search(r'sk-(?:proj-)?[A-Za-z0-9_-]{20,}', json.dumps(imported)):
                    raise ValueError('This file contains an API key. Remove it before importing.')
                path = CASES / f'imported_{datetime.now():%Y%m%d_%H%M%S_%f}.json'
                e = engine(path)
                e.workflow.check_structure(imported['recruitment_materials'], e.workflow.materials_schema)
                e.workflow.check_scorecard(imported['recruitment_materials'], imported['hiring_record'])
                e.save(imported)
                st.session_state['switch_case'] = path.name
                st.session_state['notice'] = 'Case copy imported. Existing approval gates remain in force.'
                st.rerun()
            except Exception as error:
                safe_error(error)
    st.stop()

case_path = CASES / selected_case
try:
    e = engine(case_path)
    case = e.load()
    w = e.workflow
except Exception as error:
    safe_error(error)
    st.stop()

if notice := st.session_state.pop('notice', None):
    st.success(notice)

reviewer = st.session_state.get('reviewer_name', '').strip()
case_key = fingerprint(str(case_path))
with st.sidebar:
    if st.session_state.pop('demo_opened', False):
        st.session_state['view_stage'] = 'Evaluation'
    stage = st.radio('Step', ['Role', 'Screening', 'Interview', 'Evaluation', 'Tracker & checks'], key='view_stage')
    candidate_ids = sorted(case.get('screening_results', {}))
    selected_candidate = st.selectbox('Candidate', candidate_ids + ['Add candidate'], key=case_key + '_candidate')
    if selected_candidate == 'Add candidate':
        candidate_id = st.text_input('New candidate ID', value='Candidate_001', key=case_key + '_new_candidate').strip()
    else:
        candidate_id = selected_candidate
    st.divider()
    st.download_button('Download case backup', json.dumps(case, indent=2, ensure_ascii=False),
                       file_name=selected_case, mime='application/json')

st.subheader(case.get('case_name', 'Recruitment case'))
if stage != 'Role':
    st.info(f'Selected candidate: {candidate_id or "Enter a candidate ID"}')


def gate(function):
    try:
        return function(case, candidate_id) if function != w.get_approved_case else function(case)
    except (ValueError, KeyError, PermissionError) as error:
        st.info(str(error))
        if str(error) == 'The scorecard changed. Screen this candidate again.':
            previous = case.get('screening_results', {}).get(candidate_id, {}).get('approval', {})
            current = case.get('review', {}).get('approval', {})
            if previous and current and all(
                previous.get(key) == current.get(key)
                for key in ('source_version', 'materials_version')
            ):
                st.warning(
                    'The role content still matches, but its approval was recorded again '
                    'after this screening. The saved screening refers to the earlier approval.'
                )
                st.write(
                    'To resume your completed notebook case, import the latest '
                    'recruitment_case_gpt.json as a fresh copy. Open the candidate’s '
                    'Evaluation page directly. Existing approvals are preserved on import.'
                )
            else:
                st.write(
                    'The role approval attached to this screening differs from the '
                    'current role approval. Check that you imported the latest notebook '
                    'case before generating new screening.'
                )
        st.stop()


if stage == 'Role':
    st.write('Review the job description, outreach and selection criteria. Nothing is sent to candidates.')
    review = case.get('review', {})
    materials = copy.deepcopy(review.get('materials', case['recruitment_materials']))
    role_key = case_key + '_role_' + fingerprint({'source': w.review_source_version(case), 'materials': materials})
    with st.expander('Client brief and extracted facts'):
        st.write(case['source_brief'])
        for fact in case['hiring_record']['confirmed_facts']:
            st.markdown('**' + fact['value'] + '**')
            st.caption('Source: ' + fact['source_quote'])
        for question in case['hiring_record']['clarification_questions']:
            st.write('Clarify: ' + question)
    if review.get('approval'):
        st.success('Role materials approved. Saving revised materials requires a new approval and can make downstream records outdated.')
    with st.form(role_key):
        jd = st.text_area('Job description', materials['job_description'], height=350)
        outreach = st.text_area('Candidate message', materials['outreach_message'], height=180)
        keywords = st.text_area('Search keywords — one per line', '\n'.join(materials['search_keywords']), height=100)
        facts = {f['field']: f for f in case['hiring_record']['confirmed_facts']}
        criteria = []
        st.markdown('#### Selection criteria')
        for index, row in enumerate(materials['draft_scorecard']):
            with st.expander(f"{index + 1}. {row['criterion']}"):
                keep = st.checkbox('Keep this criterion', value=True, key=role_key + f'_keep_{index}')
                criterion = st.text_input('Criterion', row['criterion'], key=role_key + f'_criterion_{index}')
                evidence = st.text_area('Evidence to look for', row['evidence_to_look_for'], key=role_key + f'_evidence_{index}')
                refs = st.multiselect('Supporting client requirements', list(facts), default=row['supporting_fact_fields'],
                                      format_func=lambda key: facts[key]['value'], key=role_key + f'_facts_{index}')
                if keep:
                    criteria.append({'criterion': criterion.strip(), 'supporting_fact_fields': refs, 'evidence_to_look_for': evidence.strip()})
        with st.expander('Add a criterion (optional)'):
            extra = st.text_input('New criterion')
            extra_evidence = st.text_area('Evidence for the new criterion')
            extra_refs = st.multiselect('Supporting requirements for the new criterion', list(facts), format_func=lambda key: facts[key]['value'])
        notes = st.text_area('Review notes — one per line', '\n'.join(materials['review_notes']))
        checked = confirmed_review(role_key, 'I reviewed the materials, criteria and supporting requirements.')
        submitted = st.form_submit_button('Save and approve role', type='primary')
    if submitted:
        if extra.strip():
            criteria.append({'criterion': extra.strip(), 'supporting_fact_fields': extra_refs, 'evidence_to_look_for': extra_evidence.strip()})
        edited = {'job_description': jd.strip(), 'outreach_message': outreach.strip(), 'search_keywords': parse_lines(keywords),
                  'draft_scorecard': criteria, 'review_notes': parse_lines(notes)}
        mutate(lambda c: e.approve_role(c, edited, reviewer, checked), 'Role saved and approved.')
    trace_panel(case)

elif stage == 'Screening':
    gate(w.get_approved_case)
    draft = case.get('screening_results', {}).get(candidate_id)
    upload = st.file_uploader('Candidate CV', type=['txt', 'pdf', 'docx'], key=case_key + candidate_id + '_cv_upload')
    try:
        source_text = read_document(upload.name, upload.getvalue()) if upload else (draft or {}).get('candidate_source', '')
    except Exception as error:
        safe_error(error)
        st.stop()
    source_key = case_key + candidate_id + '_cv_' + fingerprint(source_text)
    with st.form(source_key):
        cv_text = st.text_area('Check or paste the CV text', source_text, height=260)
        checked = confirmed_review(source_key, f'I checked that this CV belongs to {candidate_id}.')
        submitted = st.form_submit_button('Screen candidate', type='primary')
    if submitted:
        mutate(lambda c: e.screen(c, candidate_id, cv_text.strip(), checked), 'Screening draft ready for review.')
    if draft:
        reviews = case.get('screening_reviews', {}).get(candidate_id, {})
        valid_review = reviews.get('approval') and reviews.get('draft_version') == w.review_fingerprint(draft)
        if valid_review:
            st.success('Screening review approved.')
        rows = reviews.get('assessments', draft['assessments']) if reviews.get('draft_version') == w.review_fingerprint(draft) else draft['assessments']
        source = w.candidate_evidence(candidate_id, draft['candidate_source'])
        evidence = {item['id']: item['text'] for item in source['evidence']}
        key = case_key + candidate_id + '_screen_review_' + fingerprint(rows)
        edited = []
        with st.form(key):
            for index, row in enumerate(rows):
                with st.expander(row['criterion']):
                    status = st.selectbox('Assessment', STATUSES, index=STATUSES.index(row['status']), key=key + f'_status_{index}')
                    refs = st.multiselect('Supporting evidence', list(evidence), default=[q['id'] for q in row['evidence']],
                                          format_func=lambda ref: ref + ': ' + evidence[ref], key=key + f'_refs_{index}')
                    explanation = st.text_area('Explanation', row['explanation'], key=key + f'_explanation_{index}')
                    edited.append({'criterion_id': row['criterion_id'], 'criterion': row['criterion'], 'status': status,
                                   'evidence_ids': refs, 'explanation': explanation.strip()})
            checked = confirmed_review(key, 'I reviewed all screening judgments and citations.')
            submitted = st.form_submit_button('Save and approve screening', type='primary')
        if submitted:
            mutate(lambda c: e.approve_screening(c, candidate_id, edited, reviewer, checked), 'Screening saved and approved.')
        trace_panel(draft)

elif stage == 'Interview':
    gate(w.get_reviewed_screening)
    if st.button('Prepare interview plan', type='primary'):
        mutate(lambda c: e.plan(c, candidate_id), 'Interview plan ready for review.')
    plan = case.get('interview_plans', {}).get(candidate_id)
    if plan:
        if plan.get('approval'):
            st.success('Interview plan approved.')
        key = case_key + candidate_id + '_plan_' + fingerprint(plan)
        edited = []
        with st.form(key):
            for index, topic in enumerate(plan['plan']):
                with st.expander(topic['criterion']):
                    reason = st.text_area('Reason for follow-up', topic['reason'], key=key + f'_reason_{index}')
                    questions = []
                    for j in range(2):
                        existing = topic['questions'][j] if j < len(topic['questions']) else {}
                        label = 'Question' if j == 0 else 'Additional question (optional)'
                        question = st.text_area(label, existing.get('question', ''), key=key + f'_q_{index}_{j}')
                        purpose = st.text_input('Purpose', existing.get('purpose', ''), key=key + f'_purpose_{index}_{j}')
                        signals = st.text_area('Answer signals — one per line', '\n'.join(existing.get('listen_for', [])), key=key + f'_signals_{index}_{j}')
                        routes = ['professional_interview', 'recruiter_confirmation']
                        route = st.selectbox('Asked by', routes, index=routes.index(existing.get('route', routes[0])),
                                              format_func=lambda r: 'Professional interview' if r == routes[0] else 'Recruiter confirmation', key=key + f'_route_{index}_{j}')
                        if question.strip():
                            questions.append({'question': question.strip(), 'purpose': purpose.strip(), 'listen_for': parse_lines(signals), 'route': route})
                    edited.append({'criterion_id': topic['criterion_id'], 'criterion': topic['criterion'], 'reason': reason.strip(), 'questions': questions})
            notes = st.text_area('Interviewer notes — one per line', '\n'.join(plan['interviewer_notes']))
            checked = confirmed_review(key, 'I reviewed the questions and approve this plan.')
            submitted = st.form_submit_button('Save and approve interview plan', type='primary')
        if submitted:
            mutate(lambda c: e.approve_plan(c, candidate_id, edited, parse_lines(notes), reviewer, checked), 'Interview plan saved and approved.')
        trace_panel(plan)
        try:
            w.get_approved_interview_plan(case, candidate_id)
        except (PermissionError, ValueError, KeyError):
            st.info('Approve the plan before adding interview evidence.')
        else:
            st.markdown('#### Interview evidence')
            stored = case.get('interview_records', {}).get(candidate_id, {})
            transcript_upload = st.file_uploader('Transcript or interview notes', type=['txt', 'pdf', 'docx'], key=case_key + candidate_id + '_transcript_upload')
            try:
                text = read_document(transcript_upload.name, transcript_upload.getvalue()) if transcript_upload else stored.get('source_text', '')
            except Exception as error:
                safe_error(error)
                st.stop()
            key = case_key + candidate_id + '_notes_' + fingerprint(text)
            with st.form(key):
                text = st.text_area('Check or paste interview text', text, height=300)
                types = ['actual', 'simulated']
                source_type = st.selectbox('Interview source', types, index=types.index(stored.get('source_type', 'actual')),
                                           format_func=lambda t: 'Actual interview' if t == 'actual' else 'Simulated course demonstration')
                checked = confirmed_review(key, f'I checked the interview text and source label for {candidate_id}.')
                submitted = st.form_submit_button('Save reviewed interview evidence', type='primary')
            if submitted:
                mutate(lambda c: e.save_notes(c, candidate_id, text, source_type, reviewer, checked), 'Reviewed interview evidence saved.')

elif stage == 'Evaluation':
    context = gate(w.read_evaluation_context)
    if st.button('Generate evaluation', type='primary'):
        mutate(lambda c: e.evaluate(c, candidate_id), 'Evaluation draft ready for human review.')
    draft = case.get('interview_evaluations', {}).get(candidate_id)
    if draft:
        if draft['context_version'] != w.review_fingerprint(context):
            st.warning('This evaluation uses outdated source records. Generate a new evaluation before reviewing.')
            st.stop()
        review = case.get('evaluation_reviews', {}).get(candidate_id, {})
        current = review if review.get('draft_version') == w.review_fingerprint(draft) else draft
        if review.get('approval') and current is review:
            st.success('Final report approved. Tracker confirmation remains separate.')
        evidence = {r['id']: r for r in context['evidence']}
        key = case_key + candidate_id + '_eval_' + fingerprint(current)
        edited = []
        with st.form(key):
            for index, row in enumerate(current['assessments']):
                with st.expander(row['criterion']):
                    status = st.selectbox('Assessment', STATUSES, index=STATUSES.index(row['status']), key=key + f'_status_{index}')
                    refs = st.multiselect('Supporting evidence', list(evidence), default=[q['id'] for q in row['evidence']],
                                          format_func=lambda ref: f"{ref} [{evidence[ref]['source']}]: {evidence[ref]['text']}", key=key + f'_refs_{index}')
                    explanation = st.text_area('Explanation', row['explanation'], key=key + f'_explanation_{index}')
                    questions = st.text_area('Unresolved questions — one per line', '\n'.join(row['open_questions']), key=key + f'_questions_{index}')
                    edited.append({'criterion_id': row['criterion_id'], 'criterion': row['criterion'], 'status': status,
                                   'evidence_ids': refs, 'explanation': explanation.strip(), 'open_questions': parse_lines(questions)})
            summary = st.text_area('Client summary', current['client_summary'], height=180)
            next_step = st.text_area('Proposed next step', current['proposed_next_step'])
            checked = confirmed_review(key, 'I checked every assessment, citation and the client summary.')
            submitted = st.form_submit_button('Save and approve report', type='primary')
        if submitted:
            mutate(lambda c: e.approve_evaluation(c, candidate_id, edited, summary, next_step, reviewer, checked), 'Report saved and approved.')
        trace_panel(draft)

elif stage == 'Tracker & checks':
    approved = gate(w.get_approved_evaluation)
    key = case_key + candidate_id + '_tracker_' + fingerprint(approved['approval'])
    with st.form(key):
        options = ['follow_up_required', 'ready_for_hiring_manager_review', 'on_hold']
        labels = ['Follow-up required', 'Ready for hiring-manager review', 'On hold']
        tracker_stage = st.selectbox('Recruitment stage', options, format_func=lambda s: labels[options.index(s)])
        action = st.text_area('Next action', approved['proposed_next_step'])
        checked = confirmed_review(key, f'I approve this tracker update for {candidate_id}.')
        submitted = st.form_submit_button('Approve tracker update', type='primary')
    if submitted:
        mutate(lambda c: e.tracker(c, candidate_id, tracker_stage, action, reviewer, checked), 'Tracker update saved.')
    if entry := case.get('tracker', {}).get(candidate_id):
        st.write('Saved tracker entry')
        st.json(entry)
    st.markdown('#### Report checks')
    st.json(e.quality(case, candidate_id))
    st.caption('Quotation checks verify exact source text, not whether it supports the interpretation.')
    if st.button('Run approval safeguard checks'):
        st.json(e.safeguards(case, candidate_id))
    st.download_button('Download approved report', e.report_markdown(case, candidate_id), file_name=candidate_id + '_report.md', mime='text/markdown')
