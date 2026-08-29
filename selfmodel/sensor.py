"""LLM client and stance sensor.

Endpoint-agnostic: point OPENAI_BASE_URL / model at any OpenAI-compatible
completions endpoint (a local proxy, a hosted provider, etc.). The sensor reads
one line of text and returns a per-mode likelihood plus an evidence scalar,
suitable for feeding selfmodel.filter.dirichlet_step.

Note the `_extract` helper: some reasoning models return their text in a
`reasoning_content` field with an empty `content`. Reading only `content` makes
such a model look like it returns nothing, which silently degrades any loop
built on it. `_extract` falls back to `reasoning_content`. (This was a real bug
in our own first cut; it is preserved here because it will bite anyone
reproducing this against a reasoning model.)
"""
from __future__ import annotations
import json
import os
import time
import urllib.request

from .filter import MODES, normalise

BASE_URL = os.environ.get("OPENAI_BASE_URL", "http://127.0.0.1:8001/v1")
MODEL = os.environ.get("SELFMODEL_MODEL", "gpt-4o-mini")
API_KEY = os.environ.get("OPENAI_API_KEY", "")


def _extract(resp: dict) -> str:
    msg = ((resp.get("choices") or [{}])[0].get("message") or {})
    return ((msg.get("content") or msg.get("reasoning_content") or "").strip())


def chat(system: str, user: str, temperature: float = 0.7,
         max_tokens: int = 400, model: str | None = None) -> str:
    body = json.dumps({
        "model": model or MODEL,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": ([{"role": "system", "content": system}] if system else [])
        + [{"role": "user", "content": user}],
    }).encode()
    for attempt in (1, 2):
        try:
            req = urllib.request.Request(
                BASE_URL.rstrip("/") + "/chat/completions",
                data=body, headers={"Content-Type": "application/json",
                                    **({"Authorization": "Bearer " + API_KEY}
                                       if API_KEY else {})})
            with urllib.request.urlopen(req, timeout=120) as r:
                out = _extract(json.loads(r.read().decode()))
            if out:
                return out
        except Exception:
            if attempt == 2:
                return ""
            time.sleep(2)
    return ""


SENSOR_SYS = (
    "Classify the stance of one chat line into exactly one mode. "
    "Modes: exploring (opens questions), evaluating (weighs a decision / names "
    "criteria), overwhelmed (narrows scope, drops threads), asserting (commands "
    "one concrete action), disengaging (closes or defers). "
    'Answer JSON only: {"mode":"<mode>","confidence":<0..1>}'
)


def stance_likelihood(text: str, model: str | None = None):
    """Return (likelihood dict over MODES, evidence scalar) or (None, 0.0)."""
    text = (text or "").strip()
    if len(text) < 8:
        return None, 0.0
    out = chat(SENSOR_SYS, text[:800], temperature=0.0, max_tokens=60, model=model)
    if not out:
        return None, 0.0
    try:
        o = json.loads(out[out.find("{"): out.rfind("}") + 1])
        m = str(o.get("mode", "")).lower()
        c = float(o.get("confidence") or 0.5)
        if m in MODES:
            raw = {k: 0.15 for k in MODES}
            raw[m] += 1.0 + c
            return normalise(raw), max(0.32, min(1.15, 0.4 + 0.7 * c))
    except Exception:
        pass
    return None, 0.0
