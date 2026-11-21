<?php

namespace App\Http\Controllers;

use App\Models\Camera;
use App\Models\Event;
use App\Models\Video;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\File;

class ArchiveController extends Controller
{
    /**
     * Сторінка відеоархіву: фільтри + dayline-віджет + плеєр.
     */
    public function index(Request $request)
    {
        $cameras = Camera::orderBy('name')->get();

        $cameraId = $request->get('camera_id');

        $date = $request->get('date', now()->format('Y-m-d'));

        return view(
            'archive.index',
            compact('cameras', 'cameraId', 'date')
        );
    }

    /**
     * Дані дня (відео + події) для dayline-віджета.
     * Викликається JS-ом сторінки архіву.
     */
    public function data(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'camera_id' => [
                'nullable',
                'integer',
                'exists:cameras,id',
            ],

            'date' => [
                'required',
                'date_format:Y-m-d',
            ],
        ]);

        $videosQuery = Video::query()
            ->whereDate('recording_date', $validated['date'])
            ->where('status', 'finished')
            ->orderBy('started_at');

        $eventsQuery = Event::query()
            ->whereDate('detected_at', $validated['date'])
            ->orderBy('detected_at');

        if (!empty($validated['camera_id'])) {
            $videosQuery->where('camera_id', $validated['camera_id']);
            $eventsQuery->where('camera_id', $validated['camera_id']);
        }

        /*
        |----------------------------------------------------------------------
        | Відео
        |----------------------------------------------------------------------
        */

        $videoData = [];

        foreach ($videosQuery->get() as $video) {

            $start = $video->started_at;
            $end = $video->ended_at;
            $duration = $video->duration;

            // Самоперевірка: якщо в БД лежить "5 хв часом стіни",
            // а started_at/ended_at дають менше — довіряємо часу.
            if ($start && $end) {
                $timeDiff = (int) $start->diffInSeconds($end);

                if ($timeDiff < 0) {
                    $timeDiff = 0;
                }

                if ($duration === null || abs((int) $duration - $timeDiff) > 10) {
                    $duration = $timeDiff;
                }
            }

            if ($duration === null) {
                $duration = 0;
            }

            $videoData[] = [
                'id' => $video->id,
                'camera_id' => $video->camera_id,
                'camera_name' => $video->camera_name,
                'filename' => $video->filename,
                'path' => $video->path,
                'recording_date' => $video->recording_date?->format('Y-m-d'),
                'started_at' => $start?->format('Y-m-d H:i:s'),
                'ended_at' => $end?->format('Y-m-d H:i:s'),
                'duration' => (int) $duration,
                'size' => (int) ($video->size ?? 0),
                'size_mb' => round(((int) ($video->size ?? 0)) / 1024 / 1024, 2),
                'url' => route('archive.video', ['video' => $video->id]),
                // Кадр-превʼю: перший кадр відео (#t=0.5).
                // Браузер підвантажить лише метадані + 1 кадр
                // завдяки preload="metadata" в archive.js.
                'thumb_url' => route('archive.video', ['video' => $video->id]).'#t=0.5',
            ];
        }

        /*
        |----------------------------------------------------------------------
        | Події
        |----------------------------------------------------------------------
        */

        $eventData = [];

        foreach ($eventsQuery->get() as $event) {

            $eventData[] = [
                'id' => $event->id,
                'camera_id' => $event->camera_id,
                'camera_name' => $event->camera_name,
                'object' => $event->object,
                'object_icon' => \App\Support\ObjectIcon::icon($event->object),
                'object_label' => \App\Support\ObjectIcon::label($event->object),
                'object_badge' => \App\Support\ObjectIcon::badge($event->object),
                'confidence' => (float) $event->confidence,
                'track_id' => $event->track_id,
                'detected_at' => $event->detected_at?->format('Y-m-d H:i:s'),
                'image' => $event->image,
                'image_url' => $event->image_url,
            ];
        }

        return response()->json([
            'success' => true,
            'date' => $validated['date'],
            'videos' => $videoData,
            'events' => $eventData,
        ]);
    }

    /*
    |--------------------------------------------------------------------------
    | Віддача відеофайлу з ai_server (підтримка Range → 206 Partial Content)
    |--------------------------------------------------------------------------
    */

    public function video(Request $request, Video $video)
    {
        /* Шлях до Python AI Server */
        $basePath = base_path('ai_server');

        /* Нормалізуємо path */
        $relativePath = str_replace(
            ['/', '\\'],
            DIRECTORY_SEPARATOR,
            $video->path
        );

        $relativePath = ltrim(
            $relativePath,
            DIRECTORY_SEPARATOR
        );

        $fullPath = realpath(
            $basePath . DIRECTORY_SEPARATOR . $relativePath
        );

        if ($fullPath === false || !File::exists($fullPath)) {
            abort(404, 'Відеофайл не знайдено на диску. Можливо, запис ще триває.');
        }

        $ext = strtolower(pathinfo($fullPath, PATHINFO_EXTENSION));

        if ($ext !== 'mp4') {
            abort(415, 'Непідтримуваний формат відео');
        }

        /* Безпека: файл повинен бути всередині ai_server */
        $realBasePath = realpath($basePath);

        if (
            $realBasePath === false
            || !str_starts_with(
                strtolower($fullPath),
                strtolower($realBasePath . DIRECTORY_SEPARATOR)
            )
        ) {
            abort(403, 'Доступ заборонено');
        }

        $size = filesize($fullPath);

        if ($size === false || $size <= 0) {
            abort(404, 'Файл порожній — запис іще триває. Спробуйте пізніше.');
        }

        $lastModified = filemtime($fullPath) ?: time();
        $etag = '"' . md5($fullPath . '|' . $size . '|' . $lastModified) . '"';

        if (trim((string) $request->header('If-None-Match')) === $etag) {
            return response('', 304, [
                'ETag' => $etag,
                'Cache-Control' => 'private, max-age=60',
            ]);
        }

        $isHead = strtoupper($request->method()) === 'HEAD';

        /* ---------- Розбір Range-запиту ---------- */
        $start = 0;
        $end = $size - 1;
        $range = $request->header('Range');

        $headers = [
            'Content-Type' => 'video/mp4',
            'Accept-Ranges' => 'bytes',
            'Content-Disposition' =>
                'inline; filename="' . basename($fullPath) . '"',
            'ETag' => $etag,
            'Last-Modified' => gmdate('D, d M Y H:i:s', $lastModified) . ' GMT',
            'Cache-Control' => 'private, max-age=60',
            'X-Content-Type-Options' => 'nosniff',
        ];

        if ($range !== null && $range !== '') {
            if (preg_match('/bytes=(\d*)-(\d*)/', $range, $m)) {
                $rangeStart = $m[1] !== '' ? (int) $m[1] : null;
                $rangeEnd = $m[2] !== '' ? (int) $m[2] : null;

                if ($rangeStart === null) {
                    /* "bytes=-N" — останні N байт */
                    $suffix = $rangeEnd ?: 0;
                    $start = max(0, $size - $suffix);
                    $end = $size - 1;
                } else {
                    $start = min($rangeStart, $size - 1);
                    $end = ($rangeEnd === null || $rangeEnd >= $size)
                        ? $size - 1
                        : $rangeEnd;
                }

                if ($start > $end || $start >= $size) {
                    return response('', 416, [
                        'Content-Range' => "bytes */$size",
                        'Accept-Ranges' => 'bytes',
                    ]);
                }

                $headers['Content-Length'] = (string) ($end - $start + 1);
                $headers['Content-Range'] = "bytes $start-$end/$size";

                $status = 206;
            } else {
                $headers['Content-Length'] = (string) $size;
                $status = 200;
            }
        } else {
            $headers['Content-Length'] = (string) $size;
            $status = 200;
        }

        if ($isHead) {
            return response('', $status, $headers);
        }

        while (ob_get_level() > 0) {
            ob_end_clean();
        }

        set_time_limit(0);

        /* ---------- Потокове віддавання ---------- */
        return response()->stream(function () use ($fullPath, $start, $end) {
            $fp = fopen($fullPath, 'rb');

            if ($fp === false) {
                return;
            }

            if ($start > 0) {
                fseek($fp, $start);
            }

            $chunk = 512 * 1024;
            $pos = $start;

            while ($pos <= $end && !feof($fp)) {
                $toRead = min($chunk, $end - $pos + 1);
                $data = fread($fp, $toRead);

                if ($data === false || $data === '') {
                    break;
                }

                echo $data;
                $pos += strlen($data);

                if (ob_get_level() > 0) {
                    ob_flush();
                }
                flush();

                if (connection_aborted()) {
                    break;
                }
            }

            fclose($fp);
        }, $status, $headers);
    }

    /*
    |--------------------------------------------------------------------------
    | Віддача фото події з ai_server
    |--------------------------------------------------------------------------
    */

    public function image(Event $event)
    {
        if (
            empty($event->image)
        ) {
            abort(
                404,
                'Зображення не знайдено'
            );
        }

        $basePath = base_path('ai_server');

        $relativePath = str_replace(
            ['/', '\\'],
            DIRECTORY_SEPARATOR,
            ltrim($event->image, '/\\')
        );

        $relativePath = ltrim(
            $relativePath,
            DIRECTORY_SEPARATOR
        );

        $fullPath = realpath(
            $basePath
            . DIRECTORY_SEPARATOR
            . $relativePath
        );

        if (
            $fullPath === false
            ||
            !File::exists($fullPath)
        ) {
            abort(
                404,
                'Зображення не знайдено'
            );
        }

        $realBasePath = realpath(
            $basePath
        );

        if (
            $realBasePath === false
            ||
            !str_starts_with(
                strtolower($fullPath),
                strtolower(
                    $realBasePath
                    . DIRECTORY_SEPARATOR
                )
            )
        ) {
            abort(
                403,
                'Доступ заборонено'
            );
        }

        return response()->file(
            $fullPath,
            [
                'Content-Type' => 'image/jpeg',
            ]
        );
    }
}