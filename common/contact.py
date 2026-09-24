"""Customer inquiry delivery. Recipient is fixed; credentials come from secrets."""
import hashlib
import json
import re
import smtplib
import ssl
import time
import uuid
from email.message import EmailMessage
from urllib.request import Request, urlopen

RECIPIENT = 'chad@hertzler.com'


def validate_inquiry(name, email, company, message):
    if not name.strip() or len(name) > 100:
        return 'Please enter your name (up to 100 characters).'
    if len(email) > 254 or not re.fullmatch(r"[^\s@<>\r\n]+@[^\s@<>\r\n]+\.[^\s@<>\r\n]+", email):
        return 'Please enter a valid email address.'
    if any(c in name + company for c in '\r\n') or len(company) > 150:
        return 'Please enter your name and company on single lines.'
    if len(message.strip()) < 10 or len(message) > 5000:
        return 'Please describe your request using 10–5,000 characters.'
    return None


def configured(config):
    provider = config.get('provider', 'resend')
    if provider == 'resend':
        return bool(config.get('api_key') and config.get('from_email'))
    if provider == 'smtp':
        return all(config.get(k) for k in ('host', 'username', 'password', 'from_email')) and config.get('security', 'starttls') in ('starttls', 'ssl')
    return False


def send_inquiry(config, app_name, name, email, company, message, request_id):
    error = validate_inquiry(name, email, company, message)
    if error:
        raise ValueError(error)
    if not configured(config):
        raise ValueError('Email delivery is not configured.')
    subject = 'Hertzler demo inquiry: ' + app_name.replace('\n', ' ').replace('\r', ' ')[:100]
    body = '\n'.join(['App: ' + app_name, 'Name: ' + name, 'Email: ' + email,
                      'Company: ' + company, 'Request ID: ' + request_id, '', message])
    if config.get('provider', 'resend') == 'resend':
        payload = {'from': config['from_email'], 'to': [RECIPIENT],
                   'reply_to': email, 'subject': subject, 'text': body}
        req = Request('https://api.resend.com/emails', data=json.dumps(payload).encode(),
                      headers={'Authorization': 'Bearer ' + config['api_key'],
                               'Content-Type': 'application/json',
                               'User-Agent': 'HertzlerDemoContact/1.0',
                               'Idempotency-Key': request_id}, method='POST')
        with urlopen(req, timeout=20) as response:
            result = json.loads(response.read())
        if not result.get('id'):
            raise RuntimeError('Provider did not acknowledge the email.')
        return str(result['id'])
    msg = EmailMessage()
    msg['From'] = config['from_email']
    msg['To'] = RECIPIENT
    msg['Reply-To'] = email
    msg['Subject'] = subject
    msg.set_content(body)
    security = config.get('security', 'starttls')
    context = ssl.create_default_context()
    if security == 'ssl':
        client = smtplib.SMTP_SSL(config['host'], int(config.get('port', 465)), timeout=20, context=context)
    else:
        client = smtplib.SMTP(config['host'], int(config.get('port', 587)), timeout=20)
    with client as server:
        if security == 'starttls':
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
        server.login(config['username'], config['password'])
        refused = server.send_message(msg, from_addr=config['from_email'], to_addrs=[RECIPIENT])
        if refused:
            raise RuntimeError('The mail server refused the recipient.')
    return request_id


def render_contact(app_id, app_name):
    import streamlit as st
    st.divider()
    st.header('Interested in this app for your process?')
    st.write('Tell Chad what you would like to improve or customize. Your message will include the name of this demo.')
    try:
        config = dict(st.secrets.get('email', {}))
    except (FileNotFoundError, KeyError):
        config = {}
    ready = configured(config)
    if not ready:
        st.info('The contact form is not accepting messages yet. You can email chad@hertzler.com directly.')
    key = 'contact_' + app_id
    if st.session_state.get(key + '_sent'):
        st.success('Your inquiry was accepted by the email service for delivery to Chad. Thank you!')
    st.write('**App:** ' + app_name)
    st.caption('The app name is automatically included in the email subject and message.')
    with st.form(key + '_form', clear_on_submit=False):
        name = st.text_input('Your name', max_chars=100, key=key + '_name')
        email = st.text_input('Your email', max_chars=254, key=key + '_email')
        company = st.text_input('Company (optional)', max_chars=150, key=key + '_company')
        message = st.text_area('What would you like to discuss?', max_chars=5000,
                               placeholder='Describe your process, the problem, and what you would like the app to do.', key=key + '_message')
        st.caption('Send message emails these contact details and your request to chad@hertzler.com. No demo results are attached.')
        submitted = st.form_submit_button('Send message to Chad', disabled=not ready, type='primary')
    if not submitted:
        return
    name, email, company, message = [s.strip() for s in (name, email, company, message)]
    error = validate_inquiry(name, email, company, message)
    if error:
        st.error(error)
        return
    fingerprint = hashlib.sha256(json.dumps([app_id, name, email, company, message]).encode()).hexdigest()
    if st.session_state.get(key + '_fingerprint') == fingerprint:
        st.info('This message was already accepted. Edit the message if you have a different request.')
        return
    if time.time() - st.session_state.get('contact_last_sent_at', 0) < 60:
        st.info('Please wait a minute before sending another message.')
        return
    # Keep the same provider idempotency key for an identical retry after a timeout.
    pending = st.session_state.setdefault('contact_pending_ids', {})
    request_id = pending.setdefault(fingerprint, str(uuid.uuid4()))
    try:
        with st.spinner('Sending your inquiry…'):
            send_inquiry(config, app_name, name, email, company, message, request_id)
    except Exception:
        st.error('We could not confirm that your message was sent. Please email chad@hertzler.com directly if needed.')
        return
    st.session_state[key + '_fingerprint'] = fingerprint
    st.session_state[key + '_sent'] = True
    st.session_state['contact_last_sent_at'] = time.time()
    st.success('Your inquiry was accepted by the email service for delivery to Chad. Thank you!')
