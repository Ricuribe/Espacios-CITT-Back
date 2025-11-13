import requests
from django.conf import settings

def create_event_form(event_name):
    script_url = settings.GOOGLE_SCRIPT_URL
    try:
        response = requests.post(script_url, json={"event_name": event_name}, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") == "success":
            return {
                "edit_link": data.get("form_edit_link"),
                "public_link": data.get("form_public_link"),
                "published_available": data.get("published_available", False)
            }
        else:
            print("Error del script:", data)
            return None
    except Exception as e:
        print("Error al conectar con Google Script:", e)
        return None
