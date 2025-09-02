import requests
import xml.etree.ElementTree as ET
import time
import os

API_URL = "http://partner.net-empregos.com/hrsmart_insert.asp"
REMOVE_API_URL = "http://partner.net-empregos.com/hrsmart_remove.asp"
FEED_URL = "https://recruit.zoho.eu/recruit/downloadjobfeed?clientid=da279e513762f8ff929094f0761b8d7028c9ede87d9cc749c7fc7c9ec526d541db96e9a00da67f84101be0a8e52f82b6"

API_KEY = os.getenv("API_ACCESS_KEY")

session = requests.Session()

def format_ref(ref):
    cleaned_ref = ''.join(c for c in str(ref) if c.isalnum())
    if len(cleaned_ref) < 20:
        cleaned_ref = cleaned_ref.ljust(20, '0')
    elif len(cleaned_ref) > 20:
        cleaned_ref = cleaned_ref[:20]
    return cleaned_ref

def simplify_html(html_text):
    # here you can reuse your existing BeautifulSoup cleaner
    return html_text.strip()

# 1. Fetch XML feed
print("Fetching XML feed...")
response = session.get(FEED_URL, timeout=10)
response.raise_for_status()
xml_content = response.content

# 2. Parse XML
root = ET.fromstring(xml_content)
jobs = root.findall(".//job")
print(f"Found {len(jobs)} jobs in feed.")

# 3. Process each job
for job in jobs:
    title = job.findtext("title")
    job_id = job.findtext("referencenumber")
    url = job.findtext("url")
    description = job.findtext("description")
    category = job.findtext("category")
    state = job.findtext("state")
    experience = job.findtext("experience")

    formatted_ref = format_ref(job_id)

    payload = {
        "ACCESS": API_KEY,
        "REF": formatted_ref,
        "TITULO": title,
        "TEXTO": (
            f"{simplify_html(description)}<br><br>"
            f"<a href=\"{url}?id={formatted_ref}&utm_source=NET_EMPREGOS\" target=\"_blank\">"
            f"Clique aqui para se candidatar!</a><br>"
            f"ou por email para info@recruityard.com"
        ),
        "ZONA": state if state else "Indefinido",
        "CATEGORIA": category if category else "Outros",
        "TIPO": "Full-time"  # adjust mapping if needed
    }

    # Remove job first
    remove_payload = {"ACCESS": API_KEY, "REF": formatted_ref}
    try:
        remove_response = session.get(REMOVE_API_URL, params=remove_payload, timeout=10)
        print(f"Remove job {formatted_ref}: {remove_response.status_code} - {remove_response.text}")
    except Exception as e:
        print(f"Error removing job {formatted_ref}: {e}")

    # Post job
    try:
        post_response = session.post(API_URL, data=payload, timeout=10)
        print(f"Post job '{title}': {post_response.status_code} - {post_response.text}")
    except Exception as e:
        print(f"Error posting job '{title}': {e}")

    time.sleep(5)
