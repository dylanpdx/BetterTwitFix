import math
import hashlib
import base64
import uuid
from x_client_transaction import ClientTransaction
from x_client_transaction.utils import get_ondemand_file_url, generate_headers
import requests
import bs4
digits = "0123456789abcdefghijklmnopqrstuvwxyz"

def baseConversion(x, base):
    result = ''
    i = int(x)
    while i > 0:
        result = digits[i % base] + result
        i = i // base
    if int(x) != x:
        result += '.'
        i = x - int(x)
        d = 0
        while i != int(i):
            result += digits[int(i * base % base)]
            i = i * base
            d += 1
            if d >= 8:
                break
    return result


def calcSyndicationToken(idStr):
    id = int(idStr) / 1000000000000000 * math.pi
    o = baseConversion(x=id, base=int(math.pow(6, 2)))
    c = o.replace('0', '').replace('.', '')
    if c == '':
        c = '0'
    return c

def get_twitter_homepage(headers=None):
    if headers is None:
        headers = {"Authority": "x.com",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Referer": "https://x.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
            "X-Twitter-Active-User": "yes",
            "X-Twitter-Client-Language": "en"}
    if 'Authorization' in headers:
        del headers['Authorization']
    response = requests.get("https://x.com/home", headers=headers)
    return response

def generate_transaction_id(method: str, path: str,headers=None) -> str:
    session = requests.Session()
    session.headers = generate_headers()
    home_page = session.get(url="https://x.com")
    home_page_response = bs4.BeautifulSoup(home_page.content, 'html.parser')
    ondemand_file_url = get_ondemand_file_url(response=home_page_response)
    ondemand_file = session.get(url=ondemand_file_url)
    ondemand_file_response = bs4.BeautifulSoup(ondemand_file.content, 'html.parser')

    ct = ClientTransaction(home_page_response=home_page_response, ondemand_file_response=ondemand_file_response)
    transaction_id = ct.generate_transaction_id(method=method, path=path)
    return transaction_id