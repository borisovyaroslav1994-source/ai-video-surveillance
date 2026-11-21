
from pathlib import Path
import time

import torch
from ultralytics import YOLO

# Шлях до зображення відносно файлу benchmark.py
BASE_DIR = Path(__file__).resolve().parent
IMAGE = BASE_DIR.parent / "bus.jpg"
MODEL = BASE_DIR.parent / "yolo11n.pt"

if not IMAGE.exists():
    raise FileNotFoundError(f"Не знайдено зображення: {IMAGE}")

if not MODEL.exists():
    raise FileNotFoundError(f"Не знайдено модель: {MODEL}")

print(f"PyTorch: {torch.__version__}")
print(f"CUDA: {torch.cuda.is_available()}")
print(f"Зображення: {IMAGE}")
print("-" * 45)

devices = ["cpu"]

if torch.cuda.is_available():
    devices.append("cuda:0")

for device in devices:
    model = YOLO(str(MODEL))

    print(f"\nТестування: {device}")

    # Прогрів моделі
    for _ in range(5):
        model.predict(
            source=str(IMAGE),
            device=device,
            imgsz=640,
            verbose=False
        )

    times = []

    # 30 повторних вимірювань
    for _ in range(30):
        if device.startswith("cuda"):
            torch.cuda.synchronize()

        start = time.perf_counter()

        model.predict(
            source=str(IMAGE),
            device=device,
            imgsz=640,
            verbose=False
        )

        if device.startswith("cuda"):
            torch.cuda.synchronize()

        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)

    avg_ms = sum(times) / len(times)
    fps = 1000 / avg_ms

    print(f"Середній час: {avg_ms:.2f} мс")
    print(f"Швидкість: {fps:.2f} FPS")
    print("-" * 45)
