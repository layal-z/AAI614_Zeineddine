"""Streamlit browser-state tests using only a synthetic case."""
import copy
import json
import sys
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest
from engine import RecruitmentEngine
from test_app import completed_case

ROOT=Path(__file__).resolve().parent

class InterfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path=ROOT/'data'/'cases'/'_ui_test_only.json'
        cls.path.parent.mkdir(parents=True,exist_ok=True)
        cls.fixture=completed_case(RecruitmentEngine(cls.path))

    @classmethod
    def tearDownClass(cls):
        cls.path.unlink(missing_ok=True)

    def app(self):
        app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30)
        app.session_state['case_selector']=self.path.name
        app.run()
        self.assertFalse(app.exception)
        return app

    def test_all_five_pages_and_candidate_switch(self):
        app=self.app()
        candidate=next(x for x in app.selectbox if x.label=='Candidate')
        candidate.select('Candidate_002').run()
        for stage in ['Role','Screening','Interview','Evaluation','Tracker & checks']:
            next(x for x in app.radio if x.label=='Step').set_value(stage).run()
            self.assertFalse(app.exception,stage)
        next(x for x in app.radio if x.label=='Step').set_value('Screening').run()
        next(x for x in app.selectbox if x.label=='Candidate').select('Add candidate').run()
        self.assertFalse(app.exception)
        self.assertEqual(next(x for x in app.text_area if x.label=='Check or paste the CV text').value,'')
        self.assertEqual(json.loads(self.path.read_text()),self.fixture)

    def test_unconfirmed_review_blocked_and_case_unchanged(self):
        app=self.app()
        next(x for x in app.selectbox if x.label=='Candidate').select('Candidate_002').run()
        next(x for x in app.radio if x.label=='Step').set_value('Evaluation').run()
        next(x for x in app.button if x.label=='Save and approve report').click().run()
        self.assertFalse(app.exception)
        self.assertTrue(any('reviewer name' in x.value for x in app.error))
        self.assertEqual(json.loads(self.path.read_text()),self.fixture)

    def test_case_selector_can_return_to_onboarding(self):
        app=self.app()
        next(x for x in app.selectbox if x.label=='Case').select('Create or import a case').run()
        self.assertFalse(app.exception)
        self.assertTrue(any(x.value=='Start a recruitment case' for x in app.subheader))

if __name__=='__main__':
    unittest.main()
