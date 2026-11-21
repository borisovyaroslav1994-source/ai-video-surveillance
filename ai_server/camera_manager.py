import threading
import time
import requests

from camera_worker import CameraWorker
from app import runtime_config


# ============================================================
# НАЛАШТУВАННЯ
# ============================================================

API_URL = "http://diplom.local/api/cameras"

# Перевірка змін камер у Laravel
API_CHECK_INTERVAL = 5

# Перевірка статусів Worker
STATUS_CHECK_INTERVAL = 2

# Таймаут HTTP-запитів
REQUEST_TIMEOUT = 10


class CameraManager:

    def __init__(self):

        # ====================================================
        # КАМЕРИ З LARAVEL
        # ====================================================

        self.cameras = {}

        # ====================================================
        # WORKERS
        # ====================================================

        self.workers = {}

        # ====================================================
        # СТАН
        # ====================================================

        self.running = False

        # ====================================================
        # LOCK
        # ====================================================

        self.lock = threading.RLock()

        self.camera_operations_lock = threading.RLock()

        # ====================================================
        # ТАЙМЕРИ
        # ====================================================

        self.last_api_check = 0

        self.last_status_check = 0

        # ====================================================
        # ОСТАННІ ВІДПРАВЛЕНІ STATUS
        #
        # Наприклад:
        #
        # {
        #     8: "online",
        #     9: "online",
        #     10: "offline"
        # }
        # ====================================================

        self.last_sent_status = {}

        print("CameraManager створено")

    # ========================================================
    # BOOLEAN
    # ========================================================

    @staticmethod
    def is_bool(value):

        if isinstance(value, bool):
            return value

        if isinstance(value, int):
            return value != 0

        if isinstance(value, str):

            return value.lower() in (
                "1",
                "true",
                "yes",
                "on"
            )

        return False

    # ========================================================
    # FLOAT
    # ========================================================

    @staticmethod
    def normalize_float(value, default=0.5):

        try:
            return float(value)

        except (
            TypeError,
            ValueError
        ):
            return default

    # ========================================================
    # SOURCE
    # ========================================================

    @staticmethod
    def normalize_source(source):

        if source is None:
            return ""

        source = str(source).strip()

        # USB:
        # "0" -> 0
        # "1" -> 1

        if source.isdigit():
            return int(source)

        return source

    # ========================================================
    # CAMERA FINGERPRINT
    #
    # Визначає, чи змінилася конфігурація камери.
    # ========================================================

    @classmethod
    def get_camera_fingerprint(cls, camera):

        return (
            camera.get("name"),

            camera.get("type"),

            str(
                camera.get("source")
            ),

            camera.get("location"),

            cls.normalize_float(
                camera.get(
                    "confidence_threshold",
                    0.5
                )
            ),

            cls.is_bool(
                camera.get(
                    "enabled",
                    True
                )
            ),

            cls.is_bool(
                camera.get(
                    "ai_enabled",
                    True
                )
            ),

            cls.is_bool(
                camera.get(
                    "recording_enabled",
                    True
                )
            )
        )

    # ========================================================
    # ЗАВАНТАЖЕННЯ КАМЕР З LARAVEL
    # ========================================================

    def load_cameras_from_api(self):

        # Робочі налаштування Recorder з панелі (кеш 60 сек).
        # Не блокує камери: при недоступності Laravel —
        # дефолти, як захардкоджено в recorder.py.
        try:

            runtime_config.refresh()

        except Exception:

            pass

        print(
            f"Отримання камер з Laravel: "
            f"{API_URL}"
        )

        try:

            response = requests.get(
                API_URL,
                headers={
                    "Accept": "application/json"
                },
                timeout=REQUEST_TIMEOUT
            )

            response.raise_for_status()

            data = response.json()

            # ------------------------------------------------
            # Laravel може повернути:
            #
            # [
            #     {...},
            #     {...}
            # ]
            #
            # або:
            #
            # {
            #     "data": [...]
            # }
            #
            # або:
            #
            # {
            #     "cameras": [...]
            # }
            # ------------------------------------------------

            if isinstance(data, dict):

                if "data" in data:
                    data = data["data"]

                elif "cameras" in data:
                    data = data["cameras"]

            if not isinstance(data, list):

                print(
                    "Laravel API повернув "
                    "неправильний формат"
                )

                return False

            new_cameras = {}

            # =================================================
            # ОБРОБКА КАМЕР
            # =================================================

            for camera in data:

                if not isinstance(
                    camera,
                    dict
                ):
                    continue

                camera_id = camera.get("id")

                if camera_id is None:
                    continue

                try:

                    camera_id = int(
                        camera_id
                    )

                except (
                    TypeError,
                    ValueError
                ):

                    continue

                normalized = dict(
                    camera
                )

                normalized["id"] = camera_id

                normalized["source"] = (
                    self.normalize_source(
                        camera.get("source")
                    )
                )

                normalized[
                    "confidence_threshold"
                ] = self.normalize_float(
                    camera.get(
                        "confidence_threshold",
                        0.5
                    ),
                    0.5
                )

                normalized["enabled"] = (
                    self.is_bool(
                        camera.get(
                            "enabled",
                            True
                        )
                    )
                )

                normalized["ai_enabled"] = (
                    self.is_bool(
                        camera.get(
                            "ai_enabled",
                            True
                        )
                    )
                )

                normalized[
                    "recording_enabled"
                ] = self.is_bool(
                    camera.get(
                        "recording_enabled",
                        True
                    )
                )

                normalized["status"] = str(
                    camera.get(
                        "status",
                        "offline"
                    )
                ).lower()

                new_cameras[
                    camera_id
                ] = normalized

            # =================================================
            # ЗБЕРІГАЄМО
            # =================================================

            with self.lock:

                self.cameras = new_cameras

            print(
                f"Отримано камер: "
                f"{len(new_cameras)}"
            )

            # =================================================
            # ВИВЕДЕННЯ СПИСКУ
            # =================================================

            for (
                camera_id,
                camera
            ) in new_cameras.items():

                camera_name = camera.get(
                    "name",
                    f"Camera {camera_id}"
                )

                print(
                    f"  [{camera_id}] "
                    f"{camera_name} "
                    f"| source={camera.get('source')} "
                    f"| enabled={camera.get('enabled')} "
                    f"| AI={camera.get('ai_enabled')} "
                    f"| REC={camera.get('recording_enabled')} "
                    f"| CONF={camera.get('confidence_threshold')} "
                    f"| DB_STATUS={camera.get('status')}"
                )

            return True

        except requests.RequestException as e:

            print(
                f"Помилка підключення "
                f"до Laravel: {e}"
            )

            return False

        except Exception as e:

            print(
                f"Помилка завантаження "
                f"камер: {e}"
            )

            return False

    # ========================================================
    # ВІДПРАВКА STATUS В LARAVEL
    #
    # Статус відправляється тільки якщо він змінився.
    # ========================================================

    def update_camera_status(
        self,
        camera_id,
        status,
        force=False
    ):

        status = str(
            status
        ).lower()

        if status not in (
            "online",
            "offline",
            "error"
        ):
            status = "offline"

        # ----------------------------------------------------
        # Попередній відправлений статус
        # ----------------------------------------------------

        with self.lock:

            previous_status = (
                self.last_sent_status.get(
                    camera_id
                )
            )

        # ----------------------------------------------------
        # Якщо статус не змінився —
        # HTTP-запит не виконуємо.
        # ----------------------------------------------------

        if (
            not force
            and
            previous_status == status
        ):
            return True

        url = (
            f"{API_URL}/"
            f"{camera_id}/status"
        )

        payload = {
            "status": status
        }

        try:

            response = requests.post(
                url,
                json=payload,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                },
                timeout=REQUEST_TIMEOUT
            )

            if (
                response.status_code >= 200
                and
                response.status_code < 300
            ):

                with self.lock:

                    self.last_sent_status[
                        camera_id
                    ] = status

                old_text = (
                    previous_status
                    if previous_status
                    else "UNKNOWN"
                )

                print(
                    f"[STATUS] Camera "
                    f"{camera_id}: "
                    f"{old_text.upper()} → "
                    f"{status.upper()} → Laravel"
                )

                return True

            print(
                f"[STATUS] Camera "
                f"{camera_id}: "
                f"Laravel HTTP "
                f"{response.status_code}"
            )

        except requests.RequestException as e:

            print(
                f"[STATUS] Camera "
                f"{camera_id}: "
                f"помилка Laravel: {e}"
            )

        except Exception as e:

            print(
                f"[STATUS] Camera "
                f"{camera_id}: {e}"
            )

        return False

    # ========================================================
    # СИНХРОНІЗАЦІЯ STATUS WORKER → LARAVEL
    # ========================================================

    def sync_worker_status(
        self,
        camera_id,
        worker
    ):

        if worker is None:
            return

        try:

            status = worker.get_status()

        except Exception:

            status = "offline"

        status = str(
            status
        ).lower()

        if status == "online":

            self.update_camera_status(
                camera_id,
                "online"
            )

        elif status == "error":

            self.update_camera_status(
                camera_id,
                "error"
            )

        else:

            self.update_camera_status(
                camera_id,
                "offline"
            )

    # ========================================================
    # ЗАПУСК ВСІХ КАМЕР
    # ========================================================

    def start_all(self):

        print()

        print(
            "=" * 60
        )

        print(
            "ЗАПУСК КАМЕР"
        )

        print(
            "=" * 60
        )

        # ----------------------------------------------------
        # Отримуємо камери з Laravel
        # ----------------------------------------------------

        if not self.load_cameras_from_api():

            print(
                "Не вдалося отримати "
                "камери з Laravel"
            )

            return False

        started = 0

        with self.lock:

            cameras = dict(
                self.cameras
            )

        # =====================================================
        # ЗАПУСК КАМЕР
        # =====================================================

        for (
            camera_id,
            camera
        ) in cameras.items():

            if not camera.get(
                "enabled",
                True
            ):

                print(
                    f"Камера {camera_id} "
                    "вимкнена"
                )

                self.update_camera_status(
                    camera_id,
                    "offline"
                )

                continue

            if self.start_camera(
                camera_id
            ):

                started += 1

        # ----------------------------------------------------
        # Менеджер продовжує працювати навіть якщо
        # якась камера тимчасово недоступна.
        # ----------------------------------------------------

        self.running = True

        print()

        print(
            f"Запущено камер: "
            f"{started}"
        )

        print(
            "=" * 60
        )

        return True

    # ========================================================
    # ЗАПУСК ОДНІЄЇ КАМЕРИ
    # ========================================================

    def start_camera(
        self,
        camera_id
    ):

        with self.camera_operations_lock:

            with self.lock:

                camera = self.cameras.get(
                    camera_id
                )

            if camera is None:

                print(
                    f"Камера {camera_id} "
                    "не знайдена"
                )

                return False

            if not camera.get(
                "enabled",
                True
            ):

                print(
                    f"Камера {camera_id} "
                    "вимкнена"
                )

                return False

            # ------------------------------------------------
            # Якщо Worker вже працює
            # ------------------------------------------------

            existing = self.workers.get(
                camera_id
            )

            if (
                existing is not None
                and
                existing.is_alive()
            ):

                return True

            # ------------------------------------------------
            # Створення Worker
            # ------------------------------------------------

            try:

                worker = CameraWorker(
                    camera
                )

                with self.lock:

                    self.workers[
                        camera_id
                    ] = worker

                worker.start()

                camera_name = camera.get(
                    "name",
                    f"Camera {camera_id}"
                )

                print(
                    f"Worker запущено: "
                    f"{camera_name}"
                )

                return True

            except Exception as e:

                print(
                    f"Помилка запуску "
                    f"камери {camera_id}: "
                    f"{e}"
                )

                with self.lock:

                    self.workers.pop(
                        camera_id,
                        None
                    )

                self.update_camera_status(
                    camera_id,
                    "error"
                )

                return False

    # ========================================================
    # ЗУПИНКА ОДНІЄЇ КАМЕРИ
    # ========================================================

    def stop_camera(
        self,
        camera_id,
        update_status=True
    ):

        with self.camera_operations_lock:

            with self.lock:

                worker = self.workers.get(
                    camera_id
                )

            if worker is None:

                if update_status:

                    self.update_camera_status(
                        camera_id,
                        "offline"
                    )

                return

            # ------------------------------------------------
            # Stop Worker
            # ------------------------------------------------

            try:

                worker.stop()

            except Exception as e:

                print(
                    f"Помилка зупинки "
                    f"камери {camera_id}: "
                    f"{e}"
                )

            # ------------------------------------------------
            # Join Worker
            # ------------------------------------------------

            try:

                if worker.is_alive():

                    worker.join(
                        timeout=6
                    )

            except Exception as e:

                print(
                    f"Помилка join "
                    f"камери {camera_id}: "
                    f"{e}"
                )

            # ------------------------------------------------
            # Видалення Worker
            # ------------------------------------------------

            with self.lock:

                self.workers.pop(
                    camera_id,
                    None
                )

            # ------------------------------------------------
            # Laravel
            # ------------------------------------------------

            if update_status:

                self.update_camera_status(
                    camera_id,
                    "offline"
                )

            with self.lock:

                camera = self.cameras.get(
                    camera_id,
                    {}
                )

            camera_name = camera.get(
                "name",
                ""
            )

            print(
                f"Камера {camera_id} "
                f"зупинена: "
                f"{camera_name}"
            )

    # ========================================================
    # ОТРИМАННЯ WORKER
    # ========================================================

    def get_worker(
        self,
        camera_id
    ):

        with self.lock:

            return self.workers.get(
                camera_id
            )

    # ========================================================
    # ОТРИМАННЯ FRAME
    # ========================================================

    def get_frame(
        self,
        camera_id
    ):

        worker = self.get_worker(
            camera_id
        )

        if worker is None:

            return None

        try:

            return worker.get_frame()

        except Exception as e:

            print(
                f"[CameraManager] "
                f"get_frame({camera_id}): "
                f"{e}"
            )

            return None

    # ========================================================
    # ОТРИМАННЯ OBJECTS
    # ========================================================

    def get_objects(
        self,
        camera_id
    ):

        worker = self.get_worker(
            camera_id
        )

        if worker is None:

            return []

        try:

            return worker.get_objects()

        except Exception as e:

            print(
                f"[CameraManager] "
                f"get_objects({camera_id}): "
                f"{e}"
            )

            return []

    # ========================================================
    # ОТРИМАННЯ STATUS
    # ========================================================

    def get_status(
        self,
        camera_id
    ):

        worker = self.get_worker(
            camera_id
        )

        if worker is None:

            return "offline"

        try:

            status = worker.get_status()

            if status is None:

                return "offline"

            return str(
                status
            ).lower()

        except Exception:

            return "offline"

    # ========================================================
    # ВСІ STATUS
    # ========================================================

    def get_status_all(self):

        result = {}

        with self.lock:

            camera_ids = list(
                self.cameras.keys()
            )

        for camera_id in camera_ids:

            result[
                camera_id
            ] = self.get_status(
                camera_id
            )

        return result

    # ========================================================
    # СИНХРОНІЗАЦІЯ КАМЕР З LARAVEL
    # ========================================================

    def sync_cameras(self):

        # ----------------------------------------------------
        # Завантаження актуального списку
        # ----------------------------------------------------

        if not self.load_cameras_from_api():

            return

        with self.lock:

            cameras = dict(
                self.cameras
            )

            workers = dict(
                self.workers
            )

        # =====================================================
        # ПЕРЕВІРКА КОЖНОЇ КАМЕРИ
        # =====================================================

        for (
            camera_id,
            camera
        ) in cameras.items():

            worker = workers.get(
                camera_id
            )

            enabled = camera.get(
                "enabled",
                True
            )

            # =================================================
            # ВИМКНЕНА КАМЕРА
            # =================================================

            if not enabled:

                if worker is not None:

                    print(
                        f"Камера {camera_id} "
                        "вимкнена в Laravel"
                    )

                    self.stop_camera(
                        camera_id
                    )

                else:

                    self.update_camera_status(
                        camera_id,
                        "offline"
                    )

                continue

            # =================================================
            # НОВА КАМЕРА
            # =================================================

            if worker is None:

                print(
                    f"[SYNC] Нова камера: "
                    f"{camera_id}"
                )

                self.start_camera(
                    camera_id
                )

                continue

            # =================================================
            # ОТРИМАННЯ СТАРОЇ КОНФІГУРАЦІЇ
            # =================================================

            old_camera = getattr(
                worker,
                "camera",
                None
            )

            if old_camera is None:

                continue

            old_fingerprint = (
                self.get_camera_fingerprint(
                    old_camera
                )
            )

            new_fingerprint = (
                self.get_camera_fingerprint(
                    camera
                )
            )

            # =================================================
            # КОНФІГУРАЦІЯ ЗМІНИЛАСЯ
            # =================================================

            if (
                old_fingerprint
                !=
                new_fingerprint
            ):

                print(
                    f"[SYNC] Зміна "
                    f"конфігурації "
                    f"камери {camera_id}"
                )

                self.stop_camera(
                    camera_id
                )

                time.sleep(
                    0.5
                )

                self.start_camera(
                    camera_id
                )

        # =====================================================
        # ВИДАЛЕНІ КАМЕРИ
        # =====================================================

        for camera_id in workers.keys():

            if camera_id not in cameras:

                print(
                    f"[SYNC] Камеру "
                    f"{camera_id} "
                    "видалено з Laravel"
                )

                self.stop_camera(
                    camera_id,
                    update_status=False
                )

                with self.lock:

                    self.last_sent_status.pop(
                        camera_id,
                        None
                    )

    # ========================================================
    # СИНХРОНІЗАЦІЯ STATUS
    # ========================================================

    def sync_statuses(self):

        with self.lock:

            workers = dict(
                self.workers
            )

        for (
            camera_id,
            worker
        ) in workers.items():

            if worker is None:

                continue

            # ------------------------------------------------
            # Worker завершив роботу
            # ------------------------------------------------

            if not worker.is_alive():

                print(
                    f"[STATUS] Worker "
                    f"камери {camera_id} "
                    "не працює"
                )

                self.update_camera_status(
                    camera_id,
                    "offline"
                )

                continue

            # ------------------------------------------------
            # STATUS
            # ------------------------------------------------

            try:

                status = worker.get_status()

            except Exception:

                status = "offline"

            status = str(
                status
            ).lower()

            # ------------------------------------------------
            # Відправляємо тільки при зміні
            # ------------------------------------------------

            if status == "online":

                self.update_camera_status(
                    camera_id,
                    "online"
                )

            elif status == "error":

                self.update_camera_status(
                    camera_id,
                    "error"
                )

            else:

                self.update_camera_status(
                    camera_id,
                    "offline"
                )

    # ========================================================
    # MONITOR
    # ========================================================

    def monitor(self):

        self.running = True

        print()

        print(
            "Моніторинг камер запущено"
        )

        try:

            while self.running:

                current_time = time.time()

                # ============================================
                # СИНХРОНІЗАЦІЯ КАМЕР
                # ============================================

                if (
                    current_time
                    -
                    self.last_api_check
                    >=
                    API_CHECK_INTERVAL
                ):

                    self.last_api_check = (
                        current_time
                    )

                    try:

                        self.sync_cameras()

                    except Exception as e:

                        print(
                            f"[MONITOR] "
                            f"Помилка "
                            f"sync_cameras(): "
                            f"{e}"
                        )

                # ============================================
                # STATUS
                # ============================================

                if (
                    current_time
                    -
                    self.last_status_check
                    >=
                    STATUS_CHECK_INTERVAL
                ):

                    self.last_status_check = (
                        current_time
                    )

                    try:

                        self.sync_statuses()

                    except Exception as e:

                        print(
                            f"[MONITOR] "
                            f"Помилка "
                            f"sync_statuses(): "
                            f"{e}"
                        )

                time.sleep(
                    1
                )

        except Exception as e:

            print(
                f"[MONITOR] "
                f"Критична помилка: "
                f"{e}"
            )

        finally:

            print(
                "Моніторинг камер "
                "завершено"
            )

    # ========================================================
    # STOP ALL
    # ========================================================

    def stop_all(self):

        print()

        print(
            "Зупинка всіх камер..."
        )

        self.running = False

        with self.lock:

            camera_ids = list(
                self.workers.keys()
            )

        # ----------------------------------------------------
        # Зупинка Worker
        # ----------------------------------------------------

        for camera_id in camera_ids:

            self.stop_camera(
                camera_id
            )

        # ----------------------------------------------------
        # Очищення кешу
        # ----------------------------------------------------

        with self.lock:

            self.last_sent_status.clear()

        print(
            "Всі камери зупинено"
        )

