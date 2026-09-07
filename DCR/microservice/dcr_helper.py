import os
import requests
import re
import base64

DCR_API_BASE = "https://repository.dcrgraphs.net/api"
DCR_GRAPH_ID = os.getenv("DCR_GRAPH_ID")
USERNAME = os.getenv("DCR_USERNAME")
PASSWORD = os.getenv("DCR_PASSWORD")

# prepare Basic Auth header
auth_string = f"{USERNAME}:{PASSWORD}"
b64_auth = base64.b64encode(auth_string.encode()).decode()

HEADERS = {
    "Authorization": f"Basic {b64_auth}",
    "Accept": "application/xml",
    "Content-Type": "application/json"
}

def create_case():
    """
    Create a new DCR case (simulation instance).
    Returns the case_id or None on failure.
    """
    create_url = f"{DCR_API_BASE}/graphs/{DCR_GRAPH_ID}/sims"
    r = requests.post(create_url, headers=HEADERS, auth=(USERNAME, PASSWORD), json={})

    if r.status_code not in (200, 201):
        print(f"[CreateCase] Error {r.status_code}: {r.text}")
        return None

    # Fetch all sims to get the latest case_id
    sims_url = f"{DCR_API_BASE}/graphs/{DCR_GRAPH_ID}/sims?filter=all"
    r2 = requests.get(sims_url, headers=HEADERS, auth=(USERNAME, PASSWORD))

    xml = r2.text
    ids = re.findall(r'<trace[^>]*id="(\d+)"', xml)

    if not ids:
        print("[CreateCase] No case IDs found")
        return None

    case_id = ids[-1]
    print(f"[CreateCase] New case_id = {case_id}")
    return case_id


def execute_event(case_id, event_id):
    """
    Execute an event on an existing DCR case.
    Returns dict: { "error": bool, "message": str, "enabledEvents": [...] }
    """
    url = f"{DCR_API_BASE}/graphs/{DCR_GRAPH_ID}/sims/{case_id}/events/{event_id}"
    r = requests.post(url, headers=HEADERS, auth=(USERNAME, PASSWORD), json={})

    if r.status_code not in (200, 201):
        return {
            "error": True,
            "message": f"DCR returned {r.status_code}",
            "enabledEvents": []
        }

    # DCR returns XML for sims API, but JSON for new API.
    try:
        data = r.json()
        enabled = data.get("enabledEvents", [])
        return {
            "error": False,
            "message": "",
            "enabledEvents": enabled
        }
    except Exception:
        return {
            "error": True,
            "message": "Malformed DCR response",
            "enabledEvents": []
        }

