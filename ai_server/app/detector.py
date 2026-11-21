from ultralytics import YOLO


class Detector:

    def __init__(self, camera_id=None):

        self.camera_id = camera_id

        print(
            f"[YOLO][Camera {camera_id}] "
            f"Завантаження моделі..."
        )

        self.model = YOLO("yolo11n.pt")

        print(
            f"[YOLO][Camera {camera_id}] "
            f"Модель завантажена"
        )

        # Об'єкти, які нас цікавлять
        self.target_classes = {
            "person",
            "car",
            "truck",
            "bus"
        }

    def detect(self, frame, confidence=0.5):

        if frame is None:
            return []

        try:

            results = self.model.track(
                source=frame,
                persist=True,
                tracker="bytetrack.yaml",
                conf=confidence,
                # imgsz=640: детекція на зменшеному кадрі (~3-4x швидше
                # на CPU). Повний кадр сюди вже приходить зменшеним
                # з camera_worker, це — страховка.
                # vid_stride=2: трекер пропускає кадри всередині,
                # що знімає навантаження без втрати трекінгу.
                imgsz=640,
                vid_stride=2,
                verbose=False
            )

            objects = []

            for result in results:

                names = result.names
                boxes = result.boxes

                if boxes is None:
                    continue

                for box in boxes:

                    try:

                        # Клас YOLO
                        cls_id = int(
                            box.cls[0].item()
                        )

                        # Confidence
                        conf = float(
                            box.conf[0].item()
                        )

                        # Назва об'єкта
                        if isinstance(names, dict):
                            object_name = names.get(
                                cls_id,
                                str(cls_id)
                            )
                        else:
                            object_name = str(
                                names[cls_id]
                            )

                        # Фільтр класів
                        if object_name not in self.target_classes:
                            continue

                        # Координати
                        xyxy = box.xyxy[0].tolist()

                        x1 = int(xyxy[0])
                        y1 = int(xyxy[1])
                        x2 = int(xyxy[2])
                        y2 = int(xyxy[3])

                        # Track ID
                        track_id = None

                        if box.id is not None:

                            track_id = int(
                                box.id[0].item()
                            )

                        objects.append(
                            {
                                "object": object_name,

                                "confidence": conf,

                                "bbox": {
                                    "x1": x1,
                                    "y1": y1,
                                    "x2": x2,
                                    "y2": y2
                                },

                                "id": track_id
                            }
                        )

                    except Exception as e:

                        print(
                            f"[YOLO][Camera {self.camera_id}] "
                            f"Помилка detection: {e}"
                        )

            return objects

        except Exception as e:

            print(
                f"[YOLO][Camera {self.camera_id}] "
                f"Помилка YOLO: {e}"
            )

            return []

    def reset_tracker(self):

        try:

            if (
                hasattr(self.model, "predictor")
                and
                self.model.predictor is not None
            ):

                self.model.predictor.trackers = []

        except Exception as e:

            print(
                f"[YOLO][Camera {self.camera_id}] "
                f"Помилка reset tracker: {e}"
            )

    def close(self):

        try:

            self.reset_tracker()

            self.model = None

            print(
                f"[YOLO][Camera {self.camera_id}] "
                f"Detector завершено"
            )

        except Exception as e:

            print(
                f"[YOLO][Camera {self.camera_id}] "
                f"Помилка завершення: {e}"
            )

