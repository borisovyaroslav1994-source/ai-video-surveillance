import json
import os
from datetime import datetime

import requests


# ============================================================
# НАЛАШТУВАННЯ
# ============================================================

# Laravel API
LARAVEL_API_URL = "http://diplom.local/api/events"

# Таймаут запиту до Laravel
REQUEST_TIMEOUT = 5

# Локальна резервна копія
LOG_DIR = "events"
LOG_FILE = os.path.join(LOG_DIR, "events.json")


# ============================================================
# ДОПОМІЖНІ ФУНКЦІЇ
# ============================================================

def _ensure_log_directory():
    """
    Створює директорію events, якщо її ще немає.
    """
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
    except OSError as e:
        print(f"Помилка створення директорії {LOG_DIR}: {e}")


def _load_events():
    """
    Завантажує локальний events.json.
    """
    _ensure_log_directory()

    if not os.path.exists(LOG_FILE):
        return []

    try:
        with open(
            LOG_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if not isinstance(data, list):
            print("events.json має неправильний формат")
            return []

        return data

    except json.JSONDecodeError as e:

        print(
            f"Помилка JSON у {LOG_FILE}: {e}"
        )

        return []

    except OSError as e:

        print(
            f"Помилка читання {LOG_FILE}: {e}"
        )

        return []


def _save_events(events):
    """
    Зберігає локальний events.json.
    """
    _ensure_log_directory()

    try:

        with open(
            LOG_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                events,
                file,
                indent=4,
                ensure_ascii=False
            )

        return True

    except OSError as e:

        print(
            f"Помилка запису {LOG_FILE}: {e}"
        )

        return False


def _get_next_event_id(events):
    """
    Генерує наступний локальний ID події.
    """

    max_id = 0

    for event in events:

        if not isinstance(event, dict):
            continue

        try:

            event_id = int(
                event.get("id", 0)
            )

            if event_id > max_id:
                max_id = event_id

        except (
            TypeError,
            ValueError
        ):
            continue

    return max_id + 1


# ============================================================
# LARAVEL API
# ============================================================

def _save_to_laravel(
    camera_id,
    camera_name,
    object_name,
    track_id,
    confidence,
    bbox,
    image_path,
    status,
    detected_at
):
    """
    Відправляє подію в Laravel API.

    Повертає:
        dict  - якщо Laravel успішно створив подію
        None  - якщо сталася помилка
    """

    if camera_id is None:

        print(
            "Laravel: camera_id не задано"
        )

        return None

    try:

        camera_id = int(camera_id)

    except (
        TypeError,
        ValueError
    ):

        print(
            f"Laravel: неправильний camera_id: {camera_id}"
        )

        return None

    if not isinstance(bbox, dict):
        bbox = {}

    # --------------------------------------------------------
    # Формуємо JSON для Laravel
    # --------------------------------------------------------

    payload = {

        "camera_id": camera_id,

        "camera_name": (
            camera_name
            if camera_name
            else f"Camera {camera_id}"
        ),

        "object": str(
            object_name
            if object_name
            else "unknown"
        ),

        "track_id": (
            int(track_id)
            if track_id is not None
            else None
        ),

        "confidence": round(
            float(confidence),
            4
        ),

        "bbox_x1": int(
            bbox.get("x1", 0)
        ),

        "bbox_y1": int(
            bbox.get("y1", 0)
        ),

        "bbox_x2": int(
            bbox.get("x2", 0)
        ),

        "bbox_y2": int(
            bbox.get("y2", 0)
        ),

        "image": image_path,

        "status": (
            status
            if status
            else "active"
        ),

        "detected_at": detected_at
    }

    # --------------------------------------------------------
    # POST → Laravel
    # --------------------------------------------------------

    try:

        print(
            f"Відправка події в Laravel: "
            f"{LARAVEL_API_URL}"
        )

        response = requests.post(
            LARAVEL_API_URL,
            json=payload,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            timeout=REQUEST_TIMEOUT
        )

        # ----------------------------------------------------
        # Перевірка HTTP
        # ----------------------------------------------------

        if response.status_code not in (
            200,
            201
        ):

            print(
                "Laravel API помилка:"
                f" HTTP {response.status_code}"
            )

            print(
                f"Відповідь Laravel: "
                f"{response.text}"
            )

            return None

        # ----------------------------------------------------
        # JSON-відповідь
        # ----------------------------------------------------

        try:

            data = response.json()

        except ValueError:

            print(
                "Laravel повернув не JSON"
            )

            print(
                response.text
            )

            return None

        if not data.get("success"):

            print(
                "Laravel не підтвердив "
                "збереження події"
            )

            print(data)

            return None

        event = data.get(
            "event"
        )

        print()
        print(
            "=" * 60
        )
        print(
            "ПОДІЮ ЗБЕРЕЖЕНО В LARAVEL"
        )
        print(
            "=" * 60
        )

        if isinstance(event, dict):

            print(
                f"Laravel Event ID: "
                f"{event.get('id')}"
            )

            print(
                f"Камера: "
                f"{event.get('camera_name')}"
            )

            print(
                f"Об'єкт: "
                f"{event.get('object')}"
            )

            print(
                f"Track ID: "
                f"{event.get('track_id')}"
            )

            print(
                f"Confidence: "
                f"{event.get('confidence')}"
            )

        print(
            "=" * 60
        )

        return event

    except requests.exceptions.Timeout:

        print(
            "Laravel API: "
            "таймаут підключення"
        )

        return None

    except requests.exceptions.ConnectionError:

        print(
            "Laravel API: "
            "не вдалося підключитися"
        )

        return None

    except requests.exceptions.RequestException as e:

        print(
            f"Laravel API помилка: {e}"
        )

        return None

    except Exception as e:

        print(
            f"Невідома помилка Laravel API: {e}"
        )

        return None


# ============================================================
# LOCAL BACKUP
# ============================================================

def _save_to_local(
    camera_id,
    camera_name,
    object_id,
    object_name,
    confidence,
    bbox,
    image_path,
    status,
    detected_at,
    laravel_event=None
):
    """
    Зберігає подію у локальний events.json.
    """

    events = _load_events()

    local_event_id = _get_next_event_id(
        events
    )

    # Якщо Laravel вже створив подію,
    # зберігаємо його ID окремо.
    laravel_event_id = None

    if isinstance(
        laravel_event,
        dict
    ):

        laravel_event_id = laravel_event.get(
            "id"
        )

    if not isinstance(
        bbox,
        dict
    ):
        bbox = {}

    try:

        confidence = float(
            confidence
        )

    except (
        TypeError,
        ValueError
    ):

        confidence = 0.0

    # --------------------------------------------------------
    # Локальна подія
    # --------------------------------------------------------

    event = {

        # Локальний ID
        "id": local_event_id,

        # ID Laravel
        "laravel_id": laravel_event_id,

        # YOLO Track ID
        "track_id": object_id,

        # ID камери
        "camera_id": camera_id,

        # Назва камери
        "camera": (
            camera_name
            if camera_name
            else f"Camera {camera_id}"
        ),

        # Об'єкт
        "object": (
            object_name
            if object_name
            else "unknown"
        ),

        # Confidence
        "confidence": round(
            confidence,
            2
        ),

        # Bounding Box
        "bbox": {

            "x1": int(
                bbox.get("x1", 0)
            ),

            "y1": int(
                bbox.get("y1", 0)
            ),

            "x2": int(
                bbox.get("x2", 0)
            ),

            "y2": int(
                bbox.get("y2", 0)
            )
        },

        # Фото
        "image": image_path,

        # Статус
        "status": (
            status
            if status
            else "active"
        ),

        # Час
        "time": detected_at
    }

    events.append(
        event
    )

    if not _save_events(events):

        return None

    return event


# ============================================================
# ОСНОВНА ФУНКЦІЯ
# ============================================================

def save_event(
    object_id,
    object_name,
    confidence,
    bbox,
    image_path,
    camera_id,
    camera_name=None,
    status="active"
):
    """
    Створює подію.

    Основне:
        Laravel API

    Резерв:
        events/events.json

    Параметри:

        object_id
            YOLO Track ID

        object_name
            Назва об'єкта:
            person, car, truck...

        confidence
            Confidence YOLO

        bbox
            Координати об'єкта

        image_path
            Шлях до фото

        camera_id
            ID камери з Laravel

        camera_name
            Назва камери

        status
            Статус події
    """

    # ========================================================
    # ЧАС ПОДІЇ
    # ========================================================

    detected_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    # ========================================================
    # НОРМАЛІЗАЦІЯ ДАНИХ
    # ========================================================

    try:

        camera_id = int(
            camera_id
        )

    except (
        TypeError,
        ValueError
    ):

        print(
            f"Помилка: неправильний camera_id: "
            f"{camera_id}"
        )

        camera_id = None

    try:

        object_id = int(
            object_id
        )

    except (
        TypeError,
        ValueError
    ):

        object_id = None

    try:

        confidence = float(
            confidence
        )

    except (
        TypeError,
        ValueError
    ):

        confidence = 0.0

    if not isinstance(
        bbox,
        dict
    ):

        bbox = {}

    # ========================================================
    # ВИВІД ПОДІЇ
    # ========================================================

    print()
    print(
        "=" * 60
    )
    print(
        "НОВА ПОДІЯ"
    )
    print(
        "=" * 60
    )
    print(
        f"Камера: {camera_name}"
    )
    print(
        f"Camera ID: {camera_id}"
    )
    print(
        f"Об'єкт: {object_name}"
    )
    print(
        f"Track ID: {object_id}"
    )
    print(
        f"Confidence: {confidence:.2f}"
    )
    print(
        f"Час: {detected_at}"
    )
    print(
        "=" * 60
    )

    # ========================================================
    # 1. LARAVEL
    # ========================================================

    laravel_event = _save_to_laravel(

        camera_id=camera_id,

        camera_name=camera_name,

        object_name=object_name,

        track_id=object_id,

        confidence=confidence,

        bbox=bbox,

        image_path=image_path,

        status=status,

        detected_at=detected_at
    )

    # ========================================================
    # 2. ЛОКАЛЬНИЙ BACKUP
    # ========================================================

    local_event = _save_to_local(

        camera_id=camera_id,

        camera_name=camera_name,

        object_id=object_id,

        object_name=object_name,

        confidence=confidence,

        bbox=bbox,

        image_path=image_path,

        status=status,

        detected_at=detected_at,

        laravel_event=laravel_event
    )

    # ========================================================
    # РЕЗУЛЬТАТ
    # ========================================================

    if laravel_event is not None:

        print(
            "✓ Подію збережено в Laravel"
        )

    else:

        print(
            "⚠ Laravel недоступний"
        )

    if local_event is not None:

        print(
            f"✓ Резервна копія: {LOG_FILE}"
        )

    else:

        print(
            "✗ Не вдалося створити "
            "локальну резервну копію"
        )

    print()

    # Laravel має пріоритет
    if laravel_event is not None:

        return laravel_event

    # Якщо Laravel недоступний,
    # повертаємо локальну подію
    if local_event is not None:

        return local_event

    return None


# ============================================================
# ОТРИМАННЯ ПОДІЙ
# ============================================================

def get_events():
    """
    Повертає локальні резервні події.
    """

    return _load_events()


def get_latest_events(limit=50):
    """
    Повертає останні локальні події.
    """

    events = _load_events()

    try:

        limit = int(
            limit
        )

    except (
        TypeError,
        ValueError
    ):

        limit = 50

    if limit <= 0:

        return []

    return events[-limit:]


# ============================================================
# ЗАКРИТТЯ ПОДІЇ
# ============================================================

def close_event(event_id):
    """
    Закриває локальну подію.

    Laravel-подію краще закривати через:
        POST /api/events/{id}/close
    """

    events = _load_events()

    changed = False

    for event in events:

        if not isinstance(
            event,
            dict
        ):
            continue

        try:

            current_id = int(
                event.get("id")
            )

        except (
            TypeError,
            ValueError
        ):

            continue

        try:

            requested_id = int(
                event_id
            )

        except (
            TypeError,
            ValueError
        ):

            return False

        if current_id == requested_id:

            event["status"] = "completed"

            event["end_time"] = (
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )

            changed = True

            break

    if not changed:

        return False

    return _save_events(
        events
    )
