# Free Narvesen
VY is having a campaign giving out free a ~pastry and~ hot beverage to all of their users. The next step from there is pretty obvious, all we need to do is just to generate accounts to get free food!

> [!WARNING]  
> The free pastry coupon has been replaced with a hot beverage only one since `05/10/2025`

### Example of Full Web App Implementation



https://github.com/user-attachments/assets/f444eeab-de7b-4a97-9b22-093af1d2cacf

> Additionally scraped coupon data to show a clone page




<br>


## Proccess
All you have to do is just to register an account, confirm the email, and join the "Green Journey" program. This process has been automated in the [original code](https://github.com/joseph-gerald/free-narvesen/blob/main/original/main.py) and a package you can install.

<br>

# Setup

You can install this package with pip:

```
pip install vy-gen
```

Only thing left is to implement the emails. You should have a class with the two methods shown below.

```py
class EmailService:
    def generate_email(self) -> str:
        # Your implementation
        email = "user@example.com"

        return email

    def get_verification_code(self, email: str) -> str:
        # Your implementation  
        code = "123456"

        return code
```

You should end up with something like this as your final script

```py
from vy import AccountGenerator

class EmailService:
    ...

proxies = {
    "https": f"http://..." # optional
}

email_service = EmailService()

generator = AccountGenerator(email_service, proxies=proxies)

try:
    credentials = generator.generate_account()
    print(f"Account created successfully!")
    print(f"Email: {credentials.email}")
    print(f"Password: {credentials.password}")
    print(f"Account Number: {credentials.account_number}")
except Exception as e:
    print(f"Failed to create account: {e}")
```
