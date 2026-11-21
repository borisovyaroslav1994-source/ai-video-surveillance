import math
import threading


class ObjectTracker:
    """
    Логічний tracker об'єктів поверх YOLO Tracking.

    Основні принципи:

    1. Стан кожної камери зберігається окремо.
    2. Одна фізична поява об'єкта = одна подія.
    3. Зміна YOLO track_id не повинна автоматично створювати
       нову подію.
    4. Об'єкт повинен зникнути достатню кількість кадрів,
       перш ніж вважатися таким, що покинув сцену.
    5. Після реального виходу об'єкта його повторна поява
       створює нову подію.
    """

    def __init__(
        self,
        max_missing_frames=150,
        iou_threshold=0.15,
        center_distance_threshold=180,
        min_match_score=0.20
    ):
        # -----------------------------------------------------
        # Стан:
        #
        # {
        #     camera_id: {
        #         logical_id: {
        #             ...
        #         }
        #     }
        # }
        # -----------------------------------------------------

        self.active_objects = {}

        self.max_missing_frames = max_missing_frames
        self.iou_threshold = iou_threshold
        self.center_distance_threshold = center_distance_threshold
        self.min_match_score = min_match_score

        self.lock = threading.RLock()

        # Глобальний логічний ID.
        #
        # Він НЕ використовується як YOLO ID.
        # Це внутрішній ID нашого tracker.
        self.next_logical_id = 1

    # =========================================================
    # CAMERA
    # =========================================================

    def _get_camera_objects(self, camera_id):
        """
        Повертає словник об'єктів конкретної камери.
        """

        with self.lock:

            if camera_id not in self.active_objects:
                self.active_objects[camera_id] = {}

            return self.active_objects[camera_id]

    # =========================================================
    # BBOX
    # =========================================================

    @staticmethod
    def _bbox(obj):
        """
        Отримує bbox з YOLO object.
        """

        if not isinstance(obj, dict):
            return None

        bbox = obj.get("bbox")

        if not isinstance(bbox, dict):
            return None

        try:

            x1 = float(bbox.get("x1", 0))
            y1 = float(bbox.get("y1", 0))
            x2 = float(bbox.get("x2", 0))
            y2 = float(bbox.get("y2", 0))

            if x2 <= x1 or y2 <= y1:
                return None

            return {
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2
            }

        except (TypeError, ValueError):

            return None

    # =========================================================
    # IOU
    # =========================================================

    @staticmethod
    def _iou(box1, box2):

        if box1 is None or box2 is None:
            return 0.0

        x_left = max(
            box1["x1"],
            box2["x1"]
        )

        y_top = max(
            box1["y1"],
            box2["y1"]
        )

        x_right = min(
            box1["x2"],
            box2["x2"]
        )

        y_bottom = min(
            box1["y2"],
            box2["y2"]
        )

        width = max(
            0.0,
            x_right - x_left
        )

        height = max(
            0.0,
            y_bottom - y_top
        )

        intersection = width * height

        if intersection <= 0:
            return 0.0

        area1 = (
            max(
                0.0,
                box1["x2"] - box1["x1"]
            )
            *
            max(
                0.0,
                box1["y2"] - box1["y1"]
            )
        )

        area2 = (
            max(
                0.0,
                box2["x2"] - box2["x1"]
            )
            *
            max(
                0.0,
                box2["y2"] - box2["y1"]
            )
        )

        union = (
            area1
            + area2
            - intersection
        )

        if union <= 0:
            return 0.0

        return intersection / union

    # =========================================================
    # CENTER
    # =========================================================

    @staticmethod
    def _center(box):

        if box is None:
            return None

        return (
            (box["x1"] + box["x2"]) / 2.0,
            (box["y1"] + box["y2"]) / 2.0
        )

    # =========================================================
    # DISTANCE
    # =========================================================

    @classmethod
    def _center_distance(cls, box1, box2):

        center1 = cls._center(box1)
        center2 = cls._center(box2)

        if center1 is None or center2 is None:
            return float("inf")

        return math.sqrt(
            (center1[0] - center2[0]) ** 2
            +
            (center1[1] - center2[1]) ** 2
        )

    # =========================================================
    # BOX SIZE
    # =========================================================

    @staticmethod
    def _box_size(box):

        if box is None:
            return 0.0

        width = max(
            1.0,
            box["x2"] - box["x1"]
        )

        height = max(
            1.0,
            box["y2"] - box["y1"]
        )

        return math.sqrt(
            width * width
            +
            height * height
        )

    # =========================================================
    # MATCH SCORE
    # =========================================================

    def _match_score(
        self,
        object_box,
        existing_box
    ):
        """
        Оцінює наскільки два bbox можуть належати
        одному фізичному об'єкту.

        Використовуємо:

        - IoU
        - відстань між центрами
        - розмір bbox
        """

        if object_box is None or existing_box is None:
            return 0.0

        iou = self._iou(
            object_box,
            existing_box
        )

        distance = self._center_distance(
            object_box,
            existing_box
        )

        size1 = self._box_size(
            object_box
        )

        size2 = self._box_size(
            existing_box
        )

        if size1 <= 0 or size2 <= 0:
            size_similarity = 0.0

        else:

            size_similarity = min(
                size1,
                size2
            ) / max(
                size1,
                size2
            )

        # -----------------------------------------------------
        # Сильний IoU
        # -----------------------------------------------------

        if iou >= self.iou_threshold:

            return (
                iou * 0.70
                +
                size_similarity * 0.30
            )

        # -----------------------------------------------------
        # Якщо IoU маленький, використовуємо відстань
        # -----------------------------------------------------

        dynamic_distance = max(
            self.center_distance_threshold,
            self._box_size(existing_box) * 0.80
        )

        if distance <= dynamic_distance:

            distance_score = (
                1.0
                -
                distance / dynamic_distance
            )

            return (
                distance_score * 0.70
                +
                size_similarity * 0.30
            )

        return 0.0

    # =========================================================
    # CREATE LOGICAL ID
    # =========================================================

    def _create_logical_id(self):

        with self.lock:

            logical_id = self.next_logical_id

            self.next_logical_id += 1

            return logical_id

    # =========================================================
    # FIND MATCH
    # =========================================================

    def _find_match(
        self,
        camera_objects,
        obj,
        used_logical_ids
    ):
        """
        Знаходить існуючий логічний об'єкт.

        Спочатку перевіряємо YOLO track_id.

        Якщо YOLO змінив ID — використовуємо bbox.
        """

        if not isinstance(obj, dict):
            return None

        yolo_track_id = obj.get("id")

        object_name = obj.get(
            "object",
            "unknown"
        )

        object_box = self._bbox(obj)

        # -----------------------------------------------------
        # 1. Пряме співпадіння YOLO ID
        # -----------------------------------------------------

        if yolo_track_id is not None:

            for logical_id, existing in camera_objects.items():

                if logical_id in used_logical_ids:
                    continue

                if existing.get("yolo_track_id") != yolo_track_id:
                    continue

                if existing.get("object") != object_name:
                    continue

                return logical_id

        # -----------------------------------------------------
        # 2. Пошук за положенням
        # -----------------------------------------------------

        if object_box is None:
            return None

        best_logical_id = None
        best_score = 0.0

        for logical_id, existing in camera_objects.items():

            if logical_id in used_logical_ids:
                continue

            if existing.get("object") != object_name:
                continue

            existing_box = existing.get("bbox")

            if existing_box is None:
                continue

            score = self._match_score(
                object_box,
                existing_box
            )

            if score < self.min_match_score:
                continue

            if score > best_score:

                best_score = score
                best_logical_id = logical_id

        return best_logical_id

    # =========================================================
    # UPDATE
    # =========================================================

    def update(
        self,
        camera_id,
        objects
    ):
        """
        Оновлює стан конкретної камери.

        Повертає ТІЛЬКИ нові логічні об'єкти.

        Саме вони повинні створювати подію.
        """

        with self.lock:

            camera_objects = (
                self._get_camera_objects(
                    camera_id
                )
            )

            if not isinstance(objects, list):
                objects = []

            # -------------------------------------------------
            # Всі існуючі об'єкти спочатку вважаємо
            # тимчасово відсутніми.
            # -------------------------------------------------

            for object_data in camera_objects.values():

                object_data["missing_frames"] = (
                    object_data.get(
                        "missing_frames",
                        0
                    )
                    + 1
                )

            new_events = []

            used_logical_ids = set()

            # -------------------------------------------------
            # Обробляємо YOLO objects
            # -------------------------------------------------

            for obj in objects:

                if not isinstance(obj, dict):
                    continue

                object_name = obj.get(
                    "object",
                    "unknown"
                )

                yolo_track_id = obj.get(
                    "id"
                )

                bbox = self._bbox(
                    obj
                )

                # ------------------------------------------------
                # Шукаємо існуючий логічний об'єкт
                # ------------------------------------------------

                logical_id = self._find_match(
                    camera_objects,
                    obj,
                    used_logical_ids
                )

                # =================================================
                # НОВИЙ ОБ'ЄКТ
                # =================================================

                if logical_id is None:

                    logical_id = (
                        self._create_logical_id()
                    )

                    camera_objects[logical_id] = {

                        "logical_id":
                            logical_id,

                        "object":
                            object_name,

                        "yolo_track_id":
                            yolo_track_id,

                        "bbox":
                            bbox,

                        "missing_frames":
                            0,

                        "frames_seen":
                            1,

                        "event_created":
                            False,

                        "created_at":
                            time_now(),

                    }

                    used_logical_ids.add(
                        logical_id
                    )

                    # ---------------------------------------------
                    # Створюємо копію для події
                    # ---------------------------------------------

                    event_object = dict(
                        obj
                    )

                    event_object["logical_id"] = (
                        logical_id
                    )

                    new_events.append(
                        event_object
                    )

                    # ---------------------------------------------
                    # ВАЖЛИВО:
                    #
                    # Подія вже повернена main.py.
                    # Але event_created НЕ ставимо тут.
                    #
                    # main.py поставить його після успішного
                    # збереження.
                    # ---------------------------------------------

                    continue

                # =================================================
                # ІСНУЮЧИЙ ОБ'ЄКТ
                # =================================================

                object_data = camera_objects[
                    logical_id
                ]

                object_data["object"] = (
                    object_name
                )

                object_data["yolo_track_id"] = (
                    yolo_track_id
                )

                object_data["bbox"] = bbox

                object_data["missing_frames"] = 0

                object_data["frames_seen"] = (
                    object_data.get(
                        "frames_seen",
                        0
                    )
                    + 1
                )

                used_logical_ids.add(
                    logical_id
                )

            # -------------------------------------------------
            # Видаляємо об'єкти, які реально зникли.
            # -------------------------------------------------

            objects_to_remove = []

            for logical_id, object_data in (
                camera_objects.items()
            ):

                missing_frames = (
                    object_data.get(
                        "missing_frames",
                        0
                    )
                )

                if missing_frames >= (
                    self.max_missing_frames
                ):

                    objects_to_remove.append(
                        logical_id
                    )

            for logical_id in objects_to_remove:

                object_data = camera_objects.get(
                    logical_id
                )

                if object_data:

                    print(
                        "[Tracker] "
                        f"Камера {camera_id}: "
                        f"об'єкт "
                        f"{object_data.get('object')} "
                        f"(logical={logical_id}, "
                        f"yolo={object_data.get('yolo_track_id')}) "
                        f"видалено з активних"
                    )

                del camera_objects[
                    logical_id
                ]

            return new_events

    # =========================================================
    # EVENT CREATED
    # =========================================================

    def mark_event_created(
        self,
        camera_id,
        logical_id
    ):
        """
        Позначає логічний об'єкт як такий,
        для якого подія вже була створена.
        """

        with self.lock:

            camera_objects = (
                self._get_camera_objects(
                    camera_id
                )
            )

            if logical_id not in camera_objects:
                return False

            camera_objects[
                logical_id
            ]["event_created"] = True

            return True

    # =========================================================
    # EVENT CREATED CHECK
    # =========================================================

    def event_created(
        self,
        camera_id,
        logical_id
    ):
        with self.lock:

            camera_objects = (
                self._get_camera_objects(
                    camera_id
                )
            )

            if logical_id not in camera_objects:
                return False

            return camera_objects[
                logical_id
            ].get(
                "event_created",
                False
            )

    # =========================================================
    # ACTIVE OBJECTS
    # =========================================================

    def get_active_objects(
        self,
        camera_id
    ):

        with self.lock:

            camera_objects = (
                self._get_camera_objects(
                    camera_id
                )
            )

            return {
                key: dict(value)
                for key, value
                in camera_objects.items()
            }

    # =========================================================
    # REMOVE CAMERA
    # =========================================================

    def remove_camera(
        self,
        camera_id
    ):

        with self.lock:

            if camera_id in self.active_objects:

                del self.active_objects[
                    camera_id
                ]

    # =========================================================
    # CLEAR
    # =========================================================

    def clear(self):

        with self.lock:

            self.active_objects.clear()

            self.next_logical_id = 1


# =============================================================
# TIME HELPER
# =============================================================

def time_now():
    """
    Повертає Unix timestamp.
    """
    import time

    return time.time()
