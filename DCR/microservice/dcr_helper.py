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


def get_enabled_events(case_id):
    """
    Return the list of enabled event IDs for a given DCR case.
    """
    url = f"{DCR_API_BASE}/graphs/{DCR_GRAPH_ID}/sims/{case_id}/events"
    r = requests.get(url, headers=HEADERS, auth=(USERNAME, PASSWORD))

    if r.status_code not in (200, 201):
        print(f"[GetEnabledEvents] Error {r.status_code}: {r.text}")
        return []

    xml = r.text.replace('\\"', '"')
    pattern = r'<event[^>]*id="([^"]+)"[^>]*enabled="true"[^>]*>'
    events = re.findall(pattern, xml, flags=re.IGNORECASE)

    print(f"[GetEnabledEvents] case_id={case_id} events={events}")
    return events


def execute_event(case_id, event_id):
    url = f"{DCR_API_BASE}/graphs/{DCR_GRAPH_ID}/sims/{case_id}/events/{event_id}"
    r = requests.post(url, headers=HEADERS, auth=(USERNAME, PASSWORD), json={})

    if r.status_code not in (200, 201, 204):
        return {
            "error": True,
            "message": f"DCR returned {r.status_code}",
            "enabledEvents": []
        }

    if not r.content or not r.text.strip():
        return {
            "error": False,
            "message": "",
            "enabledEvents": []
        }

    try:
        data = r.json()
        enabled = data.get("enabledEvents", [])
        return {
            "error": False,
            "message": "",
            "enabledEvents": enabled
        }
    except Exception:
        text = r.text
        if "<event" in text:
            enabled = re.findall(r'<event[^>]*id="([^"]+)"[^>]*enabled="true"', text, flags=re.IGNORECASE)
            return {
                "error": False,
                "message": "",
                "enabledEvents": enabled
            }

        return {
            "error": False,
            "message": "No JSON payload; empty or non-JSON DCR response",
            "enabledEvents": []
        }

