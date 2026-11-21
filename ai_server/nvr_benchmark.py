
"""Standalone reproducible video/YOLO+ByteTrack benchmark; does not edit NVR files."""
import argparse
import csv
import datetime as dt
import json
import os
import platform
import statistics
import time
from pathlib import Path

import cv2


def source_value(s):
    return int(s) if s.isdecimal() else s


def run(args, run_number):
    cap = cv2.VideoCapture(source_value(args.source))
    if not cap.isOpened():
        raise RuntimeError(f"Не вдалося відкрити джерело: {args.source}")

    source_fps = cap.get(cv2.CAP_PROP_FPS)
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

    detector = None
    torch = None

    if args.mode == 'track':
        from ultralytics import YOLO
        import torch as torch_module

        torch = torch_module

        if args.device.startswith('cuda') and not torch.cuda.is_available():
            raise RuntimeError(
                'CUDA недоступна; перевірте torch та драйвер NVIDIA'
            )

        detector = YOLO(args.weights)
        detector.to(args.device)

    process = None
    try:
        import psutil
        process = psutil.Process(os.getpid())
    except ImportError:
        pass

    t0 = time.perf_counter()
    last_sample = t0

    frames = 0
    failed_reads = 0
    detections = 0
    track_ids = set()
    inference_ms = []
    samples = []

    while time.perf_counter() - t0 < args.seconds:
        ok, frame = cap.read()

        if not ok:
            failed_reads += 1

            if (
                isinstance(source_value(args.source), int)
                or args.source.startswith(
                    ('rtsp://', 'http://', 'https://')
                )
            ):
                time.sleep(0.05)
                continue

            break  # EOF on video file

        frames += 1

        if detector is not None:
            t_inf = time.perf_counter()

            results = detector.track(
                frame,
                persist=True,
                tracker='bytetrack.yaml',
                conf=0.5,
                imgsz=640,
                vid_stride=2,
                verbose=False,
                device=args.device
            )

            if torch is not None and args.device.startswith('cuda'):
                torch.cuda.synchronize()

            inference_ms.append(
                (time.perf_counter() - t_inf) * 1000
            )

            for r in results:
                if r.boxes is not None:
                    for b in r.boxes:
                        name = r.names[int(b.cls[0])]

                        if name in (
                            'person', 'car', 'truck', 'bus'
                        ):
                            detections += 1

                            if b.id is not None:
                                track_ids.add(
                                    (name, int(b.id[0]))
                                )

        now = time.perf_counter()

        if now - last_sample >= 1:
            rss_mb = (
                round(
                    process.memory_info().rss / 1048576, 2
                )
                if process else None
            )

            gpu_mb = (
                round(
                    torch.cuda.memory_allocated() / 1048576,
                    2
                )
                if torch and args.device.startswith('cuda')
                else None
            )

            samples.append({
                'run': run_number,
                'elapsed_s': round(now - t0, 2),
                'frames': frames,
                'rss_mb': rss_mb,
                'torch_gpu_allocated_mb': gpu_mb
            })

            last_sample = now

    elapsed = time.perf_counter() - t0
    cap.release()

    return {
        'run': run_number,
        'mode': args.mode,
        'source': args.source,
        'device': args.device if detector else 'none',
        'duration_s': round(elapsed, 3),
        'source_reported_fps': round(source_fps, 2),
        'width': int(width),
        'height': int(height),
        'frames_read': frames,
        'failed_reads': failed_reads,
        'capture_or_pipeline_fps': round(
            frames / elapsed, 2
        ),
        'mean_track_call_ms': (
            round(statistics.mean(inference_ms), 2)
            if inference_ms else None
        ),
        'median_track_call_ms': (
            round(statistics.median(inference_ms), 2)
            if inference_ms else None
        ),
        'detections_total': detections,
        'distinct_track_ids_observed': len(track_ids),
        'rss_start_mb': (
            samples[0]['rss_mb'] if samples else None
        ),
        'rss_end_mb': (
            samples[-1]['rss_mb'] if samples else None
        )
    }, samples


def save_csv(path, rows):
    if not rows:
        return

    with open(
        path, 'w', newline='', encoding='utf-8-sig'
    ) as f:
        w = csv.DictWriter(
            f, fieldnames=list(rows[0])
        )
        w.writeheader()
        w.writerows(rows)


def main():
    p = argparse.ArgumentParser(
        description='NVR camera and YOLO ByteTrack benchmark'
    )

    p.add_argument(
        '--source',
        required=True,
        help='0, RTSP URL or video file path'
    )
    p.add_argument(
        '--mode',
        choices=['capture', 'track'],
        default='capture'
    )
    p.add_argument(
        '--seconds',
        type=int,
        default=60
    )
    p.add_argument(
        '--runs',
        type=int,
        default=3
    )
    p.add_argument(
        '--device',
        default='cpu',
        help='cpu or cuda:0'
    )
    p.add_argument(
        '--weights',
        default='yolo11n.pt'
    )
    p.add_argument(
        '--output',
        default='benchmark_results'
    )

    args = p.parse_args()

    if args.seconds <= 0 or args.runs <= 0:
        p.error(
            '--seconds and --runs must be positive'
        )

    output = Path(args.output)
    output.mkdir(
        parents=True, exist_ok=True
    )

    summary = []
    all_samples = []

    for i in range(1, args.runs + 1):
        print(
            f'Запуск {i}/{args.runs}, '
            f'режим {args.mode}, '
            f'{args.seconds} с',
            flush=True
        )

        item, samples = run(args, i)

        summary.append(item)
        all_samples.extend(samples)

        print(
            json.dumps(
                item,
                ensure_ascii=False,
                indent=2
            ),
            flush=True
        )

    save_csv(
        output / 'summary.csv',
        summary
    )

    save_csv(
        output / 'memory_samples.csv',
        all_samples
    )

    with open(
        output / 'environment.json',
        'w',
        encoding='utf-8'
    ) as f:
        json.dump(
            {
                'timestamp': (
                    dt.datetime.now()
                    .astimezone()
                    .isoformat()
                ),
                'python': platform.python_version(),
                'opencv': cv2.__version__,
                'platform': platform.platform(),
                'arguments': vars(args)
            },
            f,
            ensure_ascii=False,
            indent=2
        )

    print(
        f'Результати: {output.resolve()}'
    )


if __name__ == '__main__':
    main()
