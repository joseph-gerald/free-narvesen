import re
import time
import json
import string
import random
import requests
from curl_cffi import Session
from bs4 import BeautifulSoup

class URLS:
    INIT_AUTH = "https://vy.no/auth/microsoft?lang=nb"
    EMAIL_API = "https://..."

def clear_mail(email):
    requests.delete(URLS.EMAIL_API + email)

def fetch_mail(email):
    for _ in range(60):
        res = requests.get(URLS.EMAIL_API + email)
        if res.status_code == 200:
            data = res.json()
            clear_mail(email)
            return data
        time.sleep(1)

def get_code_from_mail(email):
    mail = fetch_mail(email)
    code = mail["raw"].split(": ").pop().split("<")[0]
    return code

def parse_settings(html):
    soup = BeautifulSoup(html, 'html.parser')
    data_elm = soup.find(attrs={"data-container": "true"})
    data = json.loads(data_elm.contents[0].split("var SETTINGS = ")[1].split("};")[0] + "}")
    csrf_token = data["csrf"]
    transaction_id = data["transId"]
    page_view_id = data["pageViewId"]
    return csrf_token, transaction_id, page_view_id

def generate_account():
    session = Session(impersonate="chrome136")
    
    random_string = ''.join([random.choice(string.ascii_lowercase + string.digits) for _ in range(10)]) 
    email = f"{random_string}@example.com"
    project = "B2C_1A_V1_SIGNUPSIGNIN"

    session.headers = {
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
    }

    print(f"GENNING ({email})")

    res = session.get(URLS.INIT_AUTH, allow_redirects=True)
    csrf_token, transaction_id, page_view_id = parse_settings(res.text)
    session.headers["x-csrf-token"] = csrf_token

    create_account_url = f"https://id.vy.no/c177e224-b676-42c5-843e-99efb0f2bfce/B2C_1A_V1_SIGNUPSIGNIN/api/CombinedSigninAndSignup/unified?local=signup&csrf_token={csrf_token}&tx={transaction_id}&p=B2C_1A_V1_SIGNUPSIGNIN"
    res = session.get(create_account_url)
    csrf_token, transaction_id, page_view_id = parse_settings(res.text)
    session.headers["x-csrf-token"] = csrf_token

    data = {
        'email': email,
        'profileConsent': 'consentPrompt',
        'request_type': 'RESPONSE',
    }
    url = f"https://id.vy.no/c177e224-b676-42c5-843e-99efb0f2bfce/{project}/SelfAsserted?tx={transaction_id}&p={project}"
    session.post(url, data=data)

    trace = []
    diags = {
        "pageViewId": page_view_id,
        "pageId": "SelfAsserted",
        "trace": trace
    }
    url = f"https://id.vy.no/c177e224-b676-42c5-843e-99efb0f2bfce/{project}/api/SelfAsserted/confirmed?csrf_token={csrf_token}&tx={transaction_id}&p={project}&diags={json.dumps(diags)}"
    res = session.get(url, allow_redirects=True)
    csrf_token, transaction_id, page_view_id = parse_settings(res.text)
    session.headers["x-csrf-token"] = csrf_token

    code = get_code_from_mail(email)
    print(f"SENT OTP ({code})")

    data = {
        'verificationCode': code,
        'request_type': 'RESPONSE',
    }
    url = f"https://id.vy.no/c177e224-b676-42c5-843e-99efb0f2bfce/{project}/SelfAsserted?csrf_token={csrf_token}&tx={transaction_id}&p={project}"
    session.post(url, data=data)

    diags = {
        "pageViewId": page_view_id,
        "pageId": "SelfAsserted",
        "trace": trace
    }
    url = f"https://id.vy.no/c177e224-b676-42c5-843e-99efb0f2bfce/{project}/api/SelfAsserted/confirmed?csrf_token={csrf_token}&tx={transaction_id}&p={project}&diags={json.dumps(diags)}"
    res = session.get(url, allow_redirects=True)
    csrf_token, transaction_id, page_view_id = parse_settings(res.text)
    session.headers["x-csrf-token"] = csrf_token

    data = {
        'newPassword': 'testtest',
        'request_type': 'RESPONSE',
    }
    session.post(
        f'https://id.vy.no/c177e224-b676-42c5-843e-99efb0f2bfce/{project}/SelfAsserted?tx={transaction_id}&p={project}',
        data=data,
    )

    diags = {
        "pageViewId": page_view_id,
        "pageId": "SelfAsserted",
        "trace": trace
    }
    url = f"https://id.vy.no/c177e224-b676-42c5-843e-99efb0f2bfce/{project}/api/SelfAsserted/confirmed?csrf_token={csrf_token}&tx={transaction_id}&p={project}&diags={json.dumps(diags)}"
    res = session.get(url, allow_redirects=True)

    html = res.text
    account_number = html.split("knr")[1].split("email")[0]
    account_number = re.sub(r'\D', '', account_number)

    json_data = {
        'firstName': ''.join([random.choice(string.ascii_lowercase) for _ in range(10)]),
        'lastName': ''.join([random.choice(string.ascii_lowercase) for _ in range(10)]),
        'birthYear': None,
        'phoneNumber': {
            'countryCode': '47',
            'nationalNumber': random.randint(10000000, 99999999),
        },
        'address': None,
    }

    url = f"https://www.vy.no/services/user/v2/users/{account_number}/profile"
    session.put(url, json=json_data)

    url = f"https://www.vy.no/services/loyalty-membership-register/users/{account_number}"
    session.post(url)

    print(f"DONE ({email})")
    return (email, "testtest", account_number)

