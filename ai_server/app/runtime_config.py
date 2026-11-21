"""Робочі налаштування Recorder з Laravel (єдине джерело правди).

Панель зберігає segment_seconds / record_max_* / transcode_* у БД,
віддає через GET /api/recorder-settings. Цей модуль тягне їх
з кешем 60 сек і віддає гетерами з клампами.

При недоступності API — працює на дефолтах (як зараз
захардкоджено в recorder.py). Поведінка не гіршає.

Застосування налаштувань:
- segment_seconds — при наступній ротації сегмента
  (поточний файл не ріжемо посеред запису);
- record_max_* — для НОВИХ сегментів (розмір VideoWriter
  фіксується при створенні файлу);
- transcode_* — для файлів, що стануть у чергу ПІСЛЯ зміни.
"""

import time

import requests


SETTINGS_URL = "http://diplom.local/api/recorder-settings"

FETCH_INTERVAL = 60

REQUEST_TIMEOUT = 5

ALLOWED_PRESETS = (
    "ultrafast",
    "superfast",
    "veryfast",
    "faster",
    "fast",
    "medium",
    "slow",
    "slower",
    "veryslow",
)

_DEFAULTS = {
    "segment_seconds": 300,
    "record_max_width": 1280,
    "record_max_height": 720,
    "transcode_crf": 28,
    "transcode_preset": "veryfast",
    "default_confidence": 0.5,
}

_cache = dict(_DEFAULTS)

_last_fetch = 0.0


def _clamp_int(value, default, minimum, maximum):
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default

    # 0 = "вимкнено" для розмірів.
    if number == 0 and minimum == 0:
        return 0

    if number < minimum:
        return minimum

    if number > maximum:
        return maximum

    return number


def _clamp_float(value, default, minimum, maximum):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default

    if number < minimum:
        return minimum

    if number > maximum:
        return maximum

    return number


def refresh(force=False):
    """Підтягнути налаштування з Laravel (з кешем)."""
    global _cache, _last_fetch

    now = time.time()

    if not force and (now - _last_fetch) < FETCH_INTERVAL:
        return dict(_cache)

    try:
        response = requests.get(
            SETTINGS_URL,
            headers={"Accept": "application/json"},
            timeout=REQUEST_TIMEOUT,
        )

        if response.status_code < 200 or response.status_code >= 300:
            _last_fetch = now
            return dict(_cache)

        data = response.json()

        if isinstance(data, dict) and isinstance(
            data.get("settings"), dict
        ):
            payload = data["settings"]
        elif isinstance(data, dict):
            payload = data
        else:
            _last_fetch = now
            return dict(_cache)

        merged = dict(_DEFAULTS)

        merged["segment_seconds"] = _clamp_int(
            payload.get("segment_seconds", merged["segment_seconds"]),
            _DEFAULTS["segment_seconds"],
            30,
            3600,
        )

        merged["record_max_width"] = _clamp_int(
            payload.get("record_max_width", merged["record_max_width"]),
            _DEFAULTS["record_max_width"],
            0,
            3840,
        )

        merged["record_max_height"] = _clamp_int(
            payload.get("record_max_height", merged["record_max_height"]),
            _DEFAULTS["record_max_height"],
            0,
            2160,
        )

        merged["transcode_crf"] = _clamp_int(
            payload.get("transcode_crf", merged["transcode_crf"]),
            _DEFAULTS["transcode_crf"],
            18,
            32,
        )

        preset = str(
            payload.get(
                "transcode_preset", merged["transcode_preset"]
            )
            or "veryfast"
        ).lower().strip()

        merged["transcode_preset"] = (
            preset if preset in ALLOWED_PRESETS else "veryfast"
        )

        merged["default_confidence"] = _clamp_float(
            payload.get(
                "default_confidence", merged["default_confidence"]
            ),
            _DEFAULTS["default_confidence"],
            0.0,
            1.0,
        )

        if merged != _cache:
            print(f"[Config] Налаштування оновлено: {merged}")

        _cache = merged
        _last_fetch = now

        return dict(_cache)

    except Exception:
        # Laravel недоступний — працюємо на останньому кеші.
        _last_fetch = now
        return dict(_cache)


def get_all():
    return refresh(force=False)


def segment_seconds():
    return int(refresh().get("segment_seconds", 300))


def record_max_size():
    data = refresh()

    try:
        width = int(data.get("record_max_width", 1280))
    except (TypeError, ValueError):
        width = 1280

    try:
        height = int(data.get("record_max_height", 720))
    except (TypeError, ValueError):
        height = 720

    return width, height


def transcode_crf():
    try:
        return int(refresh().get("transcode_crf", 28))
    except (TypeError, ValueError):
        return 28


def transcode_preset():
    preset = str(
        refresh().get("transcode_preset", "veryfast") or "veryfast"
    ).lower().strip()

    return preset if preset in ALLOWED_PRESETS else "veryfast"
