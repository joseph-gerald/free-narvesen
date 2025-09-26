import re
import time
import json
import string
import random
import logging
from typing import Dict, Any, Tuple, Optional, Protocol
from dataclasses import dataclass

from curl_cffi import Session
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%d/%b/%Y %H:%M:%S",
)

logger = logging.getLogger(__name__)


@dataclass
class AccountCredentials:
    """Data class to hold account credentials and information."""
    email: str
    password: str
    account_number: str


@dataclass
class AuthTokens:
    """Data class to hold authentication tokens."""
    csrf_token: str
    transaction_id: str
    page_view_id: str


class EmailServiceProtocol(Protocol):
    """Protocol defining the interface for email services."""
    
    def generate_email(self) -> str:
        """Generate a new temporary email address."""
        ...
    
    def get_verification_code(self, email: str) -> str:
        """
        Get verification code from the specified email.
        
        Args:
            email: The email address to get verification code from
            
        Returns:
            The verification code as string
            
        Raises:
            ValueError: If verification code cannot be retrieved
        """
        ...


class VyAccountGenerator:
    """
    A class to generate Vy.no accounts programmatically.
    
    This class handles the complete account creation flow including:
    - Authentication token management
    - Account setup and profile creation
    - Email verification (via external email service)
    """
    
    # Constants
    INIT_AUTH_URL = "https://vy.no/auth/microsoft?lang=nb"
    DEFAULT_PASSWORD = "testtest"
    PROJECT_ID = "B2C_1A_V1_SIGNUPSIGNIN"
    TENANT_ID = "c177e224-b676-42c5-843e-99efb0f2bfce"
    
    def __init__(self, email_service: EmailServiceProtocol, proxies: Optional[Dict[str, str]] = None) -> None:
        """
        Initialize the account generator.
        
        Args:
            email_service: An email service that implements EmailServiceProtocol
        """
        self.email_service = email_service
        self.session = self._create_session()
        
        if proxies:
            self.session.proxies = proxies
    
    def _create_session(self) -> Session:
        """Create and configure a new session with appropriate headers."""
        session = Session(impersonate="chrome136")
        
        session.headers.update({
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-GB,en;q=0.9',
            'cache-control': 'no-cache',
            'pragma': 'no-cache',
            'priority': 'u=0, i',
            'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        })
        
        if "proxies" in self.__dict__ and self.proxies:
            session.proxies.update(self.proxies)
        
        return session
    
    def _generate_random_string(self, length: int) -> str:
        """Generate a random string of specified length using lowercase letters and digits."""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    
    def _parse_auth_tokens(self, html: str) -> AuthTokens:
        """
        Parse authentication tokens from HTML response.
        
        Args:
            html: HTML content to parse
            
        Returns:
            AuthTokens object containing parsed tokens
            
        Raises:
            ValueError: If tokens cannot be parsed
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            data_element = soup.find(attrs={"data-container": "true"})
            
            if not data_element or not data_element.contents:
                raise ValueError("No data container found in HTML")
            
            # Extract JavaScript settings object
            content = data_element.contents[0]
            settings_start = content.find("var SETTINGS = ") + len("var SETTINGS = ")
            settings_end = content.find("};", settings_start) + 1
            
            if settings_start == -1 or settings_end == 0:
                raise ValueError("SETTINGS object not found in HTML")
            
            settings_json = content[settings_start:settings_end]
            data = json.loads(settings_json)
            
            return AuthTokens(
                csrf_token=data["csrf"],
                transaction_id=data["transId"],
                page_view_id=data["pageViewId"]
            )
            
        except (json.JSONDecodeError, KeyError, AttributeError) as e:
            raise ValueError(f"Failed to parse authentication tokens: {e}")
    
    def _build_api_url(self, endpoint: str, tokens: AuthTokens, **params: str) -> str:
        """Build API URL with common parameters."""
        base_url = f"https://id.vy.no/{self.TENANT_ID}/{self.PROJECT_ID}/{endpoint}"
        
        query_params = {
            'csrf_token': tokens.csrf_token,
            'tx': tokens.transaction_id,
            'p': self.PROJECT_ID,
            **params
        }
        
        query_string = '&'.join(f"{k}={v}" for k, v in query_params.items())
        return f"{base_url}?{query_string}"
    
    def _create_diagnostics_data(self, tokens: AuthTokens, page_id: str = "SelfAsserted") -> str:
        """Create diagnostics data for API calls."""
        diags = {
            "pageViewId": tokens.page_view_id,
            "pageId": page_id,
            "trace": []
        }
        return json.dumps(diags)
    
    def _extract_account_number(self, html: str) -> str:
        """
        Extract account number from HTML response.
        
        Args:
            html: HTML content containing account number
            
        Returns:
            The extracted account number
            
        Raises:
            ValueError: If account number cannot be extracted
        """
        try:
            # Find account number between 'knr' and 'email'
            knr_start = html.find("knr")
            if knr_start == -1:
                raise ValueError("'knr' marker not found in HTML")
            
            email_start = html.find("email", knr_start)
            if email_start == -1:
                raise ValueError("'email' marker not found after 'knr'")
            
            account_section = html[knr_start:email_start]
            account_number = re.sub(r'\D', '', account_section)
            
            if not account_number:
                raise ValueError("No digits found in account section")
            
            return account_number
            
        except Exception as e:
            raise ValueError(f"Failed to extract account number: {e}")
    
    def _generate_random_profile_data(self) -> Dict[str, Any]:
        """Generate random profile data for account setup."""
        return {
            'firstName': self._generate_random_string(10),
            'lastName': self._generate_random_string(10),
            'birthYear': None,
            'phoneNumber': {
                'countryCode': '47',
                'nationalNumber': random.randint(10000000, 99999999),
            },
            'address': None,
        }
    
    def generate_account(self) -> AccountCredentials:
        """
        Generate a new Vy.no account.
        
        Returns:
            AccountCredentials object containing email, password, and account number
            
        Raises:
            Exception: If account generation fails at any step
        """
        email = self.email_service.generate_email()
        logger.info(f"Generating account for {email}")
        
        try:
            # Step 1: Initialize authentication
            response = self.session.get(self.INIT_AUTH_URL, allow_redirects=True)
            print(response.status_code)
            tokens = self._parse_auth_tokens(response.text)
            self.session.headers["x-csrf-token"] = tokens.csrf_token
            
            # Step 2: Access signup page
            signup_url = self._build_api_url("api/CombinedSigninAndSignup/unified", tokens, local="signup")
            response = self.session.get(signup_url)
            tokens = self._parse_auth_tokens(response.text)
            self.session.headers["x-csrf-token"] = tokens.csrf_token
            
            # Step 3: Submit email
            submit_url = self._build_api_url("SelfAsserted", tokens)
            email_data = {
                'email': email,
                'profileConsent': 'consentPrompt',
                'request_type': 'RESPONSE',
            }
            self.session.post(submit_url, data=email_data)
            
            # Step 4: Confirm email submission
            diags_data = self._create_diagnostics_data(tokens)
            confirm_url = self._build_api_url("api/SelfAsserted/confirmed", tokens, diags=diags_data)
            response = self.session.get(confirm_url, allow_redirects=True)
            tokens = self._parse_auth_tokens(response.text)
            self.session.headers["x-csrf-token"] = tokens.csrf_token
            
            # Step 5: Get and submit verification code
            verification_code = self.email_service.get_verification_code(email)
            logger.info(f"Received verification code: {verification_code}")
            
            verify_url = self._build_api_url("SelfAsserted", tokens)
            verify_data = {
                'verificationCode': verification_code,
                'request_type': 'RESPONSE',
            }
            self.session.post(verify_url, data=verify_data)
            
            # Step 6: Confirm verification
            diags_data = self._create_diagnostics_data(tokens)
            confirm_url = self._build_api_url("api/SelfAsserted/confirmed", tokens, diags=diags_data)
            response = self.session.get(confirm_url, allow_redirects=True)
            tokens = self._parse_auth_tokens(response.text)
            self.session.headers["x-csrf-token"] = tokens.csrf_token
            
            # Step 7: Set password
            password_url = self._build_api_url("SelfAsserted", tokens)
            password_data = {
                'newPassword': self.DEFAULT_PASSWORD,
                'request_type': 'RESPONSE',
            }
            self.session.post(password_url, data=password_data)
            
            # Step 8: Finalize account creation
            diags_data = self._create_diagnostics_data(tokens)
            final_url = self._build_api_url("api/SelfAsserted/confirmed", tokens, diags=diags_data)
            response = self.session.get(final_url, allow_redirects=True)
            
            # Step 9: Extract account number and setup profile
            account_number = self._extract_account_number(response.text)
            
            # Step 10: Update user profile
            profile_data = self._generate_random_profile_data()
            profile_url = f"https://www.vy.no/services/user/v2/users/{account_number}/profile"
            self.session.put(profile_url, json=profile_data)
            
            # Step 11: Register for loyalty program
            loyalty_url = f"https://www.vy.no/services/loyalty-membership-register/users/{account_number}"
            self.session.post(loyalty_url)
            
            logger.info(f"Successfully created account: {email}")
            return AccountCredentials(email, self.DEFAULT_PASSWORD, account_number)
            
        except Exception as e:
            logger.error(f"Failed to generate account for {email}: {e}")
            raise

def main() -> None:
    """Example usage of the VyAccountGenerator."""
    email_service = None # ah implement yourself please
    
    if email_service is None:
        raise ValueError("Email service must be provided")
    
    generator = VyAccountGenerator(email_service)
    
    try:
        credentials = generator.generate_account()
        print(f"Account created successfully!")
        print(f"Email: {credentials.email}")
        print(f"Password: {credentials.password}")
        print(f"Account Number: {credentials.account_number}")
        
    except Exception as e:
        print(f"Failed to create account: {e}")


if __name__ == "__main__":
    main()