"""
==========================================================
 PROXIMITY ALERT — Google Maps + NTFY + MP3
==========================================================
 Monitora la posizione di una persona condivisa su Google Maps
 e invia una notifica NTFY e un allarme sonoro quando si avvicina.
==========================================================
"""

import argparse
import json
import math
import os
import sys
import time
import pickle
from datetime import datetime
from pathlib import Path

# ──────────────────────────────────────────────────────────
#  IMPORT CON MESSAGGIO DI ERRORE UTILE
# ──────────────────────────────────────────────────────────
try:
    import requests
except ImportError:
    print("❌ Libreria mancante. Esegui:\n   pip install -r requirements.txt")
    sys.exit(1)

try:
    import pygame
    pygame.mixer.init()
except ImportError:
    print("❌ Libreria mancante. Esegui:\n   pip install -r requirements.txt")
    sys.exit(1)

try:
    from locationsharinglib import Service
    from locationsharinglib.locationsharinglibexceptions import InvalidCookies, InvalidData
    import locationsharinglib
    from cachetools import TTLCache

    # ──────────────────────────────────────────────────────────
    #  PATCH PER BYPASS CACHE E AUTHUSER
    # ──────────────────────────────────────────────────────────
    # 1. Disattiviamo la cache interna di 30 secondi per permettere aggiornamenti più veloci
    locationsharinglib.locationsharinglib.STATE_CACHE = TTLCache(maxsize=1, ttl=0)

    # 2. Patch authuser (già presente)
    def patched_get_server_response(session):
        payload = {
            'authuser': 0,
            'hl': 'en',
            'gl': 'us',
            'pb': ('!1m7!8m6!1m3!1i14!2i8413!3i5385!2i6!3x4095'
                   '!2m3!1e0!2sm!3i407105169!3m7!2sen!5e1105!12m4'
                   '!1e68!2m2!1sset!2sRoadmap!4e1!5m4!1e4!8m2!1e0!'
                   '1e1!6m9!1e12!2i2!26m1!4b1!30m1!'
                   '1f1.3953487873077393!39b1!44e1!50e0!23i4111425')
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.google.com/maps',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        url = 'https://www.google.com/maps/rpc/locationsharing/read'
        return session.get(url, params=payload, headers=headers, verify=True)

    locationsharinglib.locationsharinglib.Service._get_server_response = staticmethod(patched_get_server_response)

except ImportError:
    print("❌ Libreria mancante. Esegui:\n   pip install -r requirements.txt")
    sys.exit(1)

# ──────────────────────────────────────────────────────────
#  CONFIGURAZIONE
# ──────────────────────────────────────────────────────────
CONFIG_FILE = Path(__file__).parent / "config.json"
COOKIES_FILE = Path(__file__).parent / "google_cookies.pkl"
BROWSER_PROFILE_DIR = Path(__file__).parent / ".browser_profile"

def load_config():
    if not CONFIG_FILE.exists():
        run_configure()
    
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)
        
    # Migrazione vecchio formato -> nuovo formato con lista locations
    if "home_lat" in config:
        print("🔧 Migrazione configurazione al nuovo formato...")
        old_loc = {
            "name": "Casa",
            "lat": config.pop("home_lat"),
            "lon": config.pop("home_lon"),
            "radius_m": config.pop("alert_radius_m", 100)
        }
        config["locations"] = [old_loc]
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
            
    return config

# ──────────────────────────────────────────────────────────
#  CALCOLO DISTANZA
# ──────────────────────────────────────────────────────────
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))

# ──────────────────────────────────────────────────────────
#  COOKIE REFRESH - MANUALE (CONSIGLIATO)
# ──────────────────────────────────────────────────────────
def refresh_cookies_manual() -> bool:
    """Consente all'utente di importare i cookie esportati in formato JSON."""
    print("\n" + "!"*55)
    print("  METODO MANUALE (Più affidabile)")
    print("!"*55)
    print("   Google blocca i programmi automatici. Segui questi passi:")
    print("\n   1. Apri Chrome (quello che usi sempre).")
    print("   2. Installa l'estensione 'Cookie-Editor' (icona biscotto).")
    print("   3. Vai su https://maps.google.com ed effettua il login.")
    print("   4. Apri l'estensione → clicca 'Export' → 'JSON'.")
    print("   5. Crea un file chiamato 'cookies.json' nella cartella del progetto.")
    print("   6. Incolla il contenuto lì dentro e salva.")
    
    json_path = Path(__file__).parent / "cookies.json"
    
    print(f"\n   Aspetto il file in: {json_path}")
    while not json_path.exists():
        print("   ... file non trovato. Premi INVIO dopo aver salvato il file (o Ctrl+C per annullare).", end="\r")
        input()
        
    try:
        import traceback
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        # Gestisce vari formati di esportazione (EditThisCookie, Cookie-Editor, etc.)
        if isinstance(data, dict):
            if "cookies" in data:
                cookies = data["cookies"]
            else:
                # Se è un dict ma non ha "cookies", forse è un singolo cookie o un altro formato
                cookies = [data]
        else:
            cookies = data
            
        with open(COOKIES_FILE, "wb") as f:
            pickle.dump(cookies, f)
            
        print("\n✅ Cookie importati con successo!")
        return True
    except Exception as e:
        print(f"\n❌ Errore durante l'importazione: {e}")
        traceback.print_exc()
        return False

# ──────────────────────────────────────────────────────────
#  COOKIE REFRESH - AUTOMATICO (PLAYWRIGHT)
# ──────────────────────────────────────────────────────────
def refresh_cookies_with_playwright(google_email: str, headless: bool = False) -> bool:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("❌ Playwright non installato. Esegui: pip install playwright && playwright install")
        return False

    print(f"\n🔄 Apertura browser {'(Sfondo)' if headless else '(Visibile)'}...")
    
    with sync_playwright() as p:
        try:
            # PROFILO: Usiamo una cartella dedicata
            # STEALTH: Evitiamo che Google rilevi l'automazione
            browser = p.chromium.launch_persistent_context(
                user_data_dir=str(BROWSER_PROFILE_DIR),
                channel="chrome", # Usa il Chrome reale installato nel sistema
                headless=headless,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={'width': 1280, 'height': 720},
                args=[
                    "--disable-blink-features=AutomationControlled", # Nasconde 'navigator.webdriver'
                    "--no-sandbox",
                ],
                ignore_default_args=["--enable-automation"] # Fondamentale per non farsi rilevare
            )
            
            page = browser.pages[0] if browser.pages else browser.new_page()
            
            # Script aggiuntivo per nascondere l'automazione
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            page.goto("https://maps.google.com")
            
            if not headless:
                print("\n" + "!"*60)
                print("  IMPORTANTE: Se vedi 'Browser non sicuro' o 'Accesso negato':")
                print("  1. Assicurati che Chrome (quello vero) sia CHIUSO.")
                print("  2. Prova a loggarti normalmente in questa finestra.")
                print("  3. Se fallisce ancora, usa il METODO MANUALE (Opzione 1).")
                print("!"*60)
                print("\n👉 EFFETTUA IL LOGIN SE NECESSARIO.")
                print("👉 Una volta che vedi Maps e la tua posizione, premi INVIO qui.")
                input("Premi INVIO dopo il login... ")
            else:
                # In modalità headless, aspettiamo che la pagina si carichi e poi proviamo a prendere i cookie
                print("⏳ Attesa caricamento Maps...")
                page.wait_for_timeout(10000) # 10 secondi per sicurezza
            
            cookies = browser.cookies(["https://www.google.com", "https://maps.google.com"])
            if not cookies:
                print("❌ Cookie non trovati.")
                browser.close()
                return False

            with open(COOKIES_FILE, "wb") as f:
                pickle.dump(cookies, f)

            print(f"✅ Cookie aggiornati automaticamente! ({len(cookies)} cookie)")
            browser.close()
            return True
        except Exception as e:
            print(f"❌ Errore Playwright: {e}")
            return False

# ──────────────────────────────────────────────────────────
#  LETTURA POSIZIONE
# ──────────────────────────────────────────────────────────
def get_authenticated_service(google_email: str):
    """Carica i cookie, li converte in formato Netscape e ritorna il Service."""
    if not COOKIES_FILE.exists():
        print("❌ File dei cookie non trovato.")
        return None

    tmp_cookie_file = Path(__file__).parent / ".tmp_netscape_cookies.txt"
    
    try:
        # Carichiamo i cookie dal pickle
        with open(COOKIES_FILE, "rb") as f:
            cookies = pickle.load(f)

        lines = ["# Netscape HTTP Cookie File"]
        for c in cookies:
            domain = c.get('domain', '.google.com')
            path = c.get('path', '/')
            host_only = c.get('hostOnly', False)
            include_subdomains = 'FALSE' if host_only else 'TRUE'
            secure = 'TRUE' if c.get('secure', False) else 'FALSE'
            expires_val = c.get('expirationDate', c.get('expires', 0))
            if expires_val > 1e11: expires_val /= 1000
            expires = int(expires_val)
            if expires == 0: expires = int(time.time()) + 31536000
            name, value = c.get('name'), c.get('value')
            if name and value:
                lines.append(f"{domain}\t{include_subdomains}\t{path}\t{secure}\t{expires}\t{name}\t{value}")

        with open(tmp_cookie_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        
        # Test diretto prima di creare il Service
        session = requests.Session()
        for c in cookies:
            session.cookies.set(c['name'], c['value'], domain=c.get('domain', '.google.com'), path=c.get('path', '/'))
        
        test_resp = patched_get_server_response(session)
        if "GgA=" in test_resp.text:
            print("⚠️ Il test di sessione ha restituito 'GgA=' (Non loggato).")
            # Proviamo con authuser=1
            print("🔄 Provo con authuser=1...")
            # Qui non possiamo facilmente cambiare il patch globale, ma il test fallito è un segnale.
        
        return Service(cookies_file=str(tmp_cookie_file))
    except Exception as e:
        print(f"❌ Errore durante l'autenticazione: {e}")
        return None

def get_shared_people_manual(cookies: list):
    """Metodo manuale per recuperare le persone se la libreria fallisce."""
    session = requests.Session()
    for c in cookies:
        session.cookies.set(c['name'], c['value'], domain=c.get('domain', '.google.com'), path=c.get('path', '/'))
    
    # Proviamo diversi authuser
    for au in [0, 1, 2]:
        payload = {
            'authuser': au,
            'hl': 'en', 'gl': 'us',
            'pb': ('!1m7!8m6!1m3!1i14!2i8413!3i5385!2i6!3x4095'
                   '!2m3!1e0!2sm!3i407105169!3m7!2sen!5e1105!12m4'
                   '!1e68!2m2!1sset!2sRoadmap!4e1!5m4!1e4!8m2!1e0!'
                   '1e1!6m9!1e12!2i2!26m1!4b1!30m1!'
                   '1f1.3953487873077393!39b1!44e1!50e0!23i4111425')
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.google.com/maps'
        }
        resp = session.get('https://www.google.com/maps/rpc/locationsharing/read', params=payload, headers=headers)
        
        if resp.ok and "GgA=" not in resp.text:
            try:
                data = json.loads(resp.text.split("'", 1)[1])
                return data[0] or []
            except:
                pass
    return None

# ──────────────────────────────────────────────────────────
#  ALLERTE
# ──────────────────────────────────────────────────────────
def play_alert_sound(sound_file: str):
    if not sound_file: return
    
    p = Path(sound_file)
    if not p.exists():
        p = Path(__file__).parent / sound_file
        
    if not p.exists():
        print(f"⚠️  Suono non trovato: {sound_file}")
        return

    try:
        print(f"🔊 Riproduzione (Loop): {p.name}")
        pygame.mixer.music.load(str(p))
        pygame.mixer.music.play(loops=-1) # Riproduce all'infinito finché non viene fermato
    except Exception as e:
        print(f"⚠️  Errore riproduzione audio: {e}")

def stop_alert_sound():
    try:
        if pygame.mixer.music.get_busy():
            print("🔇 Audio fermato.")
            pygame.mixer.music.stop()
    except: pass

def send_ntfy_alert(ntfy_topic: str, person_name: str, location_name: str, distance_m: float, lat: float, lon: float, alert_type: str = "ENTRATO"):
    try:
        maps_link = f"https://maps.google.com/?q={lat},{lon}"
        
        if alert_type == "ENTRATO":
            msg = f"{person_name} è ENTRATO nel raggio di: {location_name} ({distance_m:.0f}m)"
            title = f"Allarme {location_name}: ENTRATO"
        else:
            msg = f"{person_name} è USCITO dal raggio di: {location_name} (Fuori range)."
            title = f"Allarme {location_name}: USCITO"

        print(f"🔔 Invio notifica NTFY ({alert_type}) a: {ntfy_topic}")
        resp = requests.post(
            f"https://ntfy.sh/{ntfy_topic}",
            data=msg.encode("utf-8"),
            headers={"Title": title, "Priority": "high", "Click": maps_link},
            timeout=10
        )
        if not resp.ok:
            print(f"⚠️  NTFY ha risposto con errore: {resp.status_code}")
    except Exception as e:
        print(f"⚠️  Errore invio NTFY: {e}")

# ──────────────────────────────────────────────────────────
#  CONFIG & SETUP
# ──────────────────────────────────────────────────────────
def run_configure():
    config = {}
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            print("📝 Caricata configurazione esistente.")

    # Migrazione se necessario
    if "home_lat" in config:
        config["locations"] = [{
            "name": "Casa",
            "lat": config.pop("home_lat"),
            "lon": config.pop("home_lon"),
            "radius_m": config.pop("alert_radius_m", 100)
        }]

    def get_input(prompt, current):
        prompt_full = f"{prompt} [{current}]: " if current is not None else f"{prompt}: "
        val = input(prompt_full).strip()
        return val if val else current

    print("\n📋 GESTIONE LOCALITÀ")
    locations = config.get("locations", [])
    
    while True:
        if locations:
            print("\nLocalità attuali:")
            for i, loc in enumerate(locations):
                print(f"  {i+1}. {loc['name']} ({loc['lat']}, {loc['lon']}) - Raggio: {loc['radius_m']}m")
        else:
            print("\nNessuna località configurata.")

        choice = input("\nVuoi (A)ggiungere, (R)imuovere o (C)ontinuare? [C]: ").lower()
        if choice == 'a':
            name = input("  Nome (es. Casa): ")
            lat = float(input("  Latitudine: "))
            lon = float(input("  Longitudine: "))
            rad = int(input("  Raggio (metri): "))
            locations.append({"name": name, "lat": lat, "lon": lon, "radius_m": rad})
        elif choice == 'r':
            idx = int(input("  Numero località da rimuovere: ")) - 1
            if 0 <= idx < len(locations):
                locations.pop(idx)
        else:
            break
    
    config["locations"] = locations
    print("\n⚙️  IMPOSTAZIONI GENERALI")
    config["google_email"] = get_input("📧 Tua Email Google", config.get("google_email"))
    config["ntfy_topic"] = get_input("🔔 NTFY Topic", config.get("ntfy_topic"))
    config["sound_file"] = get_input("🔊 Sound file", config.get("sound_file", "Star Labs alarm.mp3"))
    config["check_interval_s"] = int(get_input("⏱️  Intervallo secondi", config.get("check_interval_s", 10)))

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
    print("✅ Configurazione salvata!")
    
    if input("\n🔄 Vuoi anche rifare il setup dei cookie? (s/N): ").lower() == 's':
        run_setup(config["google_email"])

def run_setup(google_email: str = None):
    print("\n--- SETUP POSIZIONE ---")
    print("1. Manuale (CONSIGLIATO - Funziona sempre)")
    print("2. Automatico (Spesso bloccato da Google)")
    scelta = input("Scegli 1 o 2: ")
    if scelta == "2":
        success = refresh_cookies_with_playwright(google_email or "email@gmail.com")
    else:
        success = refresh_cookies_manual()

    if success:
        print("\n🧪 Test di connessione in corso...")
        # Proviamo a creare il servizio per vedere se funziona
        time.sleep(1) # Un po' di pausa
        svc = get_authenticated_service(google_email or "email@gmail.com")
        if svc:
            print("✅ Connessione riuscita! I cookie sono validi.")
            return True
        else:
            print("❌ Test fallito. Il server Google Map rifiuta i cookie importati.")
            print("💡 Suggerimento: Assicurati di essere su maps.google.com quando esporti.")
            return False
    return False

def run_monitor():
    config = load_config()
    google_email = config["google_email"]
    ntfy_topic = config["ntfy_topic"]
    sound_file = config["sound_file"]
    check_interval = config.get("check_interval_s", 10)
    locations = config.get("locations", [])

    if not locations:
        print("⚠️  Nessuna località configurata. Usa --configure per aggiungerne una.")
        return

    print(f"\n🚀 MONITORAGGIO AVVIATO ({check_interval}s)")
    print(f"📧 Email: {google_email}")
    print(f"📍 Località: {', '.join([l['name'] for l in locations])}")
    print("-" * 50)

    # Stato tracciato per ogni (persona, località)
    tracked_states = {}

    service = None
    while not service:
        service = get_authenticated_service(google_email)
        if not service:
            print("\n❌ Inizializzazione fallita. Provo aggiornamento automatico in background...")
            if refresh_cookies_with_playwright(google_email, headless=True):
                service = get_authenticated_service(google_email)
            
            if not service:
                print("⚠️ Aggiornamento automatico fallito. Richiesto intervento manuale.")
                run_setup(google_email)
                config = load_config()
                google_email = config["google_email"]

    while True:
        try:
            # Carichiamo i cookie crudi per il fallback manuale
            if not COOKIES_FILE.exists():
                print("⚠️ File cookie sparito. Riprovo setup...")
                refresh_cookies_with_playwright(google_email, headless=True)

            with open(COOKIES_FILE, "rb") as f:
                raw_cookies = pickle.load(f)

            others_raw = None
            try:
                others_raw = list(service.get_shared_people())
            except Exception as e:
                print(f"\n⚠️ Errore o sessione scaduta: {e}. Provo aggiornamento automatico...")
                if refresh_cookies_with_playwright(google_email, headless=True):
                    service = get_authenticated_service(google_email)
                    if service:
                        others_raw = list(service.get_shared_people())
            
            # Se la libreria fallisce ancora o non trova nessuno, proviamo il metodo manuale
            if not others_raw:
                shared_data = get_shared_people_manual(raw_cookies)
                if not shared_data:
                    # Se anche il manuale non trova dati, proviamo un refresh forzato
                    print("🔄 Nessun dato trovato. Provo un refresh forzato del browser...")
                    if refresh_cookies_with_playwright(google_email, headless=True):
                        service = get_authenticated_service(google_email)
                        shared_data = get_shared_people_manual(raw_cookies)

                if shared_data:
                    from locationsharinglib.locationsharinglib import Person as LSPerson
                    others_raw = [LSPerson(info) for info in shared_data]

            if others_raw:
                for person in others_raw:
                    name = person.full_name or "Sconosciuto"
                    pid = person.id
                    lat, lon = person.latitude, person.longitude
                    
                    status_parts = []
                    for loc in locations:
                        loc_name = loc["name"]
                        t_lat, t_lon = loc["lat"], loc["lon"]
                        radius = loc["radius_m"]
                        
                        distance = haversine_distance(t_lat, t_lon, lat, lon)
                        inside = distance <= radius
                        
                        state_key = (pid, loc_name)
                        was_inside = tracked_states.get(state_key, False)
                        
                        if inside and not was_inside:
                            print(f"\n🚨 {name} ENTRATO nel raggio di: {loc_name} ({distance:.0f}m)")
                            send_ntfy_alert(ntfy_topic, name, loc_name, distance, lat, lon, "ENTRATO")
                            play_alert_sound(sound_file)
                        elif not inside and was_inside:
                            print(f"\n✅ {name} USCITO dal raggio di: {loc_name} (Fuori range).")
                            send_ntfy_alert(ntfy_topic, name, loc_name, distance, lat, lon, "USCITO")
                            stop_alert_sound()
                        
                        tracked_states[state_key] = inside
                        status_parts.append(f"{loc_name}: {distance:.0f}m")
                    
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] {name}: {' | '.join(status_parts)}", end="\r", flush=True)
            else:
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ⚠️ Nessuna persona trovata. I cookie potrebbero essere scaduti.")
                run_setup(google_email)
                service = get_authenticated_service(google_email)
                if not service:
                    print("❌ Impossibile reinizializzare il servizio. Uscita.")
                    return
        except Exception as e:
            print(f"\n⚠️ Errore monitoraggio: {e}. Probabile problema di cookie.")
            run_setup(google_email)
            service = get_authenticated_service(google_email)
            if not service:
                print("❌ Impossibile reinizializzare il servizio. Reiprovo tra 30s...")
                time.sleep(30)

        time.sleep(check_interval)

def run_test_alerts():
    config = load_config()
    print("\n🧪 TEST ALLERTE COMPLETO")
    
    if not config.get("locations"):
        print("⚠️ Configura almeno una località prima.")
        return
        
    loc = config["locations"][0]
    loc_name = loc["name"]
    
    print(f"\n1. Test ENTRATA a {loc_name} (Audio ON + Notifica)")
    send_ntfy_alert(config['ntfy_topic'], "TEST_USER", loc_name, 100, loc['lat'], loc['lon'], "ENTRATO")
    play_alert_sound(config['sound_file'])
    print("⏳ Audio in riproduzione... (5 secondi)")
    time.sleep(5)
    
    print(f"\n2. Test USCITA da {loc_name} (Audio OFF + Notifica)")
    send_ntfy_alert(config['ntfy_topic'], "TEST_USER", loc_name, 150, loc['lat'], loc['lon'], "USCITO")
    stop_alert_sound()
    
    print("\n✅ Test completato.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--configure", action="store_true")
    parser.add_argument("--setup", action="store_true")
    parser.add_argument("--test-alerts", action="store_true")
    args = parser.parse_args()
    
    if args.configure: run_configure()
    elif args.setup: run_setup()
    elif args.test_alerts: run_test_alerts()
    else: run_monitor()
