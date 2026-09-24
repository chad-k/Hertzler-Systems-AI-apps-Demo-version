import copy
from pathlib import Path
import unittest
from streamlit.testing.v1 import AppTest
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine import load_catalog, recommend, contact_link, visible_apps
ROOT = Path(__file__).resolve().parents[1]
class FinderTests(unittest.TestCase):
    def setUp(self):
        self.catalog = load_catalog(ROOT / 'app_catalog.json')
    def test_routing(self):
        expected = {'predict': 'predictive_spc', 'frequency': 'inspection_frequency', 'signals': 'spc_interpretation', 'integrity': 'entry_integrity', 'database': 'database_health', 'certificate': 'coa', 'dashboard': 'copilot', 'optimize': 'optimization'}
        for goal, app_id in expected.items():
            self.assertEqual([a['id'] for a in recommend(self.catalog, goal)], [app_id])
        self.assertEqual([a['id'] for a in recommend(self.catalog, 'unusual', 'batch')], ['batch_anomaly'])
        self.assertEqual([a['id'] for a in recommend(self.catalog, 'unusual', 'part_type')], ['mislabel'])
        self.assertEqual(len(recommend(self.catalog, 'unusual')), 2)
        self.assertEqual(recommend(self.catalog, 'other'), [])
    def test_urls_and_individual_scope(self):
        self.assertEqual(len(self.catalog['apps']), 10)
        self.assertEqual(len({a['demo_url'] for a in self.catalog['apps']}), 10)
        self.assertTrue(all(a['demo_url'].startswith('https://') for a in self.catalog['apps']))
        self.assertEqual([a['id'] for a in recommend(self.catalog, 'unusual', 'individual')], ['mislabel'])
        self.assertEqual(sum(a['review_status'] == 'source_reviewed' for a in self.catalog['apps']), 10)

    def test_publication_and_contact(self):
        c = copy.deepcopy(self.catalog)
        c['preview_mode'] = False
        self.assertEqual(visible_apps(c), [])
        c['apps'][0]['approved'] = True
        self.assertEqual(len(visible_apps(c)), 1)
        c['apps'][0]['enabled'] = False
        self.assertEqual(visible_apps(c), [])
        self.assertEqual(contact_link(c), 'https://www.hertzler.com/contact-us')
        c['contact_url'] = ''
        self.assertIsNone(contact_link(c))
        c['contact_url'] = 'https://example.com/contact?source=finder&app=old#form'
        c['contact_supports_app_parameter'] = True
        self.assertEqual(contact_link(c, c['apps'][0]), 'https://example.com/contact?source=finder&app=predictive_spc#form')
    def test_all_ui_paths(self):
        for goal in ['predict', 'frequency', 'signals', 'integrity', 'other', 'unusual', 'database', 'certificate', 'dashboard', 'optimize']:
            at = AppTest.from_file(str(ROOT / 'app.py')).run()
            self.assertFalse(at.exception)
            at.radio(key='goal_pick').set_value(goal).run()
            at.button(key='next_goal').click().run()
            if goal == 'unusual':
                at.radio(key='scope_pick').set_value('batch').run()
                at.button(key='next_scope').click().run()
            at.radio(key='data_pick').set_value('no').run()
            at.button(key='next_data').click().run()
            self.assertFalse(at.exception)
            self.assertEqual(at.session_state['step'], 3)
            at.button(key='back').click().run()
            self.assertEqual(at.radio(key='data_pick').value, 'no')
            at.button(key='restart').click().run()
            self.assertEqual(at.session_state['step'], 0)
            self.assertEqual(at.session_state['answers'], {})
            self.assertFalse(at.exception)

class TextParserTests(unittest.TestCase):
    def setUp(self):
        self.catalog = load_catalog(ROOT / 'app_catalog.json')
    def ids(self, query):
        from engine import parse_customer_request
        return [m['app']['id'] for m in parse_customer_request(self.catalog, query)]
    def test_customer_requests(self):
        cases = {
            'Predict future out-of-spec problems': 'predictive_spc',
            'Find unusual batches': 'batch_anomaly',
            'Find wrong part labels': 'mislabel',
            'How often should we inspect?': 'inspection_frequency',
            'Explain control chart signals': 'spc_interpretation',
            'Operators are entering repeated values': 'entry_integrity',
            'Our SQL Server is slow': 'database_health',
            'Generate a certificate of analysis': 'coa',
            'Create a dashboard comparing machines': 'copilot',
            'Find optimal machine settings': 'optimization',
        }
        for text, ident in cases.items():
            self.assertEqual(self.ids(text), [ident], text)
    def test_uncertain_multiple_and_negated(self):
        self.assertEqual(self.ids(''), [])
        self.assertEqual(self.ids('Find flights to Portland'), [])
        self.assertEqual(self.ids('coating quality'), [])
        self.assertEqual(set(self.ids('Generate a COA and create a dashboard')), {'coa','copilot'})
        self.assertEqual(self.ids('I do not need a dashboard; find unusual batches'), ['batch_anomaly'])
        self.catalog['preview_mode'] = False
        self.assertEqual(self.ids('SQL Server'), [])
    def test_text_ui_preserves_guided_answers(self):
        at = AppTest.from_file(str(ROOT / 'app.py')).run()
        at.radio(key='goal_pick').set_value('frequency').run()
        at.button(key='next_goal').click().run()
        answers_before = dict(at.session_state['answers'])
        at.text_area(key='problem_input').set_value('Our SQL Server is slow').run()
        next(b for b in at.button if b.label == 'Find matching apps').click().run()
        self.assertFalse(at.exception)
        self.assertEqual(at.session_state['answers'], answers_before)
        self.assertTrue(any(x.value == 'Our SQL Server is slow' for x in at.text))
        at.button(key='next_data').click().run()
        self.assertFalse(at.exception)
        self.assertEqual(at.session_state['submitted_problem'], 'Our SQL Server is slow')

class OptimizationWordingTests(unittest.TestCase):
    def test_problem_descriptions_and_exclusions(self):
        from engine import parse_customer_request
        c = load_catalog(ROOT / 'app_catalog.json')
        positive = ["process isn't optimized", "My process isn’t optimised",
                    'Our process is not fully optimized', 'Our process is inefficient',
                    'We have an inefficient manufacturing process',
                    'Optimize our manufacturing process', 'I need help optimizing my process',
                    'The process needs optimization', 'Our settings are not optimal',
                    'Our process is suboptimal']
        for query in positive:
            self.assertIn('optimization', [m['app']['id'] for m in parse_customer_request(c, query)], query)
        for query in ['I do not want to optimize my process',
                      'I am not interested in process optimization',
                      'I do not need process optimization; create a COA',
                      'Our approval process is confusing']:
            self.assertNotIn('optimization', [m['app']['id'] for m in parse_customer_request(c, query)], query)

class CapabilityRequestTests(unittest.TestCase):
    def test_capability_terms_and_context(self):
        from engine import parse_customer_request
        c = load_catalog(ROOT / 'app_catalog.json')
        def ids(query):
            return {m['app']['id'] for m in parse_customer_request(c, query)}
        for query in ['cpk', 'Cpk', 'CPK', 'Cp', 'Cp/Cpk', 'C p k', 'C.p.k',
                      'Our Cpk is low', 'Calculate process capability',
                      'capability analysis', 'Compare Cpk by machine']:
            self.assertEqual(ids(query), {'copilot'}, query)
        self.assertEqual(ids('Cpk and inspection frequency'), {'copilot', 'inspection_frequency'})
        self.assertEqual(ids('Cpk on a certificate of analysis'), {'copilot', 'coa'})
        for query in ['tcp connection', 'cpkfoo', 'I do not need Cpk', 'Ppk']:
            self.assertNotIn('copilot', ids(query), query)

class ExpandedParserTests(unittest.TestCase):
    def test_expanded_customer_language(self):
        from engine import analyze_customer_request
        c = load_catalog(ROOT / 'app_catalog.json')
        cases = {
            'What is our CPK?': 'copilot',
            'I want to see a histogram': 'copilot',
            'Compare machine M1 versus M2': 'copilot',
            'Show me the EWMA': 'copilot',
            'Build a dashbaord': 'copilot',
            'manufacturing copliot': 'copilot',
            'Our process isnt optmized': 'optimization',
            'Help me choose the temperature and pressure': 'optimization',
            'The output is off target': 'optimization',
            'How can we tune the machine?': 'optimization',
            'recommend a setpoint': 'optimization',
            'Some lots look very strange compared with others': 'batch_anomaly',
            'We have inconsistent batches': 'batch_anomaly',
            'Compare production batches': 'batch_anomaly',
            'These work orders have unusual results': 'batch_anomaly',
            'The sku is incorrect': 'mislabel',
            'Some measurement records seem odd': 'mislabel',
            'Could these parts be mislabled?': 'mislabel',
            'The declared type does not match the measurements': 'mislabel',
            'Determine the sampling interval': 'inspection_frequency',
            'Our inspections happen too often': 'inspection_frequency',
            'How frequently do we need to sample?': 'inspection_frequency',
            'We want to reduce unnecessary inspections': 'inspection_frequency',
            'inspection frequecy': 'inspection_frequency',
            'Warn us before quality failures occur': 'predictive_spc',
            'Can we anticipate defects?': 'predictive_spc',
            'Forecast our future OOS risk': 'predictive_spc',
            'Need an early warning of drift': 'predictive_spc',
            'What does this control chart signal mean?': 'spc_interpretation',
            'Help with Nelson violations': 'spc_interpretation',
            'What should we investigate for special cause?': 'spc_interpretation',
            'Our operators enter identical readings': 'entry_integrity',
            'People copy paste the values': 'entry_integrity',
            'Entry timestamps are all the same': 'entry_integrity',
            'Could these be made up readings?': 'entry_integrity',
            'Check backfilled records': 'entry_integrity',
            'Our databse is slow': 'database_health',
            'Queries keep timing out and performance is poor': 'database_health',
            'Find missing indexes': 'database_health',
            'SQL Server backup health': 'database_health',
            'create a quality certificate': 'coa',
            'Need a certifcate of analysis for the customer': 'coa',
            'Export a lot certificate': 'coa',
        }
        for query, app_id in cases.items():
            with self.subTest(query=query):
                result = analyze_customer_request(c, query)
                self.assertIn(app_id, [m['app']['id'] for m in result['matches']])
    def test_ambiguity_negation_and_new_catalog_entry(self):
        from engine import analyze_customer_request
        c = load_catalog(ROOT / 'app_catalog.json')
        for text in ['I want better quality', 'reduce scrap', 'anomaly detection']:
            result = analyze_customer_request(c, text)
            self.assertIsNotNone(result['followup'])
        for text in ['Find a cheap flight', 'recipe for custard', 'coating quality',
                     'I do not need Cpk analysis', 'No Cpk or histograms',
                     'I do not need database health or process optimization']:
            with self.subTest(query=text):
                self.assertEqual(analyze_customer_request(c,text)['matches'], [])
        matched = analyze_customer_request(c,'Show Cpk but not a dashboard')['matches']
        self.assertEqual([m['app']['id'] for m in matched], ['copilot'])
        app = dict(c['apps'][0], id='new_app', name='Tool Wear Tracker',
                   summary='Track cutter wear and tool replacement.',
                   outputs=['Cutter lifetime projections'])
        c['apps'].append(app)
        result = analyze_customer_request(c,'I need cutter lifetime projections')
        self.assertEqual([m['app']['id'] for m in result['matches']], ['new_app'])
        self.assertEqual(result['matches'][0]['match_type'], 'catalog')
    def test_ui_clarification_handoff(self):
        at = AppTest.from_file(str(ROOT / 'app.py')).run()
        at.text_area(key='problem_input').set_value('improve quality').run()
        next(b for b in at.button if b.label == 'Find matching apps').click().run()
        at.selectbox(key='text_focus').set_value('optimize').run()
        at.button(key='text_use_goal').click().run()
        self.assertFalse(at.exception)
        self.assertEqual(at.session_state['answers']['goal'], 'optimize')
        self.assertEqual(at.session_state['step'], 2)
        self.assertEqual(at.session_state['submitted_problem'], 'improve quality')

if __name__ == '__main__':
    unittest.main()
