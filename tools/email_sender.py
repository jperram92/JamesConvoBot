"""
Email sender tool for AI Meeting Assistant.
"""
import base64
import os
import pickle
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional, Type

from pydantic import Field

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from langchain.tools import BaseTool

from utils.config import get_config
from utils.logging_utils import logger

# Get configuration
config = get_config()


class EmailSenderTool(BaseTool):
    """Tool for sending emails via Gmail API."""

    name: str = Field(default="email_sender")
    description: str = Field(default="Useful for sending emails with meeting summaries, action items, or other information to meeting participants.")

    def __init__(self):
        """Initialize the email sender tool."""
        super().__init__()
        self.credentials_path = config.get('api_keys.google.credentials_path', 'credentials.json')
        self.token_path = config.get('api_keys.google.token_path', 'token.pickle')
        self.scopes = ['https://www.googleapis.com/auth/gmail.send']
        self.service = None

    def _authenticate(self) -> None:
        """Authenticate with the Gmail API."""
        creds = None

        # Load token from file if it exists
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)

        # Refresh token if expired
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        # Otherwise, get new credentials
        elif not creds:
            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_path, self.scopes)
            creds = flow.run_local_server(port=0)

            # Save the credentials for the next run
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)

        # Build the service
        self.service = build('gmail', 'v1', credentials=creds)
        logger.info("Authenticated with Gmail API")

    def _run(
        self,
        recipients: List[str],
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> str:
        """
        Run the email sender tool.

        Args:
            recipients: List of email recipients.
            subject: Email subject.
            body: Email body.
            cc: List of CC recipients.
            bcc: List of BCC recipients.

        Returns:
            Status message.
        """
        # Authenticate if not already authenticated
        if self.service is None:
            try:
                self._authenticate()
            except Exception as e:
                logger.error(f"Error authenticating with Gmail API: {e}")
                return f"Error authenticating with Gmail API: {str(e)}"

        try:
            # Create message
            message = MIMEMultipart()
            message['to'] = ', '.join(recipients)
            message['subject'] = subject

            if cc:
                message['cc'] = ', '.join(cc)

            if bcc:
                message['bcc'] = ', '.join(bcc)

            # Add body
            message.attach(MIMEText(body, 'html'))

            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

            # Send message
            self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()

            logger.info(f"Email sent to {', '.join(recipients)}")
            return f"Email sent successfully to {', '.join(recipients)}"

        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return f"Error sending email: {str(e)}"

    async def _arun(
        self,
        recipients: List[str],
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> str:
        """
        Run the email sender tool asynchronously.

        Args:
            recipients: List of email recipients.
            subject: Email subject.
            body: Email body.
            cc: List of CC recipients.
            bcc: List of BCC recipients.

        Returns:
            Status message.
        """
        # For simplicity, we'll just call the synchronous version
        return self._run(recipients, subject, body, cc, bcc)
