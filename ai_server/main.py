import os
import time
import math
import cv2
import numpy as np

from app.event_manager import save_event
from app.object_tracker import ObjectTracker
from camera_system import CameraSystem


EVENTS_DIR = "events"

WINDOW_NAME = "AI Video Surveillance System"

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720

CELL_WIDTH = 640
CELL_HEIGHT = 360

TEXT_COLOR = (255, 255, 255)
BOX_COLOR = (0, 255, 0)
HEADER_COLOR = (0, 0, 0)
OFFLINE_COLOR = (0, 0, 255)
ONLINE_COLOR = (0, 255, 0)
WARNING_COLOR = (0, 255, 255)

# Значки класів YOLO для OpenCV-вікна.
# OpenCV Hershey НЕ вміє малювати emoji, тому тут ASCII-маркери:
# [P]=person, [C]=car, [T]=truck, [B]=bus — читається на відеостіні.
OBJECT_ICON_ASCII = {
    "person": "[P]",
    "car": "[C]",
    "truck": "[T]",
    "bus": "[B]",
    "bicycle": "[BIKE]",
    "motorbike": "[MOTO]",
    "motorcycle": "[MOTO]",
    "dog": "[DOG]",
    "cat": "[CAT]",
    "bird": "[BIRD]",
}

OBJECT_LABEL_UA = {
    "person": "Lyudyna",
    "car": "Avto",
    "truck": "Vantazhivka",
    "bus": "Avtobus",
    "bicycle": "Velosyped",
    "motorbike": "Mototsykl",
    "motorcycle": "Mototsykl",
    "dog": "Sobaka",
    "cat": "Kit",
    "bird": "Ptakh",
}


def object_icon_ascii(name):
    return OBJECT_ICON_ASCII.get(str(name or "").lower(), "[*]")


def object_label_ua(name):
    key = str(name or "").lower()
    return OBJECT_LABEL_UA.get(key, str(name or "unknown"))


def object_badge_ascii(name):
    return f"{object_icon_ascii(name)} {object_label_ua(name)}"


def ensure_events_directory():
    os.makedirs(EVENTS_DIR, exist_ok=True)


def safe_object_name(name):
    if not name:
        return "unknown"

    name = str(name)

    for char in '<>:"/\\|?*':
        name = name.replace(char, "_")

    return name


def save_event_photo(frame, camera_id, object_name, logical_id):
    if frame is None:
        return None

    try:
        ensure_events_directory()

        timestamp = int(time.time())

        filename = (
            f"camera_{camera_id}_"
            f"{safe_object_name(object_name)}_"
            f"{logical_id}_"
            f"{timestamp}.jpg"
        )

        filepath = os.path.join(
            EVENTS_DIR,
            filename
        )

        if cv2.imwrite(filepath, frame):
            print(f"[PHOTO] Фото збережено: {filepath}")
            return filepath

        print(f"[PHOTO] Не вдалося зберегти: {filepath}")

    except Exception as e:
        print(f"[PHOTO] Помилка: {e}")

    return None


def draw_objects(frame, objects):
    if frame is None:
        return frame

    if not isinstance(objects, list):
        return frame

    for obj in objects:

        if not isinstance(obj, dict):
            continue

        bbox = obj.get("bbox")

        if not isinstance(bbox, dict):
            continue

        try:
            x1 = int(bbox.get("x1", 0))
            y1 = int(bbox.get("y1", 0))
            x2 = int(bbox.get("x2", 0))
            y2 = int(bbox.get("y2", 0))
        except (TypeError, ValueError):
            continue

        object_name = obj.get(
            "object",
            "unknown"
        )

        confidence = float(
            obj.get("confidence", 0)
        )

        logical_id = obj.get(
            "logical_id"
        )

        yolo_id = obj.get(
            "id"
        )

        label = (
            f"{object_icon_ascii(object_name)} "
            f"{object_label_ua(object_name)} "
            f"{confidence:.2f}"
        )

        if logical_id is not None:
            label += f" L:{logical_id}"

        if yolo_id is not None:
            label += f" Y:{yolo_id}"

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            BOX_COLOR,
            2
        )

        (
            text_size,
            baseline
        ) = cv2.getTextSize(
            label,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            1
        )

        text_width, text_height = text_size

        text_y = max(
            y1 - 8,
            text_height + 8
        )

        cv2.rectangle(
            frame,
            (
                x1,
                text_y - text_height - baseline - 4
            ),
            (
                x1 + text_width + 6,
                text_y + 3
            ),
            HEADER_COLOR,
            -1
        )

        cv2.putText(
            frame,
            label,
            (x1 + 3, text_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            TEXT_COLOR,
            1,
            cv2.LINE_AA
        )

    return frame


def draw_camera_header(
    frame,
    camera_name,
    camera_id,
    status,
    objects_count
):
    if frame is None:
        return frame

    height, width = frame.shape[:2]

    cv2.rectangle(
        frame,
        (0, 0),
        (width, 38),
        HEADER_COLOR,
        -1
    )

    status_text = str(
        status or "OFFLINE"
    ).upper()

    if status_text == "ONLINE":
        status_color = ONLINE_COLOR
    elif status_text in (
        "OFFLINE",
        "ERROR"
    ):
        status_color = OFFLINE_COLOR
    else:
        status_color = WARNING_COLOR

    title = (
        f"{camera_name} "
        f"[ID: {camera_id}]"
    )

    cv2.putText(
        frame,
        title,
        (10, 25),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        TEXT_COLOR,
        2,
        cv2.LINE_AA
    )

    status_x = max(
        width - 230,
        250
    )

    cv2.putText(
        frame,
        f"STATUS: {status_text}",
        (status_x, 25),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        status_color,
        2,
        cv2.LINE_AA
    )

    cv2.putText(
        frame,
        f"OBJECTS: {objects_count}",
        (10, height - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        TEXT_COLOR,
        1,
        cv2.LINE_AA
    )

    return frame


def create_offline_frame(
    camera_name,
    camera_id,
    status="OFFLINE"
):
    frame = np.zeros(
        (
            CELL_HEIGHT,
            CELL_WIDTH,
            3
        ),
        dtype=np.uint8
    )

    height, width = frame.shape[:2]

    cv2.rectangle(
        frame,
        (0, 0),
        (width, 38),
        HEADER_COLOR,
        -1
    )

    cv2.putText(
        frame,
        f"{camera_name} [ID: {camera_id}]",
        (10, 25),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        TEXT_COLOR,
        2,
        cv2.LINE_AA
    )

    text = str(
        status or "OFFLINE"
    ).upper()

    (
        text_size,
        _
    ) = cv2.getTextSize(
        text,
        cv2.FONT_HERSHEY_SIMPLEX,
        1.4,
        3
    )

    text_width, text_height = text_size

    x = (
        width - text_width
    ) // 2

    y = (
        height + text_height
    ) // 2

    cv2.putText(
        frame,
        text,
        (x, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.4,
        OFFLINE_COLOR,
        3,
        cv2.LINE_AA
    )

    return frame


def resize_to_cell(frame):
    if frame is None:
        return create_offline_frame(
            "Camera",
            "?",
            "OFFLINE"
        )

    try:
        return cv2.resize(
            frame,
            (
                CELL_WIDTH,
                CELL_HEIGHT
            ),
            interpolation=cv2.INTER_AREA
        )
    except Exception as e:
        print(
            f"[VIDEO WALL] Resize error: {e}"
        )

        return create_offline_frame(
            "Camera",
            "?",
            "ERROR"
        )


def calculate_grid(camera_count):

    if camera_count <= 0:
        return 1, 1

    if camera_count == 1:
        return 1, 1

    if camera_count == 2:
        return 2, 1

    if camera_count <= 4:
        return 2, 2

    if camera_count <= 6:
        return 3, 2

    if camera_count <= 9:
        return 3, 3

    columns = 4
    rows = math.ceil(
        camera_count / columns
    )

    return columns, rows


def create_video_wall(camera_frames):

    if not camera_frames:

        wall = np.zeros(
            (
                WINDOW_HEIGHT,
                WINDOW_WIDTH,
                3
            ),
            dtype=np.uint8
        )

        text = "NO ACTIVE CAMERAS"

        (
            text_size,
            _
        ) = cv2.getTextSize(
            text,
            cv2.FONT_HERSHEY_SIMPLEX,
            1.2,
            2
        )

        text_width, text_height = text_size

        x = (
            WINDOW_WIDTH - text_width
        ) // 2

        y = (
            WINDOW_HEIGHT + text_height
        ) // 2

        cv2.putText(
            wall,
            text,
            (x, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.2,
            TEXT_COLOR,
            2,
            cv2.LINE_AA
        )

        return wall

    camera_count = len(
        camera_frames
    )

    columns, rows = calculate_grid(
        camera_count
    )

    wall_width = (
        CELL_WIDTH * columns
    )

    wall_height = (
        CELL_HEIGHT * rows
    )

    wall = np.zeros(
        (
            wall_height,
            wall_width,
            3
        ),
        dtype=np.uint8
    )

    for index, camera_data in enumerate(
        camera_frames
    ):

        camera_id = camera_data.get(
            "camera_id",
            "?"
        )

        camera_name = camera_data.get(
            "name",
            f"Camera {camera_id}"
        )

        frame = camera_data.get(
            "frame"
        )

        objects = camera_data.get(
            "objects",
            []
        )

        status = camera_data.get(
            "status",
            "OFFLINE"
        )

        if frame is None:

            cell = create_offline_frame(
                camera_name,
                camera_id,
                status
            )

        else:

            cell = resize_to_cell(
                frame
            )

        row = index // columns
        column = index % columns

        x = (
            column * CELL_WIDTH
        )

        y = (
            row * CELL_HEIGHT
        )

        wall[
            y:y + CELL_HEIGHT,
            x:x + CELL_WIDTH
        ] = cell

    try:

        wall = cv2.resize(
            wall,
            (
                WINDOW_WIDTH,
                WINDOW_HEIGHT
            ),
            interpolation=cv2.INTER_AREA
        )

    except Exception as e:

        print(
            f"[VIDEO WALL] "
            f"Помилка: {e}"
        )

    return wall


def process_new_event(
    frame,
    camera_id,
    camera_name,
    obj,
    tracker
):

    if not isinstance(obj, dict):
        return

    logical_id = obj.get(
        "logical_id"
    )

    if logical_id is None:
        return

    if tracker.event_created(
        camera_id,
        logical_id
    ):
        return

    object_name = obj.get(
        "object",
        "unknown"
    )

    confidence = float(
        obj.get(
            "confidence",
            0
        )
    )

    bbox = obj.get(
        "bbox",
        {}
    )

    yolo_track_id = obj.get(
        "id"
    )

    print()
    print("=" * 65)
    print("НОВИЙ ЛОГІЧНИЙ ОБ'ЄКТ")
    print("=" * 65)

    print(
        f"Камера: {camera_name}"
    )

    print(
        f"Camera ID: {camera_id}"
    )

    print(
        f"Logical ID: {logical_id}"
    )

    print(
        f"YOLO Track ID: {yolo_track_id}"
    )

    print(
        f"Об'єкт: {object_name}"
    )

    print(
        f"Confidence: {confidence:.4f}"
    )

    print(
        f"BBox: {bbox}"
    )

    image_path = save_event_photo(
        frame,
        camera_id,
        object_name,
        logical_id
    )

    if image_path:
        print(
            f"[EVENT] Фото: {image_path}"
        )

    try:

        event = save_event(
            object_id=yolo_track_id,
            object_name=object_name,
            confidence=confidence,
            bbox=bbox,
            image_path=image_path,
            camera_id=camera_id,
            camera_name=camera_name,
            status="active"
        )

        if event:

            event_id = event.get(
                "id"
            )

            print(
                f"[EVENT] "
                f"Подію збережено в Laravel. "
                f"ID={event_id}"
            )

        else:

            print(
                "[EVENT] "
                "Laravel не повернув подію"
            )

    except Exception as e:

        print(
            f"[EVENT] "
            f"Помилка: {e}"
        )

    tracker.mark_event_created(
        camera_id,
        logical_id
    )


def main():

    print()
    print("=" * 70)
    print("AI VIDEO SURVEILLANCE SYSTEM")
    print("=" * 70)
    print()

    ensure_events_directory()

    tracker = ObjectTracker()

    print(
        "ObjectTracker створено"
    )

    camera_system = CameraSystem()

    try:

        if not camera_system.start():

            print()
            print(
                "Не вдалося запустити систему камер"
            )

            return

    except Exception as e:

        print()
        print("=" * 70)
        print("КРИТИЧНА ПОМИЛКА")
        print("=" * 70)

        print(e)

        print("=" * 70)

        return

    print()
    print(
        "Основний цикл AI запущено"
    )
    print()

    cv2.namedWindow(
        WINDOW_NAME,
        cv2.WINDOW_NORMAL
    )

    cv2.resizeWindow(
        WINDOW_NAME,
        WINDOW_WIDTH,
        WINDOW_HEIGHT
    )

    try:

        while camera_system.running:

            camera_frames = []

            with camera_system.manager.lock:

                cameras = dict(
                    camera_system.manager.cameras
                )

            for camera_id, camera in cameras.items():

                camera_name = camera.get(
                    "name",
                    f"Camera {camera_id}"
                )

                status = camera_system.get_status(
                    camera_id
                )

                frame = camera_system.get_frame(
                    camera_id
                )

                objects = camera_system.get_objects(
                    camera_id
                )

                if not isinstance(
                    objects,
                    list
                ):
                    objects = []

                if frame is None:

                    camera_frames.append(
                        {
                            "camera_id": camera_id,
                            "name": camera_name,
                            "frame": None,
                            "objects": [],
                            "status": status
                        }
                    )

                    continue

                display_frame = frame.copy()

                try:

                    tracked_objects = tracker.update(
                        camera_id,
                        objects
                    )

                except Exception as e:

                    print(
                        f"[Tracker] "
                        f"Камера {camera_id}: "
                        f"{e}"
                    )

                    tracked_objects = []

                if tracked_objects:

                    print(
                        f"[MAIN] "
                        f"Камера {camera_id}: "
                        f"нових об'єктів = "
                        f"{len(tracked_objects)}"
                    )

                for new_object in tracked_objects:

                    try:

                        process_new_event(
                            frame=display_frame,
                            camera_id=camera_id,
                            camera_name=camera_name,
                            obj=new_object,
                            tracker=tracker
                        )

                    except Exception as e:

                        print(
                            f"[MAIN] "
                            f"Помилка події: {e}"
                        )

                active_objects = (
                    tracker.get_active_objects(
                        camera_id
                    )
                )

                display_objects = []

                for obj in objects:

                    if not isinstance(
                        obj,
                        dict
                    ):
                        continue

                    display_object = dict(
                        obj
                    )

                    yolo_id = obj.get(
                        "id"
                    )

                    object_name = obj.get(
                        "object",
                        "unknown"
                    )

                    bbox = obj.get(
                        "bbox"
                    )

                    logical_id = None

                    if yolo_id is not None:

                        for active_id, active in active_objects.items():

                            if (
                                active.get(
                                    "yolo_track_id"
                                ) == yolo_id
                                and
                                active.get(
                                    "object"
                                ) == object_name
                            ):

                                logical_id = active_id
                                break

                    if logical_id is None and bbox:

                        try:

                            x1 = float(
                                bbox.get(
                                    "x1",
                                    0
                                )
                            )

                            y1 = float(
                                bbox.get(
                                    "y1",
                                    0
                                )
                            )

                            x2 = float(
                                bbox.get(
                                    "x2",
                                    0
                                )
                            )

                            y2 = float(
                                bbox.get(
                                    "y2",
                                    0
                                )
                            )

                            cx = (
                                x1 + x2
                            ) / 2

                            cy = (
                                y1 + y2
                            ) / 2

                            best_distance = None
                            best_id = None

                            for active_id, active in active_objects.items():

                                if active.get(
                                    "object"
                                ) != object_name:
                                    continue

                                active_bbox = active.get(
                                    "bbox"
                                )

                                if not active_bbox:
                                    continue

                                ax = (
                                    float(
                                        active_bbox.get(
                                            "x1",
                                            0
                                        )
                                    )
                                    +
                                    float(
                                        active_bbox.get(
                                            "x2",
                                            0
                                        )
                                    )
                                ) / 2

                                ay = (
                                    float(
                                        active_bbox.get(
                                            "y1",
                                            0
                                        )
                                    )
                                    +
                                    float(
                                        active_bbox.get(
                                            "y2",
                                            0
                                        )
                                    )
                                ) / 2

                                distance = math.sqrt(
                                    (cx - ax) ** 2
                                    +
                                    (cy - ay) ** 2
                                )

                                if (
                                    best_distance is None
                                    or
                                    distance < best_distance
                                ):

                                    best_distance = distance
                                    best_id = active_id

                            logical_id = best_id

                        except Exception:
                            logical_id = None

                    if logical_id is not None:

                        display_object[
                            "logical_id"
                        ] = logical_id

                    display_objects.append(
                        display_object
                    )

                display_frame = draw_objects(
                    display_frame,
                    display_objects
                )

                display_frame = draw_camera_header(
                    display_frame,
                    camera_name,
                    camera_id,
                    status,
                    len(objects)
                )

                camera_frames.append(
                    {
                        "camera_id": camera_id,
                        "name": camera_name,
                        "frame": display_frame,
                        "objects": objects,
                        "status": status
                    }
                )

            video_wall = create_video_wall(
                camera_frames
            )

            cv2.imshow(
                WINDOW_NAME,
                video_wall
            )

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q") or key == 27:

                print()
                print(
                    "Отримано команду завершення"
                )

                break

            time.sleep(0.01)

    except KeyboardInterrupt:

        print()
        print(
            "Отримано Ctrl+C"
        )

    except Exception as e:

        print()
        print("=" * 70)
        print("ПОМИЛКА ОСНОВНОГО ЦИКЛУ")
        print("=" * 70)

        print(e)

        print("=" * 70)

    finally:

        print()
        print(
            "Завершення AI Video Surveillance System..."
        )

        try:
            camera_system.stop()
        except Exception as e:
            print(
                f"[MAIN] "
                f"Помилка зупинки: {e}"
            )

        try:
            tracker.clear()
        except Exception:
            pass

        try:
            cv2.destroyAllWindows()
        except Exception:
            pass

        print(
            "AI Video Surveillance System зупинено"
        )


if __name__ == "__main__":
    main()

