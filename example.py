from vy import AccountGenerator

class EmailService:
    def __init__(self):
        self.username = "user"
        self.domain = "mail.com"

    def generate_email(self) -> str:
        # Your implementation
        return f"{self.username}@{self.domain}"

    def get_verification_code(self, email: str) -> str:
        # Your implementation  
        code = "123456"
        return code

proxies = {
    "https": f"http://..."
}

email_service = EmailService()

if email_service is None:
    raise ValueError("Email service must be provided")

generator = AccountGenerator(email_service, proxies=proxies)

try:
    credentials = generator.generate_account()
    print(f"Account created successfully!")
    print(f"Email: {credentials.email}")
    print(f"Password: {credentials.password}")
    print(f"Account Number: {credentials.account_number}")
    
except Exception as e:
    print(f"Failed to create account: {e}")