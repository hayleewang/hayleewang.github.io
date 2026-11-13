"""Game logic for "Ten Words. STOP." -- no Telegram code in here, so it's easy to test.

Rules: summarize a news story in 10 words or fewer, ending with STOP
(the word STOP itself doesn't count toward the 10, like a telegram).
Everyone votes on the best one. You can't vote for your own.
"""
import json
import os
import re

MAX_WORDS = 10
STOP = "STOP"


def clean_entry(text):
    """Return (entry, error). Adds the closing STOP if the player forgot it."""
    text = " ".join(text.split())
    text = re.sub(r"[\s.!?,;:]*\bstop\b[\s.!?]*$", "", text, flags=re.I).strip()
    words = text.split()
    if not words:
        return None, "Send me a summary first!"
    if len(words) > MAX_WORDS:
        return None, f"That's {len(words)} words. Cut it to {MAX_WORDS} or fewer (STOP doesn't count)."
    return f"{text} {STOP}.", None


class Game:
    def __init__(self, path="state.json"):
        self.path = path
        self.chats = {}
        if os.path.exists(path):
            with open(path) as f:
                self.chats = json.load(f)

    def save(self):
        tmp = self.path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(self.chats, f, indent=2)
        os.replace(tmp, self.path)

    def chat(self, chat_id):
        return self.chats.setdefault(str(chat_id), {"round": None, "scores": {}})

    # ---- round lifecycle -------------------------------------------------
    def new_round(self, chat_id, story):
        c = self.chat(chat_id)
        c["round"] = {"story": story, "status": "open", "entries": {}, "votes": {}}
        self.save()

    def current(self, chat_id):
        return self.chat(chat_id)["round"]

    def submit(self, chat_id, user_id, name, text):
        r = self.current(chat_id)
        if not r or r["status"] != "open":
            return None, "Submissions are closed for that round."
        entry, err = clean_entry(text)
        if err:
            return None, err
        replaced = str(user_id) in r["entries"]
        r["entries"][str(user_id)] = {"name": name, "text": entry}
        self.save()
        return entry, ("Updated! " if replaced else "") + "Locked in."

    def start_voting(self, chat_id):
        r = self.current(chat_id)
        if not r or r["status"] != "open":
            return "No open round to vote on. Start one with /newround."
        if len(r["entries"]) < 2:
            return "Need at least 2 entries before voting can start."
        r["status"] = "voting"
        self.save()
        return None

    def ballot(self, chat_id):
        """Entries in a stable order, anonymous: [(author_id, text)]."""
        r = self.current(chat_id)
        return sorted(((a, e["text"]) for a, e in r["entries"].items()), key=lambda x: x[1].lower())

    def vote(self, chat_id, voter_id, author_id):
        r = self.current(chat_id)
        if not r or r["status"] != "voting":
            return "Voting isn't open."
        if str(author_id) not in r["entries"]:
            return "That entry doesn't exist."
        if str(voter_id) == str(author_id):
            return "Nice try -- you can't vote for your own."
        r["votes"][str(voter_id)] = str(author_id)
        self.save()
        return "Vote recorded (tap another to change it)."

    def finish(self, chat_id):
        """Close the round. Returns (ranking, error); ranking = [(name, text, votes)]."""
        r = self.current(chat_id)
        if not r or r["status"] != "voting":
            return None, "No round in voting. Use /vote first."
        tally = {a: 0 for a in r["entries"]}
        for author in r["votes"].values():
            tally[author] += 1
        ranking = sorted(
            ((r["entries"][a]["name"], r["entries"][a]["text"], n, a) for a, n in tally.items()),
            key=lambda x: -x[2],
        )
        top = ranking[0][2] if ranking else 0
        scores = self.chat(chat_id)["scores"]
        for name, _, n, a in ranking:
            s = scores.setdefault(a, {"name": name, "wins": 0, "votes": 0})
            s["name"] = name
            s["votes"] += n
            if n == top and top > 0:
                s["wins"] += 1
        r["status"] = "closed"
        self.save()
        return [(n, t, v) for n, t, v, _ in ranking], None

    def leaderboard(self, chat_id):
        scores = self.chat(chat_id)["scores"].values()
        return sorted(scores, key=lambda s: (-s["wins"], -s["votes"]))
