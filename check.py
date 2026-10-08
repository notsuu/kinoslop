from dotenv import load_dotenv
load_dotenv()

import json
import os
import requests
import sys
import time

HISTORY_FILE = ".seen_ids"
MESSAGE_CAPACITY = 4000 # slightly below actual limit (4096) as a safety margin
SEND_ATTEMPTS = 10
SEND_INTERVAL = 5

TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
TG_USER_ID = os.getenv("TG_USER_ID")
TG_API = os.getenv("TG_API")
TG_PROXY_KEY = os.getenv("TG_PROXY_KEY")
MK_SITE = os.getenv("MK_SITE")
MK_CINEMA_ID = os.getenv("MK_CINEMA_ID")
MK_CINEMA_LOCATION = os.getenv("MK_CINEMA_LOCATION")

def tg_request(method: str, data = dict()) -> dict | None:
    url = f"{TG_API}/bot{TG_BOT_TOKEN}/{method}"
    resp = requests.post(url, data=json.dumps(data), headers={
        "Content-Type": "application/json; charset=utf-8",
        "X-Proxy-Auth": TG_PROXY_KEY
    })

    result = resp.json()
    if not result.get("ok"):
        source = "Telegram proxy" if result.get("proxy_error") else "Telegram API"
        desc = result.get("description") or "Unknown error"
        raise Exception(f"{source} returned error: {desc} ({resp.status_code})")
    return result.get("result")

def fetch_films():
    url = f"{MK_SITE}/api/cinema/{MK_CINEMA_ID}/film/soon"
    resp = requests.get(url)

    result = resp.json()
    status = result.get("status")
    if status != "success":
        raise Exception(f"Cinema API returned error: {status} ({resp.status_code})")
    return result.get("data")

def sanitize(string: str):
    for src, repl in [("&", "&amp;"), ("<", "&lt;"), (">", "&gt;")]:
        string = string.replace(src, repl)
    return string

def format_message(films: list[dict]):
    queue = [f"Новых фильмов: {len(films)}\n"]
    index = 0
    for i in range(len(films)):
        film = films[i]
        tickets = f", доступны билеты" if film["buy"] else ""
        duration = f" · {sanitize(film["duration"])}" if film.get("duration") else ""
        meta = (
            f"- <a href=\"{MK_SITE}/{MK_CINEMA_LOCATION}/afisha/film/{film["id"]}\">{sanitize(film["name"])}</a>"
            f" · {sanitize(film["genres"])} · {sanitize(film["countries"])}{duration}"
            f" · <b>премьера {film["premiere"]}{tickets}</b>"
        )

        updated = queue[index] + "\n" + meta
        if len(updated.encode("utf-8")) > MESSAGE_CAPACITY:
            index += 1
            queue.append(meta)
        else: queue[index] = updated
    return queue

def send_messages(messages):
    for i in range(len(messages)):
        attempt = 1
        while True:
            try:
                tg_request("sendMessage", {
                    "chat_id": TG_USER_ID,
                    "text": messages[i],
                    "parse_mode": "HTML"
                })
                break
            except Exception as e:
                print(
                    f"Sending message {i+1}/{len(messages)} attempt {attempt}/{SEND_ATTEMPTS} failed: {e}",
                    file=sys.stderr
                )
                if attempt == SEND_ATTEMPTS:
                    print("Aborting", file=sys.stderr)
                    sys.exit(1)
                attempt += 1
                time.sleep(SEND_INTERVAL)

def _main():
    seen = []
    try:
        with open(HISTORY_FILE, "r") as f: seen = json.load(f)
    except Exception: pass

    unseen = []
    for film in fetch_films():
        if film["id"] in seen: continue
        seen.append(film["id"])
        unseen.append(film)
    if len(unseen) == 0: return print("No new films")

    messages = format_message(unseen)
    print(f"Sending {len(unseen)} film(s) across {len(messages)} message(s)")
    send_messages(messages)

    with open(HISTORY_FILE, "w") as f: json.dump(seen, f)

if __name__ == "__main__":
    try: _main()
    except Exception as e: print(e, file=sys.stderr)