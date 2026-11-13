"""Telegram front end for "Ten Words. STOP."  Standard library only.

Run:  BOT_TOKEN=123:abc python3 bot.py
"""
import json
import os
import sys
import urllib.parse
import urllib.request

from game import Game, MAX_WORDS

TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    sys.exit("Set BOT_TOKEN first (get one from @BotFather).")
API = f"https://api.telegram.org/bot{TOKEN}/"

game = Game(os.path.join(os.path.dirname(os.path.abspath(__file__)), "state.json"))
dm_target = {}  # user_id -> group chat_id they're submitting to
BOT_USERNAME = ""

HELP = (
    "<b>Ten Words. STOP.</b>\n"
    f"Summarize a news story in {MAX_WORDS} words or fewer, ending with STOP, "
    "like a telegram. Everyone votes on the best one.\n\n"
    "Add me to a group, then:\n"
    "/newround &lt;headline, summary or link&gt; - post a story\n"
    "/vote - close submissions and open the ballot\n"
    "/results - reveal the winner\n"
    "/leaderboard - season standings\n"
    "/play - today's Daily Nebraskan game (or /play &lt;story link&gt; for any story)"
)


def call(method, **params):
    data = urllib.parse.urlencode(
        {k: json.dumps(v) if isinstance(v, (dict, list)) else v for k, v in params.items()}
    ).encode()
    try:
        with urllib.request.urlopen(API + method, data, timeout=60) as r:
            return json.load(r)["result"]
    except Exception as e:
        print("API error:", method, e)
        return None


def send(chat_id, text, **kw):
    return call("sendMessage", chat_id=chat_id, text=text, parse_mode="HTML",
                disable_web_page_preview=True, **kw)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def name_of(u):
    return u.get("first_name") or u.get("username") or "Someone"


# ---- handlers ----------------------------------------------------------------
def on_message(m):
    chat, user, text = m["chat"], m["from"], (m.get("text") or "").strip()
    cid = chat["id"]
    cmd, _, arg = text.partition(" ")
    cmd = cmd.split("@")[0].lower()
    arg = arg.strip()

    if chat["type"] == "private":
        if cmd == "/start" and arg.lstrip("-").isdigit():
            gid = int(arg)
            r = game.current(gid)
            if not r or r["status"] != "open":
                return send(cid, "No round is open in that group right now.")
            dm_target[user["id"]] = gid
            return send(cid, f"<b>The story:</b>\n{esc(r['story'])}\n\nReply with your summary: "
                             f"{MAX_WORDS} words or fewer. I'll add the STOP.")
        if cmd == "/play":
            return send_play(cid, arg)
        if cmd.startswith("/"):
            return send(cid, HELP)
        gid = dm_target.get(user["id"])
        if gid is None:
            return send(cid, "Tap the Submit button under a story in your group first.")
        entry, msg = game.submit(gid, user["id"], name_of(user), text)
        if entry:
            n = len(game.current(gid)["entries"])
            send(cid, f"<b>{esc(entry)}</b>\n{msg} Send another to replace it.")
            send(gid, f"{n} entr{'y' if n == 1 else 'ies'} in so far.")
        else:
            send(cid, msg)
        return

    if cmd == "/newround":
        if not arg:
            return send(cid, "Usage: /newround &lt;the story: headline, summary or link&gt;")
        game.new_round(cid, arg)
        kb = {"inline_keyboard": [[{"text": "Submit your STOP headline",
                                    "url": f"https://t.me/{BOT_USERNAME}?start={cid}"}]]}
        send(cid, f"<b>NEW ROUND</b>\n{esc(arg)}\n\nSummarize it in {MAX_WORDS} words or fewer, "
                  "ending with STOP. Tap below to DM me your entry (it stays secret until voting).",
             reply_markup=kb)
    elif cmd == "/vote":
        err = game.start_voting(cid)
        if err:
            return send(cid, err)
        lines = []
        buttons = []
        for i, (author, text) in enumerate(game.ballot(cid), 1):
            lines.append(f"{i}. {esc(text)}")
            buttons.append([{"text": f"Vote {i}", "callback_data": f"v:{cid}:{author}"}])
        send(cid, "<b>VOTE for the best one</b> (not your own!)\n\n" + "\n".join(lines),
             reply_markup={"inline_keyboard": buttons})
    elif cmd == "/results":
        ranking, err = game.finish(cid)
        if err:
            return send(cid, err)
        top = ranking[0][2]
        out = ["<b>RESULTS</b>"]
        for name, text, votes in ranking:
            crown = "🏆 " if votes == top and top > 0 else ""
            out.append(f"{crown}{esc(text)}\n   by {esc(name)}, {votes} vote{'s' if votes != 1 else ''}")
        if top == 0:
            out.append("\nNobody voted. Tough crowd.")
        send(cid, "\n".join(out))
    elif cmd == "/leaderboard":
        board = game.leaderboard(cid)
        if not board:
            return send(cid, "No finished rounds yet.")
        send(cid, "<b>LEADERBOARD</b>\n" + "\n".join(
            f"{i}. {esc(s['name'])}: {s['wins']} win{'s' if s['wins'] != 1 else ''}, {s['votes']} votes"
            for i, s in enumerate(board, 1)))
    elif cmd == "/play":
        send_play(cid, arg)
    elif cmd in ("/help", "/start"):
        send(cid, HELP)


def send_play(cid, link=""):
    """/play <DN link> -> button that builds the story game. Needs GAME_URL = where server.py is hosted."""
    base = os.environ.get("GAME_URL", "").rstrip("/")
    if not base.startswith("https://"):
        return send(cid, "Set GAME_URL to your hosted server.py address (https, see README).")
    url = f"{base}/?url={urllib.parse.quote(link, safe='')}" if link else f"{base}/today"
    send(cid, "<b>Play the news</b>\nBonk the ? blocks, answer questions about the story, reach Memorial Stadium.",
         reply_markup={"inline_keyboard": [[{"text": "Play (Go Big Red)", "url": url}]]})


def on_callback(q):
    _, gid, author = q["data"].split(":")
    msg = game.vote(int(gid), q["from"]["id"], int(author))
    call("answerCallbackQuery", callback_query_id=q["id"], text=msg, show_alert=msg.startswith("Nice"))


def main():
    global BOT_USERNAME
    BOT_USERNAME = call("getMe")["username"]
    print(f"Running as @{BOT_USERNAME}. Ctrl+C to stop.")
    offset = 0
    while True:
        updates = call("getUpdates", offset=offset, timeout=30) or []
        for u in updates:
            offset = u["update_id"] + 1
            try:
                if "message" in u and "text" in u["message"]:
                    on_message(u["message"])
                elif "callback_query" in u:
                    on_callback(u["callback_query"])
            except Exception as e:
                print("Handler error:", e)


if __name__ == "__main__":
    main()
