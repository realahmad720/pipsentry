"""Session Clock (Section 19 page 10): Asian/London/New York session times
and overlaps, in UTC — pure calendar math, no external data source."""

from datetime import datetime, timezone

# (name, open_hour_utc, close_hour_utc) — standard approximations, not
# adjusted for regional daylight-saving shifts.
SESSIONS = [
    ("Asian (Tokyo)", 0, 9),
    ("London", 8, 17),
    ("New York", 13, 22),
]


def session_status(now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    hour = now.hour + now.minute / 60

    open_sessions = [name for name, start, end in SESSIONS if start <= hour < end]
    overlaps = []
    for i, (name_a, start_a, end_a) in enumerate(SESSIONS):
        for name_b, start_b, end_b in SESSIONS[i + 1 :]:
            if start_a < end_b and start_b < end_a and name_a in open_sessions and name_b in open_sessions:
                overlaps.append(f"{name_a} / {name_b}")

    return {
        "utc_time": now.isoformat(),
        "open_sessions": open_sessions,
        "overlaps": overlaps,
        "sessions": [{"name": n, "open_hour_utc": s, "close_hour_utc": e} for n, s, e in SESSIONS],
    }
