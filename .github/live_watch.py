"""Следит, идёт ли эфир в TikTok (@_heart995), и пишет результат в status.json.

Работает внутри GitHub Actions: проверяет каждые 2 минуты примерно 5,5 часа,
потом workflow сам перезапускает себя (так проверка идёт без перерыва).
"""
import datetime, json, subprocess, time, urllib.request

URL = ("https://www.tiktok.com/api-live/user/room/?aid=1988&app_name=tiktok_web"
       "&device_platform=web_pc&uniqueId=_heart995&sourceType=54")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130 Safari/537.36")
INTERVAL = 120            # секунд между проверками
RUN_FOR = 5.5 * 3600      # сколько работает один запуск
HEARTBEAT = 20 * 60       # пока идёт эфир — подтверждаем раз в 20 минут (сайт не верит данным старше 40 мин)


def tiktok_live():
    try:
        req = urllib.request.Request(URL, headers={"User-Agent": UA})
        d = json.load(urllib.request.urlopen(req, timeout=20))
        data = d.get("data") or {}
        st = (data.get("liveRoom") or {}).get("status") or (data.get("user") or {}).get("status")
        return st == 2
    except Exception as e:  # сеть/TikTok недоступны — пропускаем эту проверку
        print("не удалось получить статус:", e, flush=True)
        return None


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True)


def read_status():
    try:
        return json.load(open("status.json"))
    except Exception:
        return {}


def age_of(old, now):
    try:
        return (now - datetime.datetime.fromisoformat(old["checked"].replace("Z", "+00:00"))).total_seconds()
    except Exception:
        return 1e9


def main():
    git("config", "user.name", "live-status-bot")
    git("config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    end = time.time() + RUN_FOR
    while time.time() < end:
        live = tiktok_live()
        now = datetime.datetime.now(datetime.timezone.utc)
        if live is not None:
            old = read_status()
            if old.get("live") != live or (live and age_of(old, now) > HEARTBEAT):
                git("pull", "--rebase", "-q", "origin", "main")
                json.dump({"live": live, "checked": now.strftime("%Y-%m-%dT%H:%M:%SZ")}, open("status.json", "w"))
                git("add", "status.json")
                git("commit", "-q", "-m", "Live: on" if live else "Live: off")
                for _ in range(3):
                    if git("push", "-q", "origin", "HEAD:main").returncode == 0:
                        break
                    git("pull", "--rebase", "-q", "origin", "main")
                print(now.strftime("%H:%M"), "записано: live =", live, flush=True)
            else:
                print(now.strftime("%H:%M"), "без изменений: live =", live, flush=True)
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
