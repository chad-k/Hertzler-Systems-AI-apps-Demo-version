import ast
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from common.contact import send_inquiry, validate_inquiry, RECIPIENT

class DemoRestrictions(unittest.TestCase):
    def test_no_upload_widgets(self):
        for path in ROOT.rglob('*.py'):
            if 'tests' in path.parts:
                continue
            tree = ast.parse(path.read_text())
            uploads = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == 'file_uploader']
            self.assertFalse(uploads, str(path))

    def test_guides_and_entrypoints(self):
        manifest = json.loads((ROOT / 'deployment_manifest.json').read_text())
        self.assertEqual(len(manifest), 10)
        for app in manifest:
            self.assertTrue((ROOT / app['entrypoint']).is_file())
            guide = (ROOT / 'guides' / (app['app_id'] + '.md')).read_text()
            self.assertGreater(len(guide.split()), 250)

class ContactDelivery(unittest.TestCase):
    def test_validation(self):
        self.assertIsNone(validate_inquiry('Customer', 'customer@example.com', '', 'Please customize this app.'))
        self.assertIsNotNone(validate_inquiry('Customer', 'bad\r\nBcc: x@example.com', '', 'Please customize this app.'))
        self.assertIsNotNone(validate_inquiry('', 'customer@example.com', '', 'Please customize this app.'))

    @patch('common.contact.urlopen')
    def test_resend_fixed_recipient_reply_to_and_retry_key(self, send):
        send.return_value.__enter__.return_value.read.return_value = b'{"id":"test-accepted"}'
        result = send_inquiry({'provider':'resend','api_key':'test-key','from_email':'demo@example.com'}, 'Example Demo', 'Customer', 'customer@example.com', 'Example', 'Please customize this app.', 'stable-request-id')
        request = send.call_args.args[0]
        payload = json.loads(request.data)
        self.assertEqual(result, 'test-accepted')
        self.assertEqual(payload['to'], [RECIPIENT])
        self.assertEqual(payload['reply_to'], 'customer@example.com')
        self.assertEqual(payload['subject'], 'Hertzler demo inquiry: Example Demo')
        self.assertIn('Example Demo', payload['text'])
        self.assertEqual(request.get_header('Idempotency-key'), 'stable-request-id')

    @patch('common.contact.smtplib.SMTP')
    def test_smtp_encrypted_delivery(self, smtp):
        server = smtp.return_value.__enter__.return_value
        server.send_message.return_value = {}
        send_inquiry({'provider':'smtp','host':'smtp.example.com','username':'test','password':'test','from_email':'demo@example.com'}, 'Example Demo','Customer','customer@example.com','','Please customize this app.','test-id')
        server.starttls.assert_called_once()
        self.assertEqual(server.send_message.call_args.kwargs['to_addrs'], [RECIPIENT])

    @patch('common.contact.urlopen', side_effect=TimeoutError)
    def test_delivery_error_is_not_success(self, send):
        with self.assertRaises(TimeoutError):
            send_inquiry({'api_key':'test','from_email':'demo@example.com'}, 'Demo','Customer','customer@example.com','','Please customize this app.','test-id')

if __name__ == '__main__':
    unittest.main()
