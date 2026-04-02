# Diagnostic script for locationsharinglib

import pickle
import time
import requests
from pathlib import Path
from locationsharinglib import Service

COOKIES_FILE = Path("google_cookies.pkl")
TMP_NETSCAPE = Path(".test_netscape.txt")

def test():
    if not COOKIES_FILE.exists():
        print("❌ google_cookies.pkl non trovato.")
        return

    with open(COOKIES_FILE, "rb") as f:
        cookies = pickle.load(f)

    lines = ["# Netscape HTTP Cookie File"]
    for c in cookies:
        domain = c.get('domain', '.google.com')
        path = c.get('path', '/')
        host_only = c.get('hostOnly', False)
        subdomains = 'FALSE' if host_only else 'TRUE'
        secure = 'TRUE' if c.get('secure', False) else 'FALSE'
        expires = int(c.get('expirationDate', c.get('expires', time.time() + 31536000)))
        name = c.get('name')
        value = c.get('value')
        if name and value:
            lines.append(f"{domain}\t{subdomains}\t{path}\t{secure}\t{expires}\t{name}\t{value}")

    with open(TMP_NETSCAPE, "w") as f:
        f.write("\n".join(lines))

    print(f"✅ Creato {TMP_NETSCAPE} con {len(lines)-1} cookie.")
    
    try:
        print("🔍 Inizializzazione Service...")
        service = Service(cookies_file=str(TMP_NETSCAPE))
        print("✅ Sessione valida!")
        print(f"👤 Autenticato come: {service.email}")
        people = list(service.get_shared_people())
        print(f"📍 Persone trovate: {len(people)}")
        for p in people:
            print(f"   - {p.full_name} ({p.latitude}, {p.longitude})")
    except Exception as e:
        print(f"❌ Fallito: {e}")
        
        # Prova debug manuale della risposta
        print("\n--- DEBUG RISPOSTA MANUALE ---")
        session = requests.Session()
        for c in cookies:
            session.cookies.set(c['name'], c['value'], domain=c.get('domain', '.google.com'), path=c.get('path', '/'))
        
        url = 'https://www.google.com/maps/rpc/locationsharing/read'
        payload = {'authuser': 0, 'hl': 'en', 'gl': 'us'}
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.google.com/maps'
        }
        resp = session.get(url, params=payload, headers=headers)
        print(f"HTTP Status: {resp.status_code}")
        if resp.ok:
            print("Risposta ricevuta, ma forse non contiene dati di posizione.")
            if "Side-of-highway" in resp.text:
                print("Sembra una pagina di login o errore.")
            else:
                print(f"Snippet risposta: {resp.text[:200]}...")
        else:
            print(f"Errore HTTP: {resp.text[:200]}...")

if __name__ == "__main__":
    test()
