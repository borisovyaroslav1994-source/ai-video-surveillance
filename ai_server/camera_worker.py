import queue
import threading
import time
import cv2

from app.detector import Detector
from app.recorder import Recorder


RECONNECT_DELAY = 3
FRAME_RETRY_DELAY = 0.01

# Черга для потоку запису: маленька, зі скиданням старого.
# Запис завжди бере СВІЖИЙ кадр — це тримає 1:1 з реальним
# часом без дублів і без перемотки.
RECORD_QUEUE_SIZE = 2


class CameraWorker(threading.Thread):

    def __init__(self, camera):

        super().__init__(
            name=f"CameraWorker-{camera.get('id', 'unknown')}",
            daemon=True
        )

        # ==========================================
        # КОНФІГУРАЦІЯ КАМЕРИ
        # ==========================================

        self.camera = camera

        self.camera_id = camera.get("id")

        self.camera_name = camera.get(
            "name",
            f"Camera {self.camera_id}"
        )

        self.camera_type = str(
            camera.get("type", "usb")
        ).lower()

        self.source = self.normalize_source(
            camera.get("source")
        )

        self.confidence = self.normalize_float(
            camera.get(
                "confidence_threshold",
                0.5
            ),
            0.5
        )

        self.ai_enabled = self.is_bool(
            camera.get(
                "ai_enabled",
                True
            )
        )

        self.recording_enabled = self.is_bool(
            camera.get(
                "recording_enabled",
                True
            )
        )

        # ==========================================
        # СТАН
        # ==========================================

        self.running = False

        self.capture = None

        self.detector = None

        self.recorder = None

        self.frame = None

        self.objects = []

        # ==========================================
        # ТРИ ПОТОКИ: захват / запис / детекція
        # ==========================================
        # Головний run() — тільки capture.read() + розкладка
        # копій кадрів. Запис і YOLO живуть в окремих потоках
        # і більше не гальмують один одного.

        # Черга для запису (свіжі кадри, drop-oldest).
        self.record_queue = queue.Queue(maxsize=RECORD_QUEUE_SIZE)

        # Слот для детекції: тільки ОСТАННІЙ кадр.
        # YOLO не потрібен кожен кадр — йому потрібен свіжий.
        self.detect_frame = None

        self.detect_lock = threading.Lock()

        self.recorder_lock = threading.RLock()

        self.record_thread = None

        self.detect_thread = None

        self.record_fps_real = 0.0

        self._record_frames = 0

        self._record_fps_ts = 0.0

        # ==========================================
        # LOCK
        # ==========================================

        self.frame_lock = threading.RLock()

        self.object_lock = threading.RLock()

        self.status_lock = threading.RLock()

        # ==========================================
        # STATUS
        # ==========================================

        self.status = "offline"

        self.last_error = None

        # ==========================================
        # ПАРАМЕТРИ ВІДЕО
        # ==========================================

        self.fps = 25.0

        self.width = 0

        self.height = 0

        self.last_frame_time = 0

        self.reconnect_count = 0

        print(
            f"[{self.camera_name}] "
            "CameraWorker створено"
        )


    # =========================================================
    # HELPERS
    # =========================================================

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


    @staticmethod
    def normalize_float(
            value,
            default=0.5
    ):

        try:
            return float(value)

        except (
            TypeError,
            ValueError
        ):

            return default


    @staticmethod
    def normalize_source(source):

        if source is None:
            return ""

        source = str(source).strip()

        if source.isdigit():
            return int(source)

        return source


    # =========================================================
    # STATUS
    # =========================================================

    def set_status(self, status):

        status = str(status).lower()

        if status not in (
            "online",
            "offline",
            "error",
            "connecting"
        ):

            status = "offline"

        with self.status_lock:

            old_status = self.status

            self.status = status

        if old_status != status:

            print(
                f"[{self.camera_name}] "
                f"STATUS: "
                f"{old_status.upper()} → "
                f"{status.upper()}"
            )


    def get_status(self):

        with self.status_lock:

            return self.status


    # =========================================================
    # ПІДКЛЮЧЕННЯ КАМЕРИ
    # =========================================================

    def connect(self):

        self.set_status("connecting")

        try:

            print(
                f"[{self.camera_name}] "
                f"Підключення камери: "
                f"{self.source}"
            )

            self.release_capture()

            # ==========================================
            # USB
            # ==========================================

            if self.camera_type == "usb":

                self.capture = cv2.VideoCapture(
                    self.source,
                    cv2.CAP_DSHOW
                )

                if not self.capture.isOpened():

                    self.capture.release()

                    self.capture = cv2.VideoCapture(
                        self.source
                    )

            # ==========================================
            # RTSP / HTTP / HLS
            # ==========================================

            else:

                self.capture = cv2.VideoCapture(
                    self.source
                )

            # ==========================================
            # ПЕРЕВІРКА
            # ==========================================

            if (
                self.capture is None
                or
                not self.capture.isOpened()
            ):

                self.release_capture()

                self.set_status("offline")

                print(
                    f"[{self.camera_name}] "
                    f"Не вдалося відкрити джерело: "
                    f"{self.source}"
                )

                return False

            # ==========================================
            # BUFFER
            # ==========================================

            try:

                self.capture.set(
                    cv2.CAP_PROP_BUFFERSIZE,
                    1
                )

            except Exception:
                pass

            # ==========================================
            # FPS
            # ==========================================

            try:

                fps = self.capture.get(
                    cv2.CAP_PROP_FPS
                )

                if fps and fps > 0:

                    self.fps = float(fps)

                else:

                    self.fps = 25.0

            except Exception:

                self.fps = 25.0

            # ==========================================
            # РОЗДІЛЬНА ЗДАТНІСТЬ
            # ==========================================

            try:

                self.width = int(
                    self.capture.get(
                        cv2.CAP_PROP_FRAME_WIDTH
                    )
                )

                self.height = int(
                    self.capture.get(
                        cv2.CAP_PROP_FRAME_HEIGHT
                    )
                )

            except Exception:

                self.width = 0

                self.height = 0

            # ==========================================
            # YOLO
            # ==========================================

            if self.ai_enabled:

                if self.detector is None:

                    try:

                        self.detector = Detector(
                            camera_id=self.camera_id
                        )

                    except Exception as e:

                        self.last_error = str(e)

                        print(
                            f"[{self.camera_name}] "
                            f"Помилка YOLO: {e}"
                        )

                        self.detector = None

                        self.set_status("error")

                        self.release_capture()

                        return False

            # ==========================================
            # RECORDER
            # ==========================================

            if self.recording_enabled:

                try:

                    self.start_recorder()

                except Exception as e:

                    print(
                        f"[{self.camera_name}] "
                        f"Помилка Recorder: {e}"
                    )

                    self.recorder = None

            # ==========================================
            # ONLINE
            # ==========================================

            self.reconnect_count = 0

            self.set_status("online")

            print(
                f"[{self.camera_name}] "
                f"ONLINE "
                f"{self.width}x{self.height} "
                f"{self.fps:.1f} FPS"
            )

            return True

        except Exception as e:

            self.last_error = str(e)

            print(
                f"[{self.camera_name}] "
                f"Помилка підключення: {e}"
            )

            self.release_capture()

            self.set_status("offline")

            return False


    # =========================================================
    # RECORDER
    # =========================================================

    def start_recorder(self):

        if not self.recording_enabled:

            return

        with self.recorder_lock:

            if self.recorder is not None:

                # Recorder живий, але потоки могли впасти
                # (напр. після помилки) — перезапускаємо.
                pass

            else:

                # Якщо OpenCV не визначив параметри,
                # НЕ підставляємо 1920x1080 "наосліп":
                # реальний розмір візьмемо з першого кадру в Recorder.
                # Інакше VideoWriter створюється з хибним розміром
                # і записи "некоректні" (чорні/обрізані/не грають).

                width = self.width

                height = self.height

                fps = self.fps

                if width <= 0:

                    width = 0

                if height <= 0:

                    height = 0

                if fps <= 0:

                    fps = 25.0

                self.recorder = Recorder(
                    camera_id=self.camera_id,
                    width=width,
                    height=height,
                    fps=fps,
                    camera_name=self.camera_name
                )

                self._clear_record_queue()

                print(
                    f"[{self.camera_name}] "
                    f"Recorder готовий: "
                    f"{width}x{height} "
                    f"{fps:.1f} FPS"
                )

        self._start_record_thread()

        self._start_detect_thread()


    # =========================================================
    # ЧЕРГА ЗАПИСУ (drop-oldest, завжди свіже)
    # =========================================================

    def _clear_record_queue(self):

        try:

            while True:

                self.record_queue.get_nowait()

        except queue.Empty:

            pass

        except Exception:

            pass


    def _push_record_frame(self, frame):

        if not self.recording_enabled:

            return

        if frame is None:

            return

        try:

            self.record_queue.put_nowait(frame)

        except queue.Full:

            # Черга повна (запис повільніший за захват) —
            # викидаємо НАЙСТАРІШИЙ, кладемо свіжий.
            try:

                self.record_queue.get_nowait()

            except Exception:

                pass

            try:

                self.record_queue.put_nowait(frame)

            except Exception:

                pass

        except Exception:

            pass


    # =========================================================
    # ЗАПИС КАДРУ (викликається ТІЛЬКИ з _record_loop)
    # =========================================================

    def write_recording(self, frame):

        if not self.recording_enabled:

            return

        if frame is None:

            return

        with self.recorder_lock:

            recorder = self.recorder

            if recorder is None:

                return

            try:

                recorder.write(frame)

                self._record_frames += 1

                now = time.time()

                if self._record_fps_ts <= 0:

                    self._record_fps_ts = now

                    self._record_frames = 0

                elif now - self._record_fps_ts >= 5.0:

                    elapsed = now - self._record_fps_ts

                    if elapsed > 0:

                        self.record_fps_real = (
                            self._record_frames / elapsed
                        )

                    self._record_frames = 0

                    self._record_fps_ts = now

            except Exception as e:

                print(
                    f"[{self.camera_name}] "
                    f"Помилка запису: {e}"
                )


    # =========================================================
    # ПОТІК ЗАПИСУ
    # =========================================================

    def _start_record_thread(self):

        if not self.recording_enabled:

            return

        try:

            thread = self.record_thread

            if thread is not None and thread.is_alive():

                return

        except Exception:

            pass

        thread = threading.Thread(
            target=self._record_loop,
            name=f"Record-{self.camera_id}",
            daemon=True
        )

        self.record_thread = thread

        thread.start()

        print(
            f"[{self.camera_name}] "
            "Потік запису запущено"
        )


    def _record_loop(self):

        # Окремий потік: бере свіжі кадри з черги і пише.
        # Не чекає YOLO — рівний fps файлу, без фризів
        # і без перемотки.

        while self.running:

            if not self.recording_enabled:

                time.sleep(0.2)

                continue

            try:

                frame = self.record_queue.get(timeout=0.5)

            except queue.Empty:

                continue

            except Exception:

                continue

            try:

                self.write_recording(frame)

            except Exception as e:

                print(
                    f"[{self.camera_name}] "
                    f"Помилка потоку запису: {e}"
                )


    # =========================================================
    # ЗУПИНКА RECORDER
    # =========================================================

    def stop_recorder(self):

        with self.recorder_lock:

            recorder = self.recorder

            self.recorder = None

        self._clear_record_queue()

        if recorder is None:

            return

        try:

            recorder.release()

            print(
                f"[{self.camera_name}] "
                "Recorder зупинено"
            )

        except Exception as e:

            print(
                f"[{self.camera_name}] "
                f"Помилка зупинки Recorder: {e}"
            )


    # =========================================================
    # ОТРИМАННЯ КАДРУ
    # =========================================================

    def read_frame(self):

        if (
            self.capture is None
            or
            not self.capture.isOpened()
        ):

            return None

        try:

            success, frame = self.capture.read()

            if not success:

                return None

            if frame is None:

                return None

            self.last_frame_time = time.time()

            return frame

        except Exception as e:

            self.last_error = str(e)

            return None


    # =========================================================
    # YOLO
    # =========================================================

    def detect_objects(self, frame):

        if not self.ai_enabled:

            return []

        if self.detector is None:

            return []

        if frame is None:

            return []

        try:

            objects = self.detector.detect(
                frame,
                confidence=self.confidence
            )

            if isinstance(objects, list):

                return objects

            return []

        except Exception as e:

            print(
                f"[{self.camera_name}] "
                f"YOLO error: {e}"
            )

            return []


    # =========================================================
    # ПОТІК ДЕТЕКЦІЇ
    # =========================================================

    def _start_detect_thread(self):

        if not self.ai_enabled:

            return

        try:

            thread = self.detect_thread

            if thread is not None and thread.is_alive():

                return

        except Exception:

            pass

        thread = threading.Thread(
            target=self._detect_loop,
            name=f"Detect-{self.camera_id}",
            daemon=True
        )

        self.detect_thread = thread

        thread.start()

        print(
            f"[{self.camera_name}] "
            "Потік детекції запущено"
        )


    def _detect_loop(self):

        # Окремий потік: бере ОСТАННІЙ кадр і детектить.
        # Поки YOLO зайнятий, нові кадри перезаписують слот —
        # захват і запис не чекають.

        while self.running:

            if not self.ai_enabled or self.detector is None:

                time.sleep(0.2)

                continue

            frame = None

            try:

                with self.detect_lock:

                    if self.detect_frame is not None:

                        frame = self.detect_frame.copy()

                        # Слот очищаємо: кожен кадр детектиться
                        # максимум 1 раз. Диспетчер покладе свіжий.
                        self.detect_frame = None

            except Exception:

                frame = None

            if frame is None:

                time.sleep(0.05)

                continue

            try:

                detect_frame = frame

                try:

                    det_h, det_w = frame.shape[:2]

                    if det_w > 640:

                        scale = 640.0 / float(det_w)

                        detect_frame = cv2.resize(
                            frame,
                            (
                                640,
                                max(2, int(det_h * scale)),
                            ),
                        )

                except Exception:

                    detect_frame = frame

                fresh_objects = self.detect_objects(
                    detect_frame
                )

                try:

                    if (
                        detect_frame is not frame
                        and isinstance(fresh_objects, list)
                        and fresh_objects
                    ):

                        full_h, full_w = frame.shape[:2]

                        small_h, small_w = detect_frame.shape[:2]

                        kx = float(full_w) / float(max(1, small_w))

                        ky = float(full_h) / float(max(1, small_h))

                        for obj in fresh_objects:

                            if not isinstance(obj, dict):

                                continue

                            bbox = obj.get("bbox")

                            if not isinstance(bbox, dict):

                                continue

                            for key, k in (
                                ("x1", kx),
                                ("x2", kx),
                                ("y1", ky),
                                ("y2", ky),
                            ):

                                try:

                                    bbox[key] = int(
                                        float(bbox.get(key, 0)) * k
                                    )

                                except (TypeError, ValueError):

                                    pass

                except Exception:

                    pass

                if isinstance(fresh_objects, list):

                    with self.object_lock:

                        self.objects = [
                            dict(obj)
                            for obj in fresh_objects
                            if isinstance(obj, dict)
                        ]

            except Exception as e:

                print(
                    f"[{self.camera_name}] "
                    f"Помилка потоку детекції: {e}"
                )


    def _push_detect_frame(self, frame):

        if not self.ai_enabled:

            return

        if frame is None:

            return

        try:

            with self.detect_lock:

                self.detect_frame = frame

        except Exception:

            pass


    # =========================================================
    # FRAME
    # =========================================================

    def get_frame(self):

        with self.frame_lock:

            if self.frame is None:

                return None

            return self.frame.copy()


    # =========================================================
    # OBJECTS
    # =========================================================

    def get_objects(self):

        with self.object_lock:

            return [
                dict(obj)
                for obj in self.objects
                if isinstance(obj, dict)
            ]


    # =========================================================
    # RELEASE CAMERA
    # =========================================================

    def release_capture(self):

        if self.capture is None:

            return

        try:

            self.capture.release()

        except Exception:
            pass

        self.capture = None


    # =========================================================
    # RECONNECT
    # =========================================================

    def reconnect(self):

        self.reconnect_count += 1

        print(
            f"[{self.camera_name}] "
            f"Перепідключення №"
            f"{self.reconnect_count}"
        )

        self.set_status("offline")

        self.release_capture()

        self.stop_recorder()

        self._clear_record_queue()

        try:

            with self.detect_lock:

                self.detect_frame = None

        except Exception:

            pass

        # Старі під-потоки вже вийшли (running ще True —
        # вони крутяться на timeout'ах черги). Перестворюємо
        # їх на свіжий Recorder після connect().
        for attr in ("record_thread", "detect_thread"):

            try:

                thread = getattr(self, attr, None)

                if thread is not None and not thread.is_alive():

                    setattr(self, attr, None)

            except Exception:

                pass

        with self.frame_lock:

            self.frame = None

        with self.object_lock:

            self.objects = []

        if not self.running:

            return False

        time.sleep(
            RECONNECT_DELAY
        )

        if not self.running:

            return False

        return self.connect()


    # =========================================================
    # MAIN WORKER LOOP
    # =========================================================

    def run(self):

        self.running = True

        print(
            f"[{self.camera_name}] "
            "Worker запущено"
        )

        try:

            while self.running:

                # ======================================
                # ПІДКЛЮЧЕННЯ
                # ======================================

                if (
                    self.capture is None
                    or
                    not self.capture.isOpened()
                ):

                    if not self.connect():

                        if not self.running:

                            break

                        time.sleep(
                            RECONNECT_DELAY
                        )

                        continue

                # ======================================
                # КАДР
                # ======================================

                frame = self.read_frame()

                if frame is None:

                    print(
                        f"[{self.camera_name}] "
                        "Не отримано кадр"
                    )

                    self.set_status("offline")

                    if not self.reconnect():

                        if not self.running:

                            break

                    continue

                # ======================================
                # ONLINE
                # ======================================

                if self.get_status() != "online":

                    self.set_status("online")

                # ======================================
                # ДИСПЕТЧЕР: тільки розкладаємо копії.
                # Запис і YOLO — в окремих потоках, тут
                # нічого важкого: жодного wait.
                # ======================================

                with self.frame_lock:

                    self.frame = frame.copy()

                # Копія для запису (потік запису забере).
                try:

                    self._push_record_frame(frame.copy())

                except Exception:

                    pass

                # Копія для детекції (потік YOLO забере
                # коли звільниться; старий слот перезаписуємо).
                try:

                    self._push_detect_frame(frame.copy())

                except Exception:

                    pass

                try:

                    del frame

                except Exception:

                    pass

                # ======================================
                # НЕ НАВАНТАЖУЄМО CPU
                # ======================================

                time.sleep(
                    FRAME_RETRY_DELAY
                )

        except Exception as e:

            self.last_error = str(e)

            print(
                f"[{self.camera_name}] "
                f"Критична помилка Worker: {e}"
            )

            self.set_status("error")

        finally:

            self.cleanup()

            print(
                f"[{self.camera_name}] "
                "Worker завершено"
            )


    # =========================================================
    # STOP
    # =========================================================

    def stop(self):

        print(
            f"[{self.camera_name}] "
            "Зупинка Worker"
        )

        self.running = False

        self.set_status("offline")

        # Даємо під-потокам (запис/детекція) вийти з циклів.
        for attr in ("record_thread", "detect_thread"):

            try:

                thread = getattr(self, attr, None)

                if thread is not None and thread.is_alive():

                    thread.join(timeout=3.0)

            except Exception:

                pass

        try:

            setattr(self, "record_thread", None)

            setattr(self, "detect_thread", None)

        except Exception:

            pass


    # =========================================================
    # CLEANUP
    # =========================================================

    def cleanup(self):

        self.running = False

        # Чекаємо під-потоки ПЕРЕД release Recorder —
        # інакше потік запису влучить у закритий файл.
        for attr in ("record_thread", "detect_thread"):

            try:

                thread = getattr(self, attr, None)

                if thread is not None and thread.is_alive():

                    thread.join(timeout=3.0)

            except Exception:

                pass

        try:

            self.record_thread = None

            self.detect_thread = None

        except Exception:

            pass

        # ==========================================
        # RECORDER
        # ==========================================

        self.stop_recorder()

        self._clear_record_queue()

        try:

            with self.detect_lock:

                self.detect_frame = None

        except Exception:

            pass

        # ==========================================
        # CAMERA
        # ==========================================

        self.release_capture()

        # ==========================================
        # FRAME
        # ==========================================

        with self.frame_lock:

            self.frame = None

        # ==========================================
        # OBJECTS
        # ==========================================

        with self.object_lock:

            self.objects = []

        # ==========================================
        # YOLO
        # ==========================================

        if self.detector is not None:

            try:

                if hasattr(
                    self.detector,
                    "close"
                ):

                    self.detector.close()

            except Exception as e:

                print(
                    f"[{self.camera_name}] "
                    f"Помилка закриття Detector: {e}"
                )

            finally:

                self.detector = None

        self.set_status("offline")

        print(
            f"[{self.camera_name}] "
            "Worker зупинено"
            )

