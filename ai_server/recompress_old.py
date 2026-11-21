"""Разове пережаття ВЖЕ записаних сегментів.

Черга транскоду живе в пам'яті Recorder — файли, записані
до встановлення ffmpeg, самі не пережмуться. Цей скрипт
проходить по videos/ і стискає все що знайде.

Використання:
    python ai_server/recompress_old.py
    python ai_server/recompress_old.py --dry-run   # тільки показати
    python ai_server/recompress_old.py --crf 26    # якісніше
    python ai_server/recompress_old.py --delete-big # видалити .faststart залишки

Працює БЕЗ Laravel: просто викликає той самий ffmpeg-прохід,
що й Recorder.ensure_browser_compatible().
"""

import argparse
import os
import shutil
import subprocess
import sys


def _parse_args():
    parser = argparse.ArgumentParser(
        description="Пережаття старих MP4-сегментів у H.264 CRF."
    )

    parser.add_argument(
        "--root",
        default=None,
        help="Корінь пошуку videos/ (default: storage/app/public).",
    )

    parser.add_argument(
        "--crf",
        default="28",
        help="CRF libx264 (менше = якісніше/більше, default 28).",
    )

    parser.add_argument(
        "--preset",
        default="veryfast",
        help="Preset libx264 (default veryfast).",
    )

    parser.add_argument(
        "--max-w",
        default="1280",
        help="Макс. ширина (default 1280).",
    )

    parser.add_argument(
        "--max-h",
        default="720",
        help="Макс. висота (default 720).",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Тільки показати файли, нічого не чіпати.",
    )

    parser.add_argument(
        "--delete-big",
        action="store_true",
        help="Видалити залишки *.faststart.mp4 перед стартом.",
    )

    return parser.parse_args()


def _find_videos_dirs(root_arg):
    here = os.path.abspath(os.path.dirname(__file__))

    candidates = []

    if root_arg:
        candidates.append(os.path.abspath(root_arg))

    candidates.append(
        os.path.abspath(
            os.path.join(here, "..", "storage", "app", "public")
        )
    )

    found = []

    for base in candidates:
        if not base or not os.path.isdir(base):
            continue

        for sub in ("videos",):
            path = os.path.join(base, sub)

            if os.path.isdir(path) and path not in found:
                found.append(path)

    return found


def _iter_mp4(dirs):
    for top in dirs:
        for root, _names, files in os.walk(top):
            for name in sorted(files):
                low = name.lower()

                if not low.endswith(".mp4"):
                    continue

                if low.endswith(".faststart.mp4"):
                    continue

                if low.endswith(".tmp.mp4"):
                    continue

                yield os.path.join(root, name)


def _cleanup_leftovers(dirs):
    removed = 0

    for top in dirs:
        for root, _names, files in os.walk(top):
            for name in files:
                low = name.lower()

                if low.endswith(".faststart.mp4"):
                    path = os.path.join(root, name)

                    try:
                        os.remove(path)
                        removed += 1
                    except OSError:
                        pass

    return removed


def _transcode_one(path, crf, preset, max_w, max_h):
    try:
        size_before = os.path.getsize(path)
    except OSError:
        return ("skip", 0, 0)

    if size_before <= 0:
        return ("skip", size_before, 0)

    tmp_path = path + ".faststart.mp4"

    try:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
    except OSError:
        pass

    vf_scale = (
        f"scale={max_w}:{max_h}:"
        f"force_original_aspect_ratio=decrease,"
        f"scale=trunc(iw/2)*2:trunc(ih/2)*2"
    )

    cmd = [
        "ffmpeg",
        "-y",
        "-i", path,
        "-c:v", "libx264",
        "-preset", preset,
        "-crf", crf,
        "-pix_fmt", "yuv420p",
        "-vf", vf_scale,
        "-an",
        "-movflags", "+faststart",
        tmp_path,
    ]

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=600,
        )
    except Exception as e:
        print(f"  ПОМИЛКА запуску: {e}")
        return ("fail", size_before, 0)

    if result.returncode != 0 or not os.path.exists(tmp_path):
        try:
            err = result.stderr.decode("utf-8", "ignore")[-800:]
        except Exception:
            err = "?"

        print(f"  ffmpeg код {result.returncode}: {err}")

        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except OSError:
            pass

        return ("fail", size_before, 0)

    try:
        size_after = os.path.getsize(tmp_path)

        if size_after <= 0:
            os.remove(tmp_path)
            return ("fail", size_before, 0)
    except OSError:
        return ("fail", size_before, 0)

    if size_after >= size_before:
        try:
            os.remove(tmp_path)
        except OSError:
            pass

        return ("same", size_before, size_after)

    try:
        os.replace(tmp_path, path)
    except OSError as e:
        print(f"  Не вдалося замінити: {e}")

        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except OSError:
            pass

        return ("fail", size_before, size_after)

    return ("ok", size_before, size_after)


def main():
    args = _parse_args()

    if shutil.which("ffmpeg") is None:
        print(
            "ffmpeg НЕ знайдено в PATH. Встановіть: "
            "winget install Gyan.FFmpeg — і перезапустіть термінал."
        )
        return 1

    dirs = _find_videos_dirs(args.root)

    if not dirs:
        print(
            "Не знайдено папку videos/. Вкажіть --root "
            "(напр. storage/app/public)."
        )
        return 1

    print(f"Шукаю MP4 у: {', '.join(dirs)}")

    if args.delete_big:
        removed = _cleanup_leftovers(dirs)
        print(f"Видалено залишків .faststart: {removed}")

    files = list(_iter_mp4(dirs))

    print(f"Файлів: {len(files)}")

    if args.dry_run:
        for path in files[:50]:
            try:
                size = os.path.getsize(path)
            except OSError:
                size = -1

            print(f"  {path} ({size} байт)")

        if len(files) > 50:
            print(f"  ... і ще {len(files) - 50}")

        return 0

    ok = same = fail = skip = 0
    saved = 0

    for i, path in enumerate(files, 1):
        print(f"[{i}/{len(files)}] {path}")

        status, before, after = _transcode_one(
            path,
            str(args.crf),
            str(args.preset),
            str(args.max_w),
            str(args.max_h),
        )

        if status == "ok":
            ok += 1
            saved += max(0, before - after)
            pct = 100 - int(after * 100 / max(1, before))
            print(f"  OK: {before} -> {after} (-{pct}%)")
        elif status == "same":
            same += 1
            print(f"  БЕЗ ЗМІН (пережатий більший): {before}")
        elif status == "skip":
            skip += 1
        else:
            fail += 1

    print(
        f"Готово: стиснуто={ok}, без змін={same}, "
        f"пропущено={skip}, помилок={fail}, "
        f"зекономлено={saved} байт"
    )

    return 0 if fail == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
