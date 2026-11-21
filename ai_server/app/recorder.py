import cv2
import os
import datetime
import time
import shutil
import subprocess
import requests

from app import runtime_config


# ============================================================
# НАЛАШТУВАННЯ (дефолти; робочі значення тягнуться з Laravel
# через runtime_config: GET /api/recorder-settings)
# ============================================================

API_URL = "http://diplom.local/api/videos"

REQUEST_TIMEOUT = 5

# Максимальна тривалість одного файлу (fallback, якщо
# Laravel недоступний; робоче значення — segment_seconds).
RECORDING_SEGMENT_SECONDS = 300


def _segment_seconds():
    """Робоча довжина сегмента з панелі (30..3600 сек)."""
    try:
        return int(runtime_config.segment_seconds())
    except Exception:
        try:
            return int(RECORDING_SEGMENT_SECONDS)
        except (TypeError, ValueError):
            return 300

# --- ЕКОНОМІЯ МІСЦЯ ---
# Камера часто віддає 1920x1080 (~8 Мбіт/с, ~300 МБ/5 хв).
# Для спостереження достатньо 1280x720: даунскейл перед записом
# дає ~-60% розміру без помітної втрати деталізації.
# 0 = не зменшувати (писати як є).
RECORD_MAX_WIDTH = 1280
RECORD_MAX_HEIGHT = 720

# Фонове пережаття ffmpeg (після закриття сегмента):
# CRF 28 + preset veryfast ≈ -60..-70% до вже зменшеного файлу.
# Разом із даунскейлом: ~300 МБ -> ~40-60 МБ за 5 хв.
TRANSCODE_CRF = 28
TRANSCODE_PRESET = "veryfast"
# Якщо файл після пережаття раптом БІЛЬШИЙ за оригінал —
# залишаємо оригінал (не плодимо сміття).
TRANSCODE_KEEP_SMALLER = True

# Пріоритет кодеків: H.264 (avc1) відтворюється у браузерах,
# mp4v (MPEG-4 Part 2) — НІ, тому він лише як останній fallback.
CODEC_PRIORITY = ("avc1", "H264", "X264", "mp4v")


def _fit_record_size(width, height):
    """Вписує кадр у RECORD_MAX_* зі збереженням пропорцій.

    1080p (1920x1080 = 2.07 Мп) -> 720p (1280x720 = 0.92 Мп):
    у ~2.25 раза менше пікселів = ~-55% бітрейту/розміру
    при тій же якості. Повертає парні розміри (вимога H.264).
    0 у RECORD_MAX_* = не зменшувати.
    """
    try:
        width = int(width)
        height = int(height)
    except (TypeError, ValueError):
        return width, height

    # Робочі межі з панелі (record_max_*), fallback — константи.
    try:
        cfg_w, cfg_h = runtime_config.record_max_size()
        max_w = int(cfg_w or 0)
        max_h = int(cfg_h or 0)
    except Exception:
        try:
            max_w = int(RECORD_MAX_WIDTH or 0)
            max_h = int(RECORD_MAX_HEIGHT or 0)
        except (TypeError, ValueError):
            return _even(width, 2), _even(height, 2)

    if max_w <= 0 or max_h <= 0:
        return _even(width, 2), _even(height, 2)

    if width <= max_w and height <= max_h:
        return _even(width, 2), _even(height, 2)

    try:
        scale = min(
            float(max_w) / float(max(1, width)),
            float(max_h) / float(max(1, height)),
        )
    except (TypeError, ValueError, ZeroDivisionError):
        return _even(width, 2), _even(height, 2)

    if scale <= 0 or scale >= 1.0:
        return _even(width, 2), _even(height, 2)

    return (
        _even(int(round(width * scale)), 2),
        _even(int(round(height * scale)), 2),
    )


def _ffmpeg_available():
    """Чи встановлено ffmpeg для фонового перекодування в H.264."""
    try:
        return shutil.which("ffmpeg") is not None
    except Exception:
        return False


def _ffmpeg_path():
    """Повний шлях до ffmpeg (для логів діагностики)."""
    try:
        return shutil.which("ffmpeg")
    except Exception:
        return None


def _has_audio_stream(filepath):
    """Чи є в MP4 аудіодоріжка (ffprobe, без падінь).

    OpenCV VideoWriter пише відео БЕЗ аудіо — тоді в команді
    треба -an замість -c:a aac, інакше ffmpeg падає
    з ненульовим кодом і пережаття мовчки пропускається.
    """
    try:
        if not filepath or not os.path.exists(filepath):
            return False

        ffprobe = shutil.which("ffprobe")

        if ffprobe is None:
            # ffprobe немає — припускаємо що аудіо немає
            # (наші файли пише OpenCV, він аудіо не пише).
            return False

        result = subprocess.run(
            [
                ffprobe,
                "-v", "error",
                "-select_streams", "a:0",
                "-show_entries", "stream=codec_type",
                "-of", "csv=p=0",
                str(filepath),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
        )

        try:
            out = result.stdout.decode("utf-8", "ignore").strip().lower()
        except Exception:
            out = ""

        return "audio" in out

    except Exception:
        return False


def _even(value, minimum=2):
    """H.264 вимагає парних розмірів кадру."""
    try:
        value = int(value)
    except (TypeError, ValueError):
        value = minimum
    if value < minimum:
        value = minimum
    if value % 2 == 1:
        value -= 1
    return max(minimum, value)


class Recorder:

    def __init__(
        self,
        camera_id,
        width=0,
        height=0,
        fps=20,
        camera_name=None
    ):

        self.camera_id = camera_id

        self.camera_name = camera_name or f"Camera {camera_id}"

        # H.264 вимагає парних розмірів кадру.
        # width/height тут — лише стартове значення:
        # реальний розмір беремо з першого кадру в write().
        # Економія місця: одразу вписуємо у RECORD_MAX_*
        # (1080p -> 720p ≈ -55% розміру).
        try:
            fit_w, fit_h = _fit_record_size(width, height)
        except Exception:
            fit_w, fit_h = width, height

        self.width = _even(fit_w, 2)

        self.height = _even(fit_h, 2)

        # Номінальний fps камери (заголовок MP4).
        # ВАЖЛИВО: заголовок потоку (особливо IPTV/HLS) часто бреше
        # і віддає 0/1 fps, хоча цикл реально пише ~20 кадрів/с.
        # Без клампа сегмент 300 кадрів набирався за ~12-15 сек —
        # звідси «відео тільки по 12 секунд» замість 5 хвилин.
        try:
            self.fps = float(fps)
        except (TypeError, ValueError):
            self.fps = 20.0

        if not (5.0 <= self.fps <= 60.0):
            print(
                f"[Recorder][Camera {self.camera_id}] "
                f"Підозрілий fps камери ({fps}) — "
                f"використовуємо 20.0 для заголовку MP4"
            )
            self.fps = 20.0

        # Фактичний fps, яким відкрито поточний VideoWriter
        # (заголовок MP4).
        self.write_fps = float(self.fps)

        # Багатопотоковий режим: запис іде окремим потоком,
        # кадри приходять рівно (черга drop-oldest тримає свіже).
        # Пишемо 1:1 — кожен кадр з черги = 1 кадр у файл.
        # Жодних дублів і дропів: темп задає захват, заголовок
        # MP4 підганяємо під реальний fps (див. _maybe_fix_header).
        self._slot_interval = 1.0 / float(self.fps)
        self._next_slot = None

        # Замір реального fps потоку запису (ковзне середнє).
        self.measured_fps = float(self.fps)

        # Скільки кадрів побачили для калібрування заголовка.
        self._header_fix_done = False
        self._header_fix_frames = 0
        self._header_fix_ts = 0.0

        self._last_write_ts = None

        # Лічильник реально записаних кадрів поточного сегмента.
        # Тривалість сегмента = frames_written / effective_fps,
        # де effective_fps = measured_fps (замір), а не час стіни.
        self.frames_written = 0

        # Фіксована ціль кадрів для поточного сегмента.
        # Не перераховується кожен кадр, інакше при гальмуванні YOLO
        # target_frames падає нижче frames_written → негайна ротація.
        self.segment_target_frames = 0

        self.segment_opened_at = None

        self.segment_started_at_str = None

        # Черга файлів на фонове перекодування ffmpeg
        # (щоб не блокувати цикл камери на 30-60 сек).
        self.transcode_queue = []

        self.transcode_thread = None

        self.transcode_lock = None

        try:
            import threading

            self.transcode_lock = threading.Lock()
        except Exception:
            self.transcode_lock = None

        # ----------------------------------------------------
        # OpenCV Writer
        # ----------------------------------------------------

        self.writer = None

        # ----------------------------------------------------
        # Поточний файл
        # ----------------------------------------------------

        self.file = None

        self.start_time = None

        # ----------------------------------------------------
        # Laravel ID поточного відео
        # ----------------------------------------------------

        self.laravel_video_id = None

        print(
            f"[Recorder][Camera {self.camera_id}] "
            "Recorder створено"
        )

    # ========================================================
    # СТВОРЕННЯ ФАЙЛУ
    # ========================================================

    def create_file(self, first_frame=None):

        # ----------------------------------------------------
        # Якщо попередній файл ще відкритий —
        # спочатку закриваємо його.
        # ----------------------------------------------------

        if self.writer is not None:

            self.release()

        # ----------------------------------------------------
        # Розмір сегмента беремо з РЕАЛЬНОГО кадру, а не з того,
        # що OpenCV повідомив при відкритті камери (часто 0x0
        # або застаріле значення) — інакше MP4 пишеться
        # некоректним розміром і "не грає" / обрізаний.
        # ----------------------------------------------------

        if first_frame is not None:
            try:
                fh, fw = first_frame.shape[:2]

                fw = _even(int(fw), 2)
                fh = _even(int(fh), 2)

                # Економія місця: даунскейл до RECORD_MAX_*
                # (напр. 1920x1080 -> 1280x720 ≈ -55% розміру).
                try:
                    fw, fh = _fit_record_size(fw, fh)
                except Exception:
                    pass

                if fw >= 2 and fh >= 2:
                    if fw != self.width or fh != self.height:
                        print(
                            f"[Recorder][Camera "
                            f"{self.camera_id}] "
                            f"Розмір кадру: "
                            f"{self.width}x{self.height} -> "
                            f"{fw}x{fh}"
                        )

                    self.width = fw
                    self.height = fh
            except Exception:
                pass

        if self.width < 2 or self.height < 2:
            print(
                f"[Recorder][Camera {self.camera_id}] "
                f"Невідомий розмір кадру — "
                f"чекаємо перший кадр"
            )

            return False

        now = datetime.datetime.now()

        folder = os.path.join(
            "videos",
            f"camera_{self.camera_id}",
            now.strftime("%Y-%m-%d")
        )

        os.makedirs(
            folder,
            exist_ok=True
        )

        filename = os.path.join(
            folder,
            now.strftime("%H-%M-%S") + ".mp4"
        )

        # ----------------------------------------------------
        # Кодек: H.264 (avc1) — відтворюється у Chrome/Edge/Firefox.
        # mp4v — НЕ відтворюється у браузерах, тому лише fallback.
        # Також пробуємо перекодувати готові файли через ffmpeg.
        # ----------------------------------------------------

        self.codec_used = None

        writer = None

        for tag in CODEC_PRIORITY:
            try:
                codec = cv2.VideoWriter_fourcc(*tag)

                candidate = cv2.VideoWriter(
                    filename,
                    codec,
                    self.fps,
                    (
                        self.width,
                        self.height
                    )
                )

                if candidate.isOpened():
                    writer = candidate
                    self.codec_used = tag
                    break

                try:
                    candidate.release()
                except Exception:
                    pass
            except Exception:
                continue

        if writer is None:
            print(
                f"[Recorder][Camera {self.camera_id}] "
                f"Не вдалося відкрити VideoWriter: "
                f"{filename}"
            )

            return False

        print(
            f"[Recorder][Camera {self.camera_id}] "
            f"Кодек запису: {self.codec_used}"
        )

        self.writer = writer

        # Заголовок MP4 відкрито саме з self.fps —
        # запам'ятовуємо для коректного розрахунку duration.
        self.write_fps = float(self.fps)

        self._slot_interval = 1.0 / float(self.fps)
        self._next_slot = None

        self.file = filename

        # Фіксуємо старт сегмента за часом стіни.
        # Ротація йде ПЕРЕВАЖНО за wall-time (див. write()),
        # щоб fps камери не впливав на довжину файла.
        self.start_time = time.time()

        # Новий сегмент — лічильник кадрів з нуля.
        self.frames_written = 0

        self.segment_target_frames = 0  # скидаємо, обчислиться при першому кадрі

        # Новий сегмент — калібрування заголовка заново:
        # перші ~3 сек заміряємо реальний fps потоку запису.
        self._header_fix_done = False
        self._header_fix_frames = 0
        self._header_fix_ts = 0.0

        self._last_write_ts = None

        self.segment_opened_at = datetime.datetime.now()

        self.segment_started_at_str = self.segment_opened_at.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        self.laravel_video_id = None

        print(
            f"[Recorder][Camera {self.camera_id}] "
            f"Запис: {filename}"
        )

        # ----------------------------------------------------
        # Реєструємо відео в Laravel
        # ----------------------------------------------------

        self.register_video()

        return True

    # ========================================================
    # КАЛІБРУВАННЯ ЗАГОЛОВКА ПІД РЕАЛЬНИЙ FPS
    # ========================================================

    def _maybe_fix_header(self):

        # Перші 3 сек сегмента заміряли реальний fps потоку
        # запису. Якщо він сильно нижчий за заголовок MP4 —
        # плеєр гратиме файл у «перемотці»
        # (frames / header_fps < секунд стіни).
        # Перевідкриваємо VideoWriter з header = виміряний fps:
        # втрачаємо перші 3 сек (залишаються в старому файлі
        # як короткий вступ), далі сегмент іде 1:1.

        self._header_fix_done = True

        try:

            measured = float(getattr(self, "measured_fps", 0) or 0)

            header = float(getattr(self, "write_fps", 0) or 0)

        except (TypeError, ValueError):

            return

        if measured < 5.0 or header <= 0:

            return

        # Розбіжність менше 15% — заголовок вже чесний.
        try:

            diff = abs(header - measured) / max(1.0, header)

        except (TypeError, ValueError, ZeroDivisionError):

            return

        if diff < 0.15:

            return

        new_fps = max(5.0, min(60.0, round(measured)))

        print(
            f"[Recorder][Camera {self.camera_id}] "
            f"Реальний fps запису {measured:.1f} != "
            f"заголовку {header:.1f} — "
            f"перевідкриваю сегмент з {new_fps:.0f} fps"
        )

        # Закриваємо короткий вступний файл (3 сек)...
        try:

            old_file = self.file

            old_writer = self.writer

            self.writer = None

            self.file = None

            if old_writer is not None:

                try:

                    old_writer.release()

                except Exception:

                    pass

            # ...видаляємо його, щоб не плодити сміття...
            try:

                if old_file and os.path.exists(old_file):

                    if os.path.getsize(old_file) < 500 * 1024:

                        os.remove(old_file)

            except Exception:

                pass

        except Exception:

            pass

        # ...і відкриваємо сегмент заново з чесним fps.
        try:

            self.fps = float(new_fps)

        except (TypeError, ValueError):

            pass

        self._header_fix_frames = 0

        self._header_fix_ts = 0.0

        self.start_time = time.time()

        self.frames_written = 0

        self._last_write_ts = None

        try:

            self.create_file(first_frame=None)

        except Exception as e:

            print(
                f"[Recorder][Camera {self.camera_id}] "
                f"Не вдалося перевідкрити з {new_fps:.0f} fps: {e}"
            )

        # Після перевідкриття не калібруємо знову.
        self._header_fix_done = True

    # ========================================================
    # РЕЄСТРАЦІЯ ВІДЕО В LARAVEL
    # ========================================================

    def register_video(self):

        if not self.file:
            return False

        try:

            now = datetime.datetime.now()

            opened = getattr(self, "segment_opened_at", None) or now

            # ------------------------------------------------
            # Шлях відносно кореня Python-системи
            # ------------------------------------------------

            relative_path = self.file.replace(
                "\\",
                "/"
            )

            filename = os.path.basename(
                self.file
            )

            payload = {
                "camera_id": self.camera_id,

                "camera_name": self.camera_name,

                "filename": filename,

                "path": relative_path,

                "recording_date": (
                    opened.strftime("%Y-%m-%d")
                ),

                "started_at": (
                    getattr(
                        self,
                        "segment_started_at_str",
                        None
                    )
                    or opened.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                ),

                "status": "recording"
            }

            response = requests.post(
                API_URL,
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

                try:

                    data = response.json()

                    video = data.get(
                        "video"
                    )

                    if isinstance(
                        video,
                        dict
                    ):

                        self.laravel_video_id = (
                            video.get("id")
                        )

                except Exception:
                    pass

                print(
                    f"[Recorder][Camera "
                    f"{self.camera_id}] "
                    f"Відео зареєстровано "
                    f"в Laravel"
                )

                if self.laravel_video_id:

                    print(
                        f"[Recorder][Camera "
                        f"{self.camera_id}] "
                        f"Laravel Video ID: "
                        f"{self.laravel_video_id}"
                    )

                return True

            print(
                f"[Recorder][Camera "
                f"{self.camera_id}] "
                f"Laravel HTTP "
                f"{response.status_code}"
            )

        except requests.RequestException as e:

            print(
                f"[Recorder][Camera "
                f"{self.camera_id}] "
                f"Laravel недоступний: {e}"
            )

        except Exception as e:

            print(
                f"[Recorder][Camera "
                f"{self.camera_id}] "
                f"Помилка реєстрації: {e}"
            )

        return False

    # ========================================================
    # ОНОВЛЕННЯ РОЗМІРУ В LARAVEL (після фонвого стиснення)
    # ========================================================

    def _update_video_size(self, size):

        try:
            video_id = getattr(self, "laravel_video_id", None)

            if video_id is None:
                return False

            try:
                size = int(size)
            except (TypeError, ValueError):
                return False

            if size < 0:
                return False

            url = f"{API_URL}/{video_id}/finish"

            response = requests.post(
                url,
                json={"size": size},
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                },
                timeout=REQUEST_TIMEOUT
            )

            return (
                response.status_code >= 200
                and
                response.status_code < 300
            )

        except requests.RequestException:
            return False

        except Exception:
            return False

    # ========================================================
    # ЗАВЕРШЕННЯ ВІДЕО В LARAVEL
    # ========================================================

    def finish_video(self):

        if not self.file:

            return False

        # ----------------------------------------------------
        # Реальна тривалість сегмента = час стіни.
        # Запис іде БЕЗ дублів (див. write()): 1 виклик =
        # максимум 1 кадр, зайві дропаються. Тому формула
        # frames_written / write_fps давала б ЗАНИЖЕНУ тривалість
        # коли цикл іде повільніше за header_fps або дропає зайве.
        # Час стіни (start_time -> зараз) — чесна тривалість того,
        # що реально відбувалось перед камерою.
        # ----------------------------------------------------

        wall_duration = 0

        try:
            started = float(getattr(self, "start_time", 0) or 0)

            if started > 0:
                wall_duration = int(round(time.time() - started))
        except (TypeError, ValueError):
            wall_duration = 0

        wall_duration = max(0, wall_duration)

        real_duration = wall_duration

        # probe_duration() рахує frames/fps заголовку — після переходу
        # на запис без дублів файл може мати менше кадрів ніж
        # header_fps * wall_time (цикл повільніший). Тоді probe дасть
        # занижену тривалість. Довіряємо часу стіни, probe — лише
        # саніті-перевірка що файл взагалі читається.
        probed = self.probe_duration(self.file, fallback=real_duration)

        if probed <= 0:
            duration = real_duration
        else:
            # Якщо probe сильно розходиться зі стіною (>20%) —
            # файл недописаний/битий, беремо стіну як чесну.
            try:
                ref = max(1, int(real_duration))
                diff = abs(int(probed) - ref) / float(ref)
            except (TypeError, ValueError, ZeroDivisionError):
                diff = 0

            duration = real_duration if diff > 0.2 else int(probed)

        # ----------------------------------------------------
        # Перекодування в H.264 — У ФОНІ, щоб не блокувати
        # цикл камери. Інакше ротація сегмента "зависає"
        # на 30-60 сек і наступний файл втрачає кадри.
        # ----------------------------------------------------

        try:

            self.queue_transcode(self.file)

        except Exception as e:

            print(
                f"[Recorder][Camera "
                f"{self.camera_id}] "
                f"Помилка queue_transcode: {e}"
            )

        # ----------------------------------------------------
        # Розрахунок тривалості: duration ВЖЕ пораховано вище
        # як час стіни + перевірено probe_duration().
        # ----------------------------------------------------

        # ----------------------------------------------------
        # Розмір файлу
        # ----------------------------------------------------

        size = 0

        try:

            if os.path.exists(
                self.file
            ):

                size = os.path.getsize(
                    self.file
                )

        except OSError:

            size = 0

        # ----------------------------------------------------
        # Якщо Laravel ID невідомий —
        # немає чого завершувати.
        # ----------------------------------------------------

        if self.laravel_video_id is None:

            return False

        url = (
            f"{API_URL}/"
            f"{self.laravel_video_id}/finish"
        )

        now = datetime.datetime.now()

        # ended_at = started_at + РЕАЛЬНА тривалість MP4,
        # а не час стіни (бо цикл гальмує YOLO).
        try:
            started_str = getattr(
                self, "segment_started_at_str", None
            )

            if started_str:
                started_dt = datetime.datetime.strptime(
                    started_str, "%Y-%m-%d %H:%M:%S"
                )
            else:
                started_dt = now - datetime.timedelta(seconds=duration)

            ended_dt = started_dt + datetime.timedelta(seconds=duration)
        except Exception:
            ended_dt = now

        payload = {
            "ended_at": (
                ended_dt.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            ),

            "duration": duration,

            "size": size
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

                print(
                    f"[Recorder][Camera "
                    f"{self.camera_id}] "
                    f"Відео завершено: "
                    f"{self.file}"
                )

                print(
                    f"[Recorder][Camera "
                    f"{self.camera_id}] "
                    f"Тривалість: "
                    f"{duration} сек."
                )

                print(
                    f"[Recorder][Camera "
                    f"{self.camera_id}] "
                    f"Розмір: "
                    f"{size / 1024 / 1024:.2f} MB"
                )

                return True

            print(
                f"[Recorder][Camera "
                f"{self.camera_id}] "
                f"Помилка завершення "
                f"Laravel HTTP "
                f"{response.status_code}"
            )

        except requests.RequestException as e:

            print(
                f"[Recorder][Camera "
                f"{self.camera_id}] "
                f"Laravel недоступний "
                f"при завершенні: {e}"
            )

        except Exception as e:

            print(
                f"[Recorder][Camera "
                f"{self.camera_id}] "
                f"Помилка finish: {e}"
            )

        return False

    # ========================================================
    # ПЕРЕКОНВЕРТАЦІЯ В H.264 — ФОНОВА ЧЕРГА
    # ========================================================

    def queue_transcode(self, filepath):

        if not filepath or not os.path.exists(filepath):
            return False

        if not _ffmpeg_available():
            # ГУЧНИЙ пропуск: без ffmpeg у PATH фонове стиснення
            # неможливе в принципі (OpenCV VideoWriter не вміє
            # CRF). Файл залишається з дефолтним високим бітрейтом.
            print(
                f"[Recorder][Camera "
                f"{self.camera_id}] "
                f"ffmpeg НЕ знайдено в PATH — "
                f"пережаття пропущено ({filepath}). "
                f"Встановіть ffmpeg і перезапустіть ai_server: "
                f"winget install Gyan.FFmpeg"
            )
            return False

        queue = getattr(self, "transcode_queue", None)

        if queue is None:
            self.transcode_queue = []
            queue = self.transcode_queue

        lock = getattr(self, "transcode_lock", None)

        queued_len = 0

        if lock is not None:
            try:
                with lock:
                    if filepath not in queue:
                        queue.append(filepath)

                    queued_len = len(queue)
            except Exception:
                if filepath not in queue:
                    queue.append(filepath)

                try:
                    queued_len = len(queue)
                except Exception:
                    queued_len = 0
        else:
            if filepath not in queue:
                queue.append(filepath)

            try:
                queued_len = len(queue)
            except Exception:
                queued_len = 0

        print(
            f"[Recorder][Camera "
            f"{self.camera_id}] "
            f"Файл у черзі транскоду "
            f"({queued_len} в черзі): {filepath}"
        )

        self._ensure_transcode_thread()

        return True

    def _ensure_transcode_thread(self):

        try:
            thread = getattr(self, "transcode_thread", None)

            if thread is not None and thread.is_alive():
                return

            import threading

            thread = threading.Thread(
                target=self._transcode_worker,
                name=(
                    f"RecorderTranscode-"
                    f"{self.camera_id}"
                ),
                daemon=True,
            )

            self.transcode_thread = thread

            thread.start()
        except Exception as e:
            print(
                f"[Recorder][Camera "
                f"{self.camera_id}] "
                f"Не вдалося запустити transcode-потік: {e}"
            )

    def _transcode_worker(self):

        while True:
            filepath = None

            lock = getattr(self, "transcode_lock", None)

            try:
                if lock is not None:
                    with lock:
                        if self.transcode_queue:
                            filepath = self.transcode_queue.pop(0)
                else:
                    if self.transcode_queue:
                        filepath = self.transcode_queue.pop(0)
            except Exception:
                filepath = None

            if not filepath:
                break

            try:
                self.ensure_browser_compatible(filepath)
            except Exception as e:
                print(
                    f"[Recorder][Camera "
                    f"{self.camera_id}] "
                    f"Помилка фонового transcode: {e}"
                )

    def ensure_browser_compatible(self, filepath):

        if not filepath or not os.path.exists(filepath):
            return False

        if not _ffmpeg_available():
            return False

        # Фонове СТИСНЕННЯ + faststart одним проходом:
        # libx264 CRF 28 + даунскейл до 720p дає -60..-70%
        # розміру від вже зменшеного файлу. Разом із даунскейлом
        # при записі: ~300 МБ -> ~40-60 МБ за 5 хв.
        # Працює у фоновому потоці — запис не гальмує.
        try:
            size_before = os.path.getsize(filepath)

            if size_before <= 0:
                return False
        except OSError:
            return False

        tmp_path = filepath + ".faststart.mp4"

        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass

        # CRF/preset/розмір — з панелі (transcode_*), fallback — константи.
        try:
            crf = str(int(runtime_config.transcode_crf()))
        except Exception:
            try:
                crf = str(int(TRANSCODE_CRF))
            except (TypeError, ValueError):
                crf = "28"

        try:
            preset = str(
                runtime_config.transcode_preset() or "veryfast"
            )
        except Exception:
            try:
                preset = str(TRANSCODE_PRESET or "veryfast")
            except Exception:
                preset = "veryfast"

        try:
            cfg_w, cfg_h = runtime_config.record_max_size()
            max_w = int(cfg_w or 0)
            max_h = int(cfg_h or 0)
        except Exception:
            try:
                max_w = int(RECORD_MAX_WIDTH or 0)
                max_h = int(RECORD_MAX_HEIGHT or 0)
            except (TypeError, ValueError):
                max_w, max_h = 0, 0

        # scale зі збереженням пропорцій, тільки зменшення.
        # force_original_aspect_ratio=decrease вписує кадр
        # у RECORD_MAX_* без спотворень; другий scale добиває
        # парні розміри (вимога H.264). Без ком у min() —
        # кома в -vf роздільник фільтрів, її треба екранувати,
        # тому використовуємо стандартну опцію ffmpeg.
        if max_w > 0 and max_h > 0:
            vf_scale = (
                f"scale={max_w}:{max_h}:"
                f"force_original_aspect_ratio=decrease,"
                f"scale=trunc(iw/2)*2:trunc(ih/2)*2"
            )
        else:
            vf_scale = "scale=trunc(iw/2)*2:trunc(ih/2)*2"

        # Аудіо: наші MP4 пише OpenCV — доріжки немає.
        # З -c:a aac ffmpeg падає (ненульовий код) і пережаття
        # мовчки пропускається. Тому: є аудіо -> aac, немає -> -an.
        try:
            has_audio = _has_audio_stream(filepath)
        except Exception:
            has_audio = False

        if has_audio:
            audio_args = ["-c:a", "aac"]
        else:
            audio_args = ["-an"]

        cmd = [
            "ffmpeg",
            "-y",
            "-i", filepath,
            "-c:v", "libx264",
            "-preset", preset,
            "-crf", crf,
            "-pix_fmt", "yuv420p",
            "-vf", vf_scale,
            *audio_args,
            "-movflags", "+faststart",
            tmp_path,
        ]

        print(
            f"[Recorder][Camera "
            f"{self.camera_id}] "
            f"Стискаю: {filepath} "
            f"(crf={crf} {preset}, "
            f"аудіо={'aac' if has_audio else 'немає (-an)'}, "
            f"ffmpeg={_ffmpeg_path()})"
        )

        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=300,
            )
        except Exception as e:
            print(
                f"[Recorder][Camera "
                f"{self.camera_id}] "
                f"ffmpeg помилка запуску: {e}"
            )
            return False

        if result.returncode != 0 or not os.path.exists(tmp_path):
            # ГУЧНА помилка: без хвоста stderr діагностувати
            # неможливо (раніше тут була тиша).
            try:
                err = result.stderr.decode(
                    "utf-8", "ignore"
                )[-1500:]
            except Exception:
                err = "?"

            print(
                f"[Recorder][Camera "
                f"{self.camera_id}] "
                f"ffmpeg код {result.returncode}: {err}"
            )

            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except OSError:
                pass
            return False

        try:
            size_after = os.path.getsize(tmp_path)

            if size_after <= 0:
                os.remove(tmp_path)
                return False
        except OSError:
            return False

        # Якщо пережатий файл раптом більший — залишаємо оригінал.
        try:
            keep_smaller = bool(TRANSCODE_KEEP_SMALLER)
        except Exception:
            keep_smaller = True

        if keep_smaller and size_after >= size_before:
            try:
                os.remove(tmp_path)
            except OSError:
                pass

            print(
                f"[Recorder][Camera "
                f"{self.camera_id}] "
                f"Пережаття не дало виграшу "
                f"({size_before} -> {size_after}) — "
                f"залишаємо оригінал"
            )

            return False

        try:
            os.replace(tmp_path, filepath)

            print(
                f"[Recorder][Camera "
                f"{self.camera_id}] "
                f"MP4 стиснуто: "
                f"{size_before} -> {size_after} байт "
                f"(-{100 - int(size_after * 100 / max(1, size_before))}%)"
            )

            # Розмір на диску змінився — оновлюємо БД,
            # щоб дашборд показував чесне місце.
            try:
                self._update_video_size(size_after)
            except Exception:
                pass

            return True
        except OSError as e:
            print(
                f"[Recorder][Camera "
                f"{self.camera_id}] "
                f"Не вдалося замінити MP4: {e}"
            )
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except OSError:
                pass
            return False

    # ========================================================
    # РЕАЛЬНА ТРИВАЛІСТЬ MP4 (ПЕРЕВІРКА)
    # ========================================================

    @staticmethod
    def probe_duration(filepath, fallback=0):
        """Рахує тривалість за реальними кадрами MP4.

        Повертає fallback, якщо файл не читається.
        """
        try:
            fallback = int(fallback or 0)
        except (TypeError, ValueError):
            fallback = 0

        if not filepath or not os.path.exists(filepath):
            return max(0, fallback)

        cap = None

        try:
            cap = cv2.VideoCapture(filepath)

            if not cap.isOpened():
                return max(0, fallback)

            frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            fps = cap.get(cv2.CAP_PROP_FPS)

            if (
                frames is None
                or fps is None
                or frames <= 0
                or fps <= 0
            ):
                return max(0, fallback)

            return max(0, int(round(frames / fps)))
        except Exception:
            return max(0, fallback)
        finally:
            if cap is not None:
                try:
                    cap.release()
                except Exception:
                    pass

    # ========================================================
    # WRITE
    # ========================================================

    def write(
        self,
        frame
    ):

        if frame is None:

            return

        # ----------------------------------------------------
        # Замір реального fps циклу (ковзне середнє).
        # YOLO гальмує цикл: номінальні 20 fps камери
        # на практиці можуть бути 5-8 fps.
        # ----------------------------------------------------

        now_ts = time.time()

        try:
            last_ts = self._last_write_ts

            if last_ts is not None and now_ts > last_ts:
                instant = 1.0 / (now_ts - last_ts)

                if 0.5 <= instant <= 120:
                    prev = float(
                        getattr(self, "measured_fps", 0)
                        or self.fps
                    )

                    self.measured_fps = (
                        prev * 0.95 + instant * 0.05
                    )
        except Exception:
            pass

        self._last_write_ts = now_ts

        # ----------------------------------------------------
        # Якщо Writer ще не створений — створюємо з РЕАЛЬНОГО
        # кадру (розмір беремо з frame, а не з cap.get()).
        # ----------------------------------------------------

        if self.writer is None:

            if not self.create_file(first_frame=frame):

                return

        # ----------------------------------------------------
        # Перевірка розміру кадру: якщо камера змінила роздільну
        # здатність посеред сегмента — приводимо кадр до
        # розміру сегмента (інакше VideoWriter мовчки псує файл).
        # ----------------------------------------------------

        try:

            frame_height, frame_width = (
                frame.shape[:2]
            )

            if (
                frame_width != self.width
                or
                frame_height != self.height
            ):

                frame = cv2.resize(
                    frame,
                    (
                        self.width,
                        self.height
                    )
                )

        except Exception as e:

            print(
                f"[Recorder][Camera "
                f"{self.camera_id}] "
                f"Помилка обробки frame: {e}"
            )

            return

        # ----------------------------------------------------
        # Ротація сегмента — ЗА ЧАСОМ СТІНИ.
        # ----------------------------------------------------

        now_ts = time.time()

        if self.start_time is None:

            self.start_time = now_ts

        elapsed = now_ts - float(self.start_time)

        # Довжина сегмента — з панелі (segment_seconds).
        # Застосовується при наступній ротації: поточний файл
        # не ріжемо посеред запису, щоб не отримати битий MP4.
        try:
            segment_limit = float(_segment_seconds())
        except (TypeError, ValueError):
            segment_limit = 300.0

        if segment_limit < 30.0:
            segment_limit = 30.0

        if elapsed >= segment_limit:

            self.release()

            if not self.create_file(first_frame=frame):

                return

            now_ts = time.time()

        # ----------------------------------------------------
        # Запис 1:1 — кожен кадр з черги = 1 кадр у файл.
        # Багатопотоковий режим: потік запису отримує СВІЖІ
        # кадри з черги drop-oldest, темп рівний, YOLO не
        # гальмує. Дублів/дропів НЕМАЄ: фризи і перемотка
        # неможливі як клас.
        # Невідповідність header_fps vs реальний fps закриває
        # _maybe_fix_header(): перші 3 сек сегмента калібруємо
        # заголовок під виміряний fps і перевідкриваємо файл.
        # ----------------------------------------------------

        # Оновлюємо замір реального fps (ковзне середнє).
        try:

            if (
                self._last_write_ts is not None
                and isinstance(self._last_write_ts, (int, float))
            ):

                dt = now_ts - float(self._last_write_ts)

                if 0.005 < dt < 5.0:

                    instant = 1.0 / dt

                    if 1.0 <= instant <= 120.0:

                        alpha = 0.2

                        self.measured_fps = (
                            (1.0 - alpha) * float(self.measured_fps)
                            + alpha * instant
                        )

        except (TypeError, ValueError):

            pass

        self._last_write_ts = now_ts

        # Калібрування заголовка на старті сегмента.
        try:

            if not self._header_fix_done:

                if self._header_fix_ts <= 0:

                    self._header_fix_ts = now_ts

                self._header_fix_frames += 1

                if now_ts - self._header_fix_ts >= 3.0:

                    self._maybe_fix_header()

        except Exception:

            pass

        try:

            self.writer.write(
                frame
            )

            self.frames_written += 1

        except Exception as e:

            print(
                f"[Recorder][Camera "
                f"{self.camera_id}] "
                f"Помилка запису: {e}"
            )

    # ========================================================
    # RELEASE
    # ========================================================

    def release(self):

        # ----------------------------------------------------
        # Якщо нічого не записується
        # ----------------------------------------------------

        if self.writer is None:

            return

        current_file = self.file

        # ----------------------------------------------------
        # Закриваємо VideoWriter
        # ----------------------------------------------------

        try:

            self.writer.release()

        except Exception as e:

            print(
                f"[Recorder][Camera "
                f"{self.camera_id}] "
                f"Помилка release Writer: {e}"
            )

        self.writer = None

        # ----------------------------------------------------
        # Тепер MP4 фізично закритий.
        # Можна визначати його розмір.
        # ----------------------------------------------------

        if current_file:

            self.file = current_file

            self.finish_video()

        # ----------------------------------------------------
        # Очищення стану
        # ----------------------------------------------------

        self.file = None

        self.start_time = None

        self.laravel_video_id = None

        print(
            f"[Recorder][Camera "
            f"{self.camera_id}] "
            "Recorder звільнено"
        )

