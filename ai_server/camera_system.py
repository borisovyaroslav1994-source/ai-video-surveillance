import threading
import time

from camera_manager import CameraManager


class CameraSystem:

    def __init__(self):

        self.manager = CameraManager()

        self.monitor_thread = None

        self.running = False

    # =====================================================
    # START
    # =====================================================

    def start(self):

        print()
        print("=" * 60)
        print(
            "AI VIDEO SURVEILLANCE SYSTEM"
        )
        print("=" * 60)

        # ---------------------------------------------
        # Запуск камер
        # ---------------------------------------------

        if not self.manager.start_all():

            print()
            print(
                "Не вдалося запустити "
                "жодної камери"
            )

            return False

        self.running = True

        # ---------------------------------------------
        # Моніторинг камер
        # ---------------------------------------------

        self.monitor_thread = threading.Thread(
            target=self.manager.monitor,
            name="CameraManagerMonitor",
            daemon=True
        )

        self.monitor_thread.start()

        print()
        print(
            "Моніторинг камер запущено"
        )

        print()
        print(
            "AI Video Surveillance System "
            "запущено"
        )

        print("=" * 60)

        return True

    # =====================================================
    # GET FRAMES
    # =====================================================

    def get_frames(self):

        result = {}

        with self.manager.lock:

            cameras = dict(
                self.manager.cameras
            )

        for camera_id, camera in cameras.items():

            worker = (
                self.manager.get_worker(
                    camera_id
                )
            )

            if worker is None:
                continue

            frame = worker.get_frame()

            if frame is None:
                continue

            objects = worker.get_objects()

            camera_name = camera.get(
                "name",
                f"Camera {camera_id}"
            )

            result[camera_id] = {

                "frame": frame,

                "name": camera_name,

                "objects": objects
            }

        return result

    # =====================================================
    # GET FRAME
    # =====================================================

    def get_frame(self, camera_id):

        return self.manager.get_frame(
            camera_id
        )

    # =====================================================
    # GET OBJECTS
    # =====================================================

    def get_objects(self, camera_id):

        return self.manager.get_objects(
            camera_id
        )

    # =====================================================
    # GET STATUS
    # =====================================================

    def get_status(self, camera_id):

        return self.manager.get_status(
            camera_id
        )

    # =====================================================
    # GET ALL STATUS
    # =====================================================

    def get_status_all(self):

        return self.manager.get_status_all()

    # =====================================================
    # GET MANAGER
    # =====================================================

    def get_manager(self):

        return self.manager

    # =====================================================
    # STOP
    # =====================================================

    def stop(self):

        print()
        print(
            "Зупинка AI Video "
            "Surveillance System..."
        )

        self.running = False

        try:

            self.manager.stop_all()

        except Exception as e:

            print(
                "Помилка зупинки "
                f"CameraManager: {e}"
            )

        if self.monitor_thread is not None:

            if self.monitor_thread.is_alive():

                self.monitor_thread.join(
                    timeout=6
                )

        self.monitor_thread = None

        print(
            "AI Video Surveillance System "
            "зупинено"
        )

    # =====================================================
    # RUN
    # =====================================================

    def run(self):

        if not self.start():

            return False

        try:

            while self.running:

                time.sleep(1)

        except KeyboardInterrupt:

            print()
            print(
                "Отримано Ctrl+C"
            )

        finally:

            self.stop()

        return True