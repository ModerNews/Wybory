import os

import dotenv
from dotenv import load_dotenv

with open(".env", 'a') as file:
    pass

file = dotenv.find_dotenv()
load_dotenv()

if os.getenv("first_start", 'true') == 'true':
    os.system("pip install -r requirements.txt")
    dotenv.set_key(file, "first_start", "false")

os.system("uvicorn main:app --reload --host 127.0.0.1 --port 8080")