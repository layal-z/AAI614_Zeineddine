"""Offline integration tests. No API key, real candidate data or paid calls."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS

from engine import RecruitmentEngine

BRIEF = 'Role: HR Director. Minimum ten years. Personnel affairs.'
CV = 'HR Manager 2011 - 2023\nManaged personnel affairs and payroll.'
CID = 'Candidate_002'


class FakeAPI:
    """Fixed synthetic responses exercise API parsing and orchestration only."""
    def __init__(self):
        self.responses = NS(create=self.response)
        self.chat = NS(completions=NS(create=self.chat_response))
        self.calls = []

    def response(self, **kwargs):
        self.calls.append(kwargs)
        schema = kwargs['text']['format']['schema']
        props = schema['properties']
        if 'confirmed_facts' in props:
            result = {'confirmed_facts': [
                {'field':'role','value':'HR Director','source_quote':'HR Director'},
                {'field':'experience','value':'Minimum ten years','source_quote':'Minimum ten years'},
                {'field':'responsibility_personnel','value':'Personnel affairs','source_quote':'Personnel affairs'}],
                'clarification_questions':[], 'conflicts':[], 'suggestions_for_review':[]}
        elif 'job_description' in props:
            result = {'job_description':'HR Director role with personnel affairs.', 'outreach_message':'Are you interested?',
                      'search_keywords':['HR Director'], 'draft_scorecard':[
                        {'criterion':'Minimum ten years','supporting_fact_fields':['F002'],'evidence_to_look_for':'Dated HR roles'},
                        {'criterion':'Personnel affairs','supporting_fact_fields':['F003'],'evidence_to_look_for':'Personnel responsibilities'}], 'review_notes':[]}
        else:
            result = {'assessments':{
                'C001':{'status':'demonstrated','basis':'cv_only','evidence_ids':['E001'],'explanation':'The synthetic dated role supports duration.','open_questions':[]},
                'C002':{'status':'demonstrated','basis':'cv_and_interview','evidence_ids':['E002','I001'],'explanation':'Synthetic personnel responsibilities are stated.','open_questions':[]}},
                'client_summary':'Synthetic test candidate supports the test criteria.', 'proposed_next_step':'Human review.'}
        return NS(status='completed',output_text=json.dumps(result),usage=NS(input_tokens=10,output_tokens=10))

    def chat_response(self, **kwargs):
        self.calls.append(kwargs)
        if kwargs.get('tools'):
            name = kwargs['tools'][0]['function']['name']
            message = NS(content=None,refusal=None,tool_calls=[NS(id='test_call',type='function',function=NS(name=name,arguments=json.dumps({'candidate_id':CID})))])
            reason = 'tool_calls'
        else:
            # Assert internal tool messages were converted to valid API messages.
            tool_messages = [m for m in kwargs['messages'] if m['role']=='tool']
            assert tool_messages and all(m.get('tool_call_id')=='test_call' for m in tool_messages)
            assert all('tool_name' not in m for m in kwargs['messages'])
            properties = kwargs['response_format']['json_schema']['schema']['properties']
            if 'plan' in properties:
                result = {'plan':{
                    'C001':{'reason':'Explore role scope.','questions':[{'question':'Describe your role.','purpose':'Clarify scope.','listen_for':['Personal contribution'],'route':'professional_interview'}]},
                    'C002':{'reason':'Explore personnel work.','questions':[{'question':'Describe personnel work.','purpose':'Clarify contribution.','listen_for':['Specific example'],'route':'professional_interview'}]}}, 'interviewer_notes':['Record actual answers.']}
            else:
                result = {'assessments':{
                    'C001':{'status':'demonstrated','evidence_ids':['E001'],'explanation':'Dated synthetic HR role.'},
                    'C002':{'status':'demonstrated','evidence_ids':['E002'],'explanation':'Synthetic personnel responsibilities.'}}}
            message = NS(content=json.dumps(result),refusal=None,tool_calls=[])
            reason = 'stop'
        return NS(choices=[NS(message=message,finish_reason=reason)],usage=NS(prompt_tokens=10,completion_tokens=10))


def completed_case(engine):
    engine.workflow.api_client = FakeAPI()
    case = engine.generate_role(BRIEF)
    engine.approve_role(case,copy.deepcopy(case['recruitment_materials']),'Test reviewer',True)
    engine.screen(case,CID,CV,True)
    rows = [{**r,'evidence_ids':[q['id'] for q in r['evidence']]} for r in case['screening_results'][CID]['assessments']]
    engine.approve_screening(case,CID,rows,'Test reviewer',True)
    engine.plan(case,CID)
    plan = case['interview_plans'][CID]
    engine.approve_plan(case,CID,copy.deepcopy(plan['plan']),plan['interviewer_notes'],'Test reviewer',True)
    engine.save_notes(case,CID,'Candidate: I managed payroll.','simulated','Test reviewer',True)
    engine.evaluate(case,CID)
    draft = case['interview_evaluations'][CID]
    rows = [{**r,'evidence_ids':[q['id'] for q in r['evidence']]} for r in draft['assessments']]
    engine.approve_evaluation(case,CID,rows,draft['client_summary'],draft['proposed_next_step'],'Test reviewer',True)
    return case


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.engine = RecruitmentEngine(Path(self.directory.name)/'case.json')
        self.case = completed_case(self.engine)

    def tearDown(self):
        self.directory.cleanup()

    def test_full_workflow_real_mcp_and_persistence(self):
        report = self.engine.workflow.get_approved_evaluation(self.case,CID)
        self.assertEqual(report['candidate_id'],CID)
        self.assertEqual(self.engine.load(),self.case)
        self.assertEqual(len(self.engine.workflow.MCP_CALL_HISTORY),3)
        self.assertTrue(self.engine.quality(self.case,CID)['criterion_coverage_passed'])
        self.assertEqual(self.engine.quality(self.case,CID)['exact_source_quotations'],3)
        entry = self.engine.tracker(self.case,CID,'follow_up_required','Ask follow-up.','Test reviewer',True)
        self.assertEqual(entry['candidate_id'],CID)
        self.engine.tracker(self.case,CID,'follow_up_required','Ask follow-up.','Test reviewer',True)
        self.assertEqual(len(self.case['tracker_history']),1)
        self.assertIn('Reviewed by: Test reviewer',self.engine.report_markdown(self.case,CID))
        self.assertEqual(self.engine.safeguards(self.case,CID)['passed'],8)

    def test_changed_sources_and_missing_approvals_blocked(self):
        w = self.engine.workflow
        mutations = [
            lambda c: c['review'].update(approval=None),
            lambda c: c['review']['materials']['draft_scorecard'][0].update(criterion='Changed'),
            lambda c: c['screening_results'][CID].update(candidate_source='Changed CV'),
            lambda c: c['interview_plans'][CID]['plan'][0].update(reason='Changed'),
            lambda c: c['interview_records'][CID].update(source_text='Changed notes'),
            lambda c: c['evaluation_reviews'][CID]['assessments'][0].update(explanation='Changed')]
        for mutate in mutations:
            case = copy.deepcopy(self.case)
            mutate(case)
            with self.assertRaises((PermissionError,ValueError)):
                w.get_approved_evaluation(case,CID)
        with self.assertRaises(PermissionError):
            self.engine.tracker(self.case,CID,'follow_up_required','Ask follow-up.','Reviewer',False)
        with self.assertRaises((PermissionError,ValueError)):
            w.get_approved_evaluation(self.case,'Candidate_001')

    def test_evidence_ids_and_reviewer_confirmation(self):
        draft = self.case['interview_evaluations'][CID]
        rows = [{**r,'evidence_ids':[q['id'] for q in r['evidence']]} for r in draft['assessments']]
        rows[0]['evidence_ids']=['INVALID']
        with self.assertRaises(ValueError):
            self.engine.approve_evaluation(self.case,CID,rows,draft['client_summary'],draft['proposed_next_step'],'Reviewer',True)
        with self.assertRaises(ValueError):
            self.engine.save_notes(self.case,CID,'notes','actual','',True)

    def test_unchanged_role_approval_preserves_completed_case(self):
        before = copy.deepcopy(self.case)
        self.engine.approve_role(
            self.case, copy.deepcopy(self.case['review']['materials']),
            'Another reviewer', True
        )
        self.assertEqual(self.case, before)
        self.assertEqual(self.engine.load(), before)
        self.assertEqual(
            self.engine.workflow.get_approved_evaluation(self.case, CID)['candidate_id'], CID
        )

    def test_changed_role_still_invalidates_existing_screening(self):
        edited = copy.deepcopy(self.case['review']['materials'])
        edited['draft_scorecard'][0]['criterion'] = 'Changed duration requirement'
        self.engine.approve_role(self.case, edited, 'Reviewer', True)
        with self.assertRaises(PermissionError):
            self.engine.workflow.get_reviewed_screening(self.case, CID)


if __name__=='__main__':
    unittest.main()
