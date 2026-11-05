"""Bounded, policy-injected chat admission; no provider or HTTP integration."""

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
import hashlib
import threading
import uuid


def _as_utc(value):
    if (not isinstance(value, datetime) or value.tzinfo is None
            or value.utcoffset() is None):
        raise ValueError("clock must return a timezone-aware datetime")
    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class AdmissionPolicy:
    max_concurrent: int
    max_queue: int
    calls_per_minute: int
    calls_per_day: int
    ticket_ttl_seconds: int
    claim_ttl_seconds: int
    scope: str = "default"

    def __post_init__(self):
        for name in ("max_concurrent", "calls_per_minute", "calls_per_day",
                     "ticket_ttl_seconds", "claim_ttl_seconds"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"{name} must be a positive integer")
        if isinstance(self.max_queue, bool) or not isinstance(self.max_queue, int) or self.max_queue < 0:
            raise ValueError("max_queue must be a non-negative integer")
        if not isinstance(self.scope, str) or not self.scope.strip():
            raise ValueError("scope must be a non-empty string")


class InMemoryBudgetState:
    """Explicitly initialized in-memory budget counter, not a shared store."""

    def __init__(self, scope, *, _initialized=False):
        self.scope = scope
        self._ready = _initialized
        self._minute_window = None
        self._minute_calls = 0
        self._day_utc = None
        self._day_calls = 0
        self._lock = threading.RLock()

    @classmethod
    def new_empty(cls, *, scope):
        """Explicitly start a new budget epoch; do not use on an unknown restart."""
        if not isinstance(scope, str) or not scope.strip():
            raise ValueError("scope must be a non-empty string")
        return cls(scope, _initialized=True)

    @property
    def ready(self):
        return self._ready

    @classmethod
    def restore(cls, snapshot, *, expected_scope):
        """Restore a validated export; caller owns durable/shared storage."""
        required = {"schema_version", "scope", "minute_window", "calls_minute", "day_utc", "calls_day"}
        if not isinstance(snapshot, dict) or set(snapshot) != required:
            raise ValueError("budget snapshot shape is invalid")
        if (snapshot["schema_version"] != 1 or isinstance(snapshot["schema_version"], bool)
                or snapshot["scope"] != expected_scope
                or not isinstance(expected_scope, str) or not expected_scope.strip()):
            raise ValueError("budget snapshot version or scope is invalid")
        minute_window = snapshot["minute_window"]
        if (minute_window is not None and
                (isinstance(minute_window, bool) or not isinstance(minute_window, int))):
            raise ValueError("minute_window must be an integer or null")
        day_utc = snapshot["day_utc"]
        if day_utc is not None:
            if not isinstance(day_utc, str):
                raise ValueError("day_utc must be an ISO UTC date or null")
            try:
                if date.fromisoformat(day_utc).isoformat() != day_utc:
                    raise ValueError("day_utc must be a canonical ISO date")
            except ValueError as exc:
                raise ValueError("day_utc must be a canonical ISO date") from exc
        for name in ("calls_minute", "calls_day"):
            value = snapshot[name]
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if ((minute_window is None) != (snapshot["calls_minute"] == 0)
                or (day_utc is None) != (snapshot["calls_day"] == 0)):
            raise ValueError("budget snapshot counters and window keys disagree")
        state = cls(expected_scope, _initialized=True)
        state._minute_window = minute_window
        state._minute_calls = snapshot["calls_minute"]
        state._day_utc = day_utc
        state._day_calls = snapshot["calls_day"]
        return state

    def export_state(self):
        with self._lock:
            if not self._ready:
                raise ValueError("budget state is not initialized")
            return {
                "schema_version": 1, "scope": self.scope,
                "minute_window": self._minute_window, "calls_minute": self._minute_calls,
                "day_utc": self._day_utc, "calls_day": self._day_calls,
            }

    def reserve(self, policy, now):
        now = _as_utc(now)
        with self._lock:
            if not self._ready or self.scope != policy.scope:
                return "state_unavailable"
            minute_window = int(now.timestamp()) // 60
            day_utc = now.date().isoformat()
            if ((self._minute_window is not None and minute_window < self._minute_window)
                    or (self._day_utc is not None and day_utc < self._day_utc)):
                return "state_unavailable"
            if self._minute_window != minute_window:
                self._minute_window = minute_window
                self._minute_calls = 0
            if self._day_utc != day_utc:
                self._day_utc = day_utc
                self._day_calls = 0
            if (self._minute_calls >= policy.calls_per_minute
                    or self._day_calls >= policy.calls_per_day):
                return "quota_exhausted"
            self._minute_calls += 1
            self._day_calls += 1
            return "reserved"

    def status(self, now):
        now = _as_utc(now)
        with self._lock:
            minute_window = int(now.timestamp()) // 60
            day_utc = now.date().isoformat()
            if (not self._ready
                    or (self._minute_window is not None and minute_window < self._minute_window)
                    or (self._day_utc is not None and day_utc < self._day_utc)):
                raise ValueError("budget state or clock is unavailable")
            return {
                "calls_minute": self._minute_calls if self._minute_window == minute_window else 0,
                "calls_day": self._day_calls if self._day_utc == day_utc else 0,
            }


class InterfazChatAdmission:
    def __init__(self, policy=None, clock=None, *, budget_state=None):
        self._policy = policy
        self._clock = clock
        self._budget_state = budget_state
        self._lock = threading.RLock()
        self._tickets = {}
        self._queue = []
        self._idempotency = {}

    def _state_available(self):
        state = self._budget_state
        return (self._policy is not None and callable(self._clock)
                and getattr(state, "ready", False) is True
                and getattr(state, "scope", None) == self._policy.scope
                and callable(getattr(state, "reserve", None))
                and callable(getattr(state, "status", None)))

    def _budget_reserve(self, now):
        try:
            result = self._budget_state.reserve(self._policy, now)
        except Exception:
            return "state_unavailable"
        return result if result in {"reserved", "quota_exhausted", "state_unavailable"} else "state_unavailable"

    def _budget_status(self, now):
        try:
            result = self._budget_state.status(now)
        except Exception:
            return None
        if (not isinstance(result, dict)
                or any(isinstance(result.get(key), bool) or not isinstance(result.get(key), int)
                       or result.get(key) < 0 for key in ("calls_minute", "calls_day"))):
            return None
        return {"calls_minute": result["calls_minute"], "calls_day": result["calls_day"]}

    def _now(self):
        try:
            return _as_utc(self._clock())
        except Exception:
            return None

    def _active_count(self):
        return sum(ticket["state"] in {"admitted", "claimed"}
                   for ticket in self._tickets.values())

    def _queued_count(self):
        return sum(self._tickets[ticket_id]["state"] == "queued"
                   for ticket_id in self._queue if ticket_id in self._tickets)

    def _position(self, ticket_id):
        position = 0
        for queued_id in self._queue:
            ticket = self._tickets.get(queued_id)
            if ticket and ticket["state"] == "queued":
                position += 1
                if queued_id == ticket_id:
                    return position
        return None

    def _mark_expired(self, ticket, now):
        ticket["state"] = "expired"
        ticket["retire_at"] = now + timedelta(seconds=self._policy.ticket_ttl_seconds)

    def _prune(self, now):
        remove_ids = []
        for ticket_id, ticket in self._tickets.items():
            if ticket["state"] in {"queued", "admitted"} and now >= ticket["expires_at"]:
                self._mark_expired(ticket, now)
            elif ticket["state"] == "claimed" and now >= ticket["lease_expires_at"]:
                self._mark_expired(ticket, now)
            elif (ticket["state"] in {"completed", "cancelled", "expired"}
                    and ticket.get("retire_at") is not None and now >= ticket["retire_at"]):
                remove_ids.append(ticket_id)
        for ticket_id in remove_ids:
            self._idempotency_by_ticket_cleanup(ticket_id)
            del self._tickets[ticket_id]
        self._queue = [ticket_id for ticket_id in self._queue
                       if ticket_id in self._tickets and self._tickets[ticket_id]["state"] == "queued"]

    def _idempotency_by_ticket_cleanup(self, ticket_id):
        ticket = self._tickets.get(ticket_id, {})
        digest = ticket.get("idempotency_digest")
        if digest is not None and self._idempotency.get(digest) == ticket_id:
            del self._idempotency[digest]

    def _promote(self, now):
        while self._queue and self._active_count() < self._policy.max_concurrent:
            ticket_id = self._queue[0]
            ticket = self._tickets[ticket_id]
            if now >= ticket["expires_at"]:
                self._mark_expired(ticket, now)
                self._queue.pop(0)
                continue
            reserved = self._budget_reserve(now)
            if reserved != "reserved":
                return reserved
            self._queue.pop(0)
            ticket["state"] = "admitted"
            ticket["reserved_calls"] = 1
            ticket["admitted_at"] = now
        return "admitted"

    def _new_ticket(self, now, idempotency_digest=None):
        ticket_id = uuid.uuid4().hex
        self._tickets[ticket_id] = {
            "state": "queued", "created_at": now,
            "expires_at": now + timedelta(seconds=self._policy.ticket_ttl_seconds),
            "reserved_calls": 0, "retire_at": None,
            "idempotency_digest": idempotency_digest,
        }
        self._queue.append(ticket_id)
        if idempotency_digest is not None:
            self._idempotency[idempotency_digest] = ticket_id
        return ticket_id

    def submit(self, *, idempotency_key=None):
        if self._policy is None:
            return {"code": "disabled", "ticket": None}
        if not self._state_available():
            return {"code": "state_unavailable", "ticket": None}
        if idempotency_key is not None and (
                not isinstance(idempotency_key, str) or not idempotency_key
                or len(idempotency_key) > 128):
            return {"code": "invalid_request", "ticket": None}
        digest = (hashlib.sha256(idempotency_key.encode("utf-8")).hexdigest()
                  if idempotency_key is not None else None)
        with self._lock:
            now = self._now()
            if now is None:
                return {"code": "state_unavailable", "ticket": None}
            self._prune(now)
            if digest is not None and digest in self._idempotency:
                duplicate_id = self._idempotency[digest]
                return {"code": "duplicate", "ticket": duplicate_id,
                        "position": self._position(duplicate_id)}
            promoted = self._promote(now)
            if promoted == "state_unavailable":
                return {"code": promoted, "ticket": None}
            if self._queue and self._queued_count() >= self._policy.max_queue:
                return {"code": "queue_full", "ticket": None}
            ticket_id = self._new_ticket(now, digest)
            promoted = self._promote(now)
            ticket = self._tickets[ticket_id]
            if ticket["state"] == "admitted":
                return {"code": "admitted", "ticket": ticket_id, "position": None}
            if promoted == "state_unavailable":
                self._queue.remove(ticket_id)
                self._idempotency_by_ticket_cleanup(ticket_id)
                del self._tickets[ticket_id]
                return {"code": "state_unavailable", "ticket": None}
            if self._policy.max_queue == 0:
                self._queue.remove(ticket_id)
                self._idempotency_by_ticket_cleanup(ticket_id)
                del self._tickets[ticket_id]
                return {"code": "quota_exhausted" if promoted == "quota_exhausted"
                        else "queue_full", "ticket": None}
            position = self._position(ticket_id)
            code = "quota_exhausted" if promoted == "quota_exhausted" and position == 1 else "queued"
            return {"code": code, "ticket": ticket_id, "position": position}

    def claim(self, ticket_id):
        if self._policy is None:
            return {"code": "disabled", "ticket": None}
        if not self._state_available():
            return {"code": "state_unavailable", "ticket": ticket_id}
        with self._lock:
            now = self._now()
            if now is None:
                return {"code": "state_unavailable", "ticket": ticket_id}
            self._prune(now)
            ticket = self._tickets.get(ticket_id)
            if ticket is None:
                return {"code": "ticket_invalid", "ticket": ticket_id}
            if ticket["state"] == "queued":
                promoted = self._promote(now)
                if promoted == "state_unavailable":
                    return {"code": promoted, "ticket": ticket_id}
                if ticket["state"] == "queued":
                    position = self._position(ticket_id)
                    code = "quota_exhausted" if promoted == "quota_exhausted" and position == 1 else "queued"
                    return {"code": code, "ticket": ticket_id, "position": position}
            if ticket["state"] == "admitted":
                ticket["state"] = "claimed"
                ticket["claimed_at"] = now
                ticket["lease_expires_at"] = now + timedelta(seconds=self._policy.claim_ttl_seconds)
                return {"code": "claimed", "ticket": ticket_id,
                        "reserved_calls": ticket["reserved_calls"]}
            if ticket["state"] == "expired":
                return {"code": "expired", "ticket": ticket_id}
            return {"code": "duplicate", "ticket": ticket_id}

    def reserve_provider_call(self, ticket_id):
        """Reserve one additional upstream call before a tool-follow-up dispatch."""
        if self._policy is None:
            return {"code": "disabled", "ticket": None}
        if not self._state_available():
            return {"code": "state_unavailable", "ticket": ticket_id}
        with self._lock:
            now = self._now()
            if now is None:
                return {"code": "state_unavailable", "ticket": ticket_id}
            self._prune(now)
            ticket = self._tickets.get(ticket_id)
            if ticket is None:
                return {"code": "ticket_invalid", "ticket": ticket_id}
            if ticket["state"] == "expired":
                return {"code": "expired", "ticket": ticket_id}
            if ticket["state"] != "claimed":
                return {"code": "ticket_invalid", "ticket": ticket_id}
            reserved = self._budget_reserve(now)
            if reserved != "reserved":
                return {"code": reserved, "ticket": ticket_id}
            ticket["reserved_calls"] += 1
            return {"code": "reserved", "ticket": ticket_id,
                    "provider_call_number": ticket["reserved_calls"]}

    def cancel(self, ticket_id):
        if self._policy is None:
            return {"code": "disabled", "ticket": None}
        if not self._state_available():
            return {"code": "state_unavailable", "ticket": ticket_id}
        with self._lock:
            now = self._now()
            if now is None:
                return {"code": "state_unavailable", "ticket": ticket_id}
            self._prune(now)
            ticket = self._tickets.get(ticket_id)
            if ticket is None:
                return {"code": "ticket_invalid", "ticket": ticket_id}
            if ticket["state"] == "expired":
                return {"code": "expired", "ticket": ticket_id}
            if ticket["state"] in {"completed", "cancelled"}:
                return {"code": "duplicate", "ticket": ticket_id}
            ticket["state"] = "cancelled"
            ticket["retire_at"] = now + timedelta(seconds=self._policy.ticket_ttl_seconds)
            self._queue = [queued_id for queued_id in self._queue if queued_id != ticket_id]
            promoted = self._promote(now)
            return {"code": "cancelled", "ticket": ticket_id,
                    "promotion": promoted}

    def complete(self, ticket_id):
        if self._policy is None:
            return {"code": "disabled", "ticket": None}
        if not self._state_available():
            return {"code": "state_unavailable", "ticket": ticket_id}
        with self._lock:
            now = self._now()
            if now is None:
                return {"code": "state_unavailable", "ticket": ticket_id}
            self._prune(now)
            ticket = self._tickets.get(ticket_id)
            if ticket is None:
                return {"code": "ticket_invalid", "ticket": ticket_id}
            if ticket["state"] == "expired":
                return {"code": "expired", "ticket": ticket_id}
            if ticket["state"] in {"completed", "cancelled"}:
                return {"code": "duplicate", "ticket": ticket_id}
            if ticket["state"] == "queued":
                return {"code": "queued", "ticket": ticket_id,
                        "position": self._position(ticket_id)}
            ticket["state"] = "completed"
            ticket["retire_at"] = now + timedelta(seconds=self._policy.ticket_ttl_seconds)
            promoted = self._promote(now)
            return {"code": "completed", "ticket": ticket_id,
                    "promotion": promoted}

    def status(self, ticket_id=None):
        if self._policy is None:
            return {"code": "disabled"}
        if not self._state_available():
            return {"code": "state_unavailable"}
        with self._lock:
            now = self._now()
            if now is None:
                return {"code": "state_unavailable"}
            self._prune(now)
            promoted = self._promote(now)
            if promoted == "state_unavailable":
                return {"code": "state_unavailable"}
            counts = self._budget_status(now)
            if counts is None:
                return {"code": "state_unavailable"}
            if ticket_id is not None:
                ticket = self._tickets.get(ticket_id)
                if ticket is None:
                    return {"code": "ticket_invalid", "ticket": ticket_id}
                code = ticket["state"]
                position = self._position(ticket_id) if code == "queued" else None
                if (code == "queued" and position == 1
                        and (counts["calls_minute"] >= self._policy.calls_per_minute
                             or counts["calls_day"] >= self._policy.calls_per_day)):
                    code = "quota_exhausted"
                return {"code": code, "ticket": ticket_id, "position": position,
                        "active": self._active_count(), "queued": self._queued_count(), **counts}
            return {"code": "active", "active": self._active_count(),
                    "queued": self._queued_count(), **counts}
