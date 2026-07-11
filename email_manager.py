import base64
import logging
from email.message import EmailMessage
from dateutil.parser import parse
from datetime import datetime, timedelta

logger = logging.getLogger("jarvis.email")

class EmailManager:
    def __init__(self, integrations_manager):
        self.integrations = integrations_manager

    def get_unanswered_threads(self):
        """Scans inbox metadata and generates a summary of unanswered emails from the last 7 days."""
        service = self.integrations.get_google_service('gmail', 'v1')
        if not service:
            return "Gmail service not available."
            
        try:
            # Query: unread OR not replied to (rough approximation using Google's search operators)
            # A more precise way is to look for threads where the last message isn't from the user
            now = datetime.utcnow()
            last_week = now - timedelta(days=7)
            query = f"after:{int(last_week.timestamp())} -from:me"
            
            results = service.users().threads().list(userId='me', q=query).execute()
            threads = results.get('threads', [])
            
            if not threads:
                return "No unanswered emails found from the last 7 days."
                
            summary = []
            for t in threads[:10]:  # Limit to 10
                t_data = service.users().threads().get(userId='me', id=t['id']).execute()
                messages = t_data.get('messages', [])
                
                if messages:
                    last_msg = messages[-1]
                    headers = {h['name'].lower(): h['value'] for h in last_msg['payload']['headers']}
                    
                    sender = headers.get('from', 'Unknown')
                    subject = headers.get('subject', 'No Subject')
                    
                    # Ensure the last message isn't from us
                    if 'me' not in sender.lower() and self._user_email() not in sender.lower():
                        summary.append(f"From: {sender} | Subject: {subject}")
            
            if not summary:
                return "All recent threads have been replied to."
                
            return "Unanswered Threads:\n" + "\n".join(summary)
            
        except Exception as e:
            logger.error("Failed to fetch unanswered threads: %s", e)
            return f"Failed to fetch emails: {e}"

    def _user_email(self):
        """Helper to get the user's email address."""
        service = self.integrations.get_google_service('gmail', 'v1')
        if not service:
            return ""
        try:
            profile = service.users().getProfile(userId='me').execute()
            return profile.get('emailAddress', '').lower()
        except:
            return ""

    def resolve_contact(self, name: str) -> str:
        """Attempt to resolve a name to an email address via Google Contacts."""
        if '@' in name:
            return name
            
        service = self.integrations.get_google_service('people', 'v1')
        if not service:
            return name
            
        try:
            results = service.people().searchContacts(
                query=name,
                readMask='emailAddresses,names'
            ).execute()
            
            connections = results.get('results', [])
            for person in connections:
                person_data = person.get('person', {})
                emails = person_data.get('emailAddresses', [])
                if emails:
                    return emails[0].get('value', name)
                    
            return name
        except Exception as e:
            logger.error("Failed to resolve contact: %s", e)
            return name

    def draft_email(self, to_address, subject, body):
        """Creates a safety-locked email draft. Does NOT send it."""
        service = self.integrations.get_google_service('gmail', 'v1')
        if not service:
            return "Gmail service not available."
            
        try:
            message = EmailMessage()
            message.set_content(body)
            message['To'] = to_address
            message['Subject'] = subject
            
            # Encode as base64url
            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            create_message = {
                'message': {
                    'raw': encoded_message
                }
            }
            
            draft = service.users().drafts().create(userId='me', body=create_message).execute()
            draft_id = draft['id']
            
            # Create a link to the draft
            draft_url = f"https://mail.google.com/mail/u/0/#drafts/{draft['message']['id']}"
            
            return f"Draft created successfully. Draft ID: {draft_id}. Review it here: {draft_url}"
            
        except Exception as e:
            logger.error("Failed to draft email: %s", e)
            return f"Failed to create draft: {e}"

    def send_email(self, to_address, subject, body):
        """Creates and immediately sends an email."""
        service = self.integrations.get_google_service('gmail', 'v1')
        if not service:
            return "Gmail service not available."
            
        try:
            message = EmailMessage()
            message.set_content(body)
            message['To'] = to_address
            message['Subject'] = subject
            
            # Encode as base64url
            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            create_message = {
                'raw': encoded_message
            }
            
            sent_msg = service.users().messages().send(userId='me', body=create_message).execute()
            
            return f"Email successfully sent to {to_address}."
            
        except Exception as e:
            logger.error("Failed to send email: %s", e)
            return f"Failed to send email: {e}"
