"""Flashcards, review sessions and progress stats (pure Python, testable)."""
import datetime
import json
import re
from collections import deque


def parse_cards(text):
    """Model reply -> [{'q':..,'a':..}, ...]. Tolerates code fences and extra prose."""
    t = re.sub(r"```(?:json)?", "", text or "")
    i, j = t.find("["), t.rfind("]")
    if i < 0 or j <= i:
        return []
    try:
        data = json.loads(t[i:j + 1])
    except ValueError:
        return []
    cards = []
    for c in data:
        if isinstance(c, dict) and str(c.get("q", "")).strip() and str(c.get("a", "")).strip():
            cards.append({"q": str(c["q"]).strip(), "a": str(c["a"]).strip()})
    return cards[:30]


class Session:
    """Wrong answers return to the end of the queue (at most twice per card)."""

    def __init__(self, cards, max_again=2):
        self.cards = cards
        self.queue = deque(range(len(cards)))
        self.fails = {}
        self.max_again = max_again
        self.total = len(cards)
        self.reviewed = 0
        self.known = 0

    def current(self):
        return self.cards[self.queue[0]] if self.queue else None

    def answer(self, known):
        i = self.queue.popleft()
        self.reviewed += 1
        if known:
            self.known += 1
        else:
            self.fails[i] = self.fails.get(i, 0) + 1
            if self.fails[i] <= self.max_again:
                self.queue.append(i)

    @property
    def done(self):
        return not self.queue


def record(stats, day, reviewed, known, topic):
    d = stats.setdefault("days", {}).setdefault(day, {"r": 0, "k": 0})
    d["r"] += reviewed
    d["k"] += known
    t = stats.setdefault("topics", {}).setdefault(topic, {"r": 0, "k": 0})
    t["r"] += reviewed
    t["k"] += known
    return stats


def streak(stats, today):
    """Consecutive days with activity, ending today (or yesterday if today is empty)."""
    days = stats.get("days", {})
    d = datetime.date.fromisoformat(today)
    if days.get(d.isoformat(), {}).get("r", 0) == 0:
        d -= datetime.timedelta(days=1)
    n = 0
    while days.get(d.isoformat(), {}).get("r", 0) > 0:
        n += 1
        d -= datetime.timedelta(days=1)
    return n


def weakest(stats, n=3):
    rows = [(k, v["k"] / v["r"]) for k, v in stats.get("topics", {}).items() if v["r"] >= 3]
    return sorted(rows, key=lambda x: x[1])[:n]
