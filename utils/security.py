"""
Security utilities for AI Meeting Assistant.
"""
import base64
import os
import re
from typing import List, Optional, Set

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from utils.config import get_config
from utils.logging_utils import logger

# Get configuration
config = get_config()


class SecurityManager:
    """Security manager for the AI Meeting Assistant."""
    
    def __init__(self):
        """Initialize the security manager."""
        self.encrypt_transcripts = config.get('security.encrypt_transcripts', True)
        self.pii_filtering = config.get('security.pii_filtering', True)
        self.consent_required = config.get('security.consent_required', True)
        self.consented_users: Set[str] = set()
        
        # Initialize encryption key
        self._init_encryption()
    
    def _init_encryption(self) -> None:
        """Initialize encryption key for transcript encryption."""
        # Use environment variable or generate a key
        key_env = os.getenv('ENCRYPTION_KEY')
        
        if key_env:
            # Use key from environment
            self.key = key_env.encode()
        else:
            # Generate a key and save it
            salt = os.urandom(16)
            password = os.urandom(32)  # Random password for key derivation
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            
            self.key = base64.urlsafe_b64encode(kdf.derive(password))
            
            # Save the key to a secure location (in production, use a key vault)
            key_file = 'encryption_key.key'
            with open(key_file, 'wb') as f:
                f.write(self.key)
            
            logger.info(f"Generated new encryption key and saved to {key_file}")
        
        self.cipher = Fernet(self.key)
    
    def encrypt_data(self, data: str) -> str:
        """
        Encrypt data using Fernet symmetric encryption.
        
        Args:
            data: Data to encrypt.
            
        Returns:
            Encrypted data as a base64-encoded string.
        """
        if not self.encrypt_transcripts:
            return data
        
        encrypted = self.cipher.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """
        Decrypt data using Fernet symmetric encryption.
        
        Args:
            encrypted_data: Encrypted data as a base64-encoded string.
            
        Returns:
            Decrypted data.
        """
        if not self.encrypt_transcripts:
            return encrypted_data
        
        decoded = base64.urlsafe_b64decode(encrypted_data)
        decrypted = self.cipher.decrypt(decoded)
        return decrypted.decode()
    
    def filter_pii(self, text: str) -> str:
        """
        Filter personally identifiable information (PII) from text.
        
        Args:
            text: Text to filter.
            
        Returns:
            Filtered text.
        """
        if not self.pii_filtering:
            return text
        
        # Filter email addresses
        text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '[EMAIL]', text)
        
        # Filter phone numbers
        text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)
        
        # Filter credit card numbers
        text = re.sub(r'\b(?:\d{4}[-\s]?){3}\d{4}\b', '[CREDIT_CARD]', text)
        
        # Filter SSNs
        text = re.sub(r'\b\d{3}[-]?\d{2}[-]?\d{4}\b', '[SSN]', text)
        
        return text
    
    def record_consent(self, user_id: str) -> None:
        """
        Record user consent for recording and processing.
        
        Args:
            user_id: ID of the user who gave consent.
        """
        self.consented_users.add(user_id)
        logger.info(f"Recorded consent for user {user_id}")
    
    def has_consent(self, user_id: str) -> bool:
        """
        Check if a user has given consent.
        
        Args:
            user_id: ID of the user to check.
            
        Returns:
            True if the user has given consent, False otherwise.
        """
        return not self.consent_required or user_id in self.consented_users
    
    def check_all_participants_consent(self, participant_ids: List[str]) -> bool:
        """
        Check if all participants have given consent.
        
        Args:
            participant_ids: List of participant IDs.
            
        Returns:
            True if all participants have given consent, False otherwise.
        """
        if not self.consent_required:
            return True
        
        return all(self.has_consent(user_id) for user_id in participant_ids)


# Create a singleton instance
security_manager = SecurityManager()


def get_security_manager() -> SecurityManager:
    """
    Get the security manager instance.
    
    Returns:
        SecurityManager instance.
    """
    return security_manager
