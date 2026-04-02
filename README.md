# 📍 Proximity Alert — Guida Completa

App che ti avvisa su **NTFY** (iPhone/Android) e con un **allarme sonoro (MP3)** sul PC quando una persona condivide la posizione su **Google Maps** e si avvicina a casa tua.

---

## ✅ Come funziona il sistema dei Cookie (AUTOMATICO)

Il problema dei cookie scaduti è risolto così:
- Lo script usa **Playwright** per aprire il tuo Chrome (già loggato a Google)
- Estrae automaticamente i cookie di sessione
- Quando scadono, li aggiorna da solo senza che tu faccia nulla

---

## 🚀 Installazione (una volta sola)

### 1. Installa le dipendenze
```powershell
pip install -r requirements.txt
playwright install chromium
```

### 2. Configura l'app
```powershell
python proximity_alert.py --configure
```
Ti verranno chiesti:
- Coordinate di casa tua *(vai su maps.google.com, clicca su casa, copia lat/lon)*
- Raggio di allerta in metri *(es. 500)*
- La tua email Google
- API Key Pushbullet *(vedi sotto)*
- Intervallo di controllo in secondi *(es. 30)*

### 3. Configura le notifiche su iPhone/Android (NTFY)
1. Installa l'app **ntfy** sul telefono (gratis).
2. Scegli un nome topic unico (es. `allarme-casa-99x`) e aggiungilo nell'app.

### 4. Suono di allerta
Il file `Star Labs alarm.mp3` è già configurato come suono predefinito sul tuo PC.


### 4. Condivisione posizione (la persona tracciata)
La persona deve condividere la posizione con **il tuo account Google** tramite Google Maps:
- Apre Google Maps → tocca la sua foto profilo → **Condivisione posizione**
- Seleziona **"Fino a quando disattivi"** → condivide con la tua email

---

## ▶️ Avvia il monitoraggio
```powershell
python proximity_alert.py
```

Lo script girerà in background. Quando la persona entra nel raggio:
- Ricevi una notifica **Pushbullet** su Android con la distanza e il link alla mappa

---

## 🔄 Aggiornamento manuale cookie (se necessario)
Se lo script non riesce ad aggiornare i cookie da solo:
```powershell
python proximity_alert.py --setup
```

---

## 📁 File creati
| File | Descrizione |
|------|-------------|
| `proximity_alert.py` | Script principale |
| `requirements.txt` | Dipendenze Python |
| `config.json` | La tua configurazione *(creato dal --configure)* |
| `google_cookies.pkl` | Cookie Google *(creato automaticamente)* |

---

## ⚠️ Note importanti
- Lo script deve restare **aperto** sul PC per monitorare
- Per farlo girare sempre, puoi usare **Task Scheduler** di Windows
- La precisione della posizione dipende da Google Maps (aggiorna ogni ~2 minuti)
