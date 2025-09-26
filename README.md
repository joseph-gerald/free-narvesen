# free-narvesen
Abusing VY's "Green Journey" campaign to get free pastry and coffee.

<br>

## Background
VY is having a campaign trying to reward users for being environmentally concious through public transport. Their rewards are some discounts and coupons for a free pastry and hot beverage (*coutesty of narvesen*).

<br>

## Proccess
All you have to do is just to register an account, confirm the email, and join the "Green Journey" program. This process has been automated in the [original code](https://github.com/joseph-gerald/free-narvesen/blob/main/original.py) and [AI beautified](https://github.com/joseph-gerald/free-narvesen/blob/main/vy.py) one.

<br>

# Setup
```
TODO: this
```

<br>

You'll need to implement your own handling for emails, and should have the two methods shown below.

## Boilerplater Email Service Implementation
```py
from vy import VyAccountGenerator

class MyEmailService:
    def generate_email(self) -> str:
        # Your implementation
        return f"{username}@{domain}"
    
    def get_verification_code(self, email: str) -> str:
        # Your implementation  
        return code (you need to parse it yourself)

email_service = MyEmailService()
generator = VyAccountGenerator(email_service)
```
