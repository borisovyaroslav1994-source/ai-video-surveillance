<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Video;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Storage;


class VideoApiController extends Controller
{
    /**
     * ========================================================
     * СПИСОК ВІДЕО
     *
     * GET /api/videos
     *
     * Фільтри:
     *
     * /api/videos?camera_id=10
     * /api/videos?date=2026-09-06
     * /api/videos?status=finished
     * ========================================================
     */
    public function index(Request $request)
    {
        $query = Video::query()
            ->orderByDesc('started_at');

        // ----------------------------------------------------
        // Фільтр по камері
        // ----------------------------------------------------

        if ($request->filled('camera_id')) {
            $query->where(
                'camera_id',
                $request->camera_id
            );
        }

        // ----------------------------------------------------
        // Фільтр по даті
        // ----------------------------------------------------

        if ($request->filled('date')) {
            $query->whereDate(
                'recording_date',
                $request->date
            );
        }

        // ----------------------------------------------------
        // Фільтр по статусу
        // ----------------------------------------------------

        if ($request->filled('status')) {
            $query->where(
                'status',
                $request->status
            );
        }

        // ----------------------------------------------------
        // Кількість
        // ----------------------------------------------------

        $perPage = min(
            max(
                (int) $request->get('per_page', 50),
                1
            ),
            200
        );

        $videos = $query
            ->paginate($perPage);

        return response()->json(
            $videos
        );
    }


    /**
     * ========================================================
     * ОТРИМАННЯ ОДНОГО ВІДЕО
     *
     * GET /api/videos/{video}
     * ========================================================
     */
    public function show(Video $video)
    {
        return response()->json([
            'success' => true,
            'video' => $video,
        ]);
    }


    /**
     * ========================================================
     * СТВОРЕННЯ ЗАПИСУ
     *
     * POST /api/videos
     *
     * Викликається Python Recorder після створення MP4.
     * ========================================================
     */
    public function store(Request $request)
    {
        $validated = $request->validate([
            'camera_id' => [
                'nullable',
                'integer',
                'exists:cameras,id',
            ],

            'camera_name' => [
                'nullable',
                'string',
                'max:255',
            ],

            'filename' => [
                'required',
                'string',
                'max:255',
            ],

            'path' => [
                'required',
                'string',
                'max:1000',
            ],

            'recording_date' => [
                'required',
                'date',
            ],

            'started_at' => [
                'nullable',
                'date',
            ],

            'status' => [
                'nullable',
                'in:recording,finished,error',
            ],
        ]);

        if (!isset($validated['status'])) {
            $validated['status'] = 'recording';
        }

        $video = Video::create(
            $validated
        );

        return response()->json([
            'success' => true,
            'video' => $video,
        ], 201);
    }


    /**
     * ========================================================
     * ЗАВЕРШЕННЯ ЗАПИСУ
     *
     * POST /api/videos/{video}/finish
     *
     * Python викликає цей метод після закриття MP4.
     * ========================================================
     */
    public function finish(
        Request $request,
        Video $video
    ) {
        $validated = $request->validate([
            'ended_at' => [
                'nullable',
                'date',
            ],

            'duration' => [
                'nullable',
                'integer',
                'min:0',
            ],

            'size' => [
                'nullable',
                'integer',
                'min:0',
            ],
        ]);

        // ----------------------------------------------------
        // Оновлення ТІЛЬКИ розміру (фонове стиснення Python).
        // _update_video_size() шле {"size": N} без ended_at —
        // це НЕ завершення, тривалість/статус не чіпаємо,
        // інакше ended_at=now() надує duration до годин.
        // ----------------------------------------------------

        $isSizeOnly = (
            $request->has('size')
            &&
            !$request->has('ended_at')
            &&
            !$request->has('duration')
        );

        if ($isSizeOnly) {
            $video->update([
                'size' => (int) $request->input('size', $video->size ?? 0),
            ]);

            return response()->json([
                'success' => true,
                'video' => $video->fresh(),
            ]);
        }

        // ----------------------------------------------------
        // Якщо ended_at не переданий —
        // використовуємо поточний час.
        // ----------------------------------------------------

        if (
            !isset(
                $validated['ended_at']
            )
        ) {
            $validated['ended_at'] = now();
        }

        // ----------------------------------------------------
        // Самоперевірка: duration звіряємо зі started_at/ended_at.
        // Python раніше рахував duration часом стіни, поки YOLO
        // гальмував цикл — тому в БД лежали "5 хв" для файлів
        // з 1-2 хв реального відео. Тепер довіряємо різниці часу.
        // ----------------------------------------------------

        $endedAt = \Carbon\Carbon::parse($validated['ended_at']);
        $startedAt = $video->started_at;

        if ($startedAt) {
            $realDuration = (int) $startedAt->diffInSeconds($endedAt);

            if ($realDuration < 0) {
                $realDuration = 0;
            }

            $given = isset($validated['duration'])
                ? (int) $validated['duration']
                : $realDuration;

            // Якщо розбіжність > 10 сек — беремо часовий diff.
            if (abs($given - $realDuration) > 10) {
                $validated['duration'] = $realDuration;
            } else {
                $validated['duration'] = $given;
            }
        }

        $validated['status'] = 'finished';

        $video->update(
            $validated
        );

        return response()->json([
            'success' => true,
            'video' => $video->fresh(),
        ]);
    }


    /**
     * ========================================================
     * ВИДАЛЕННЯ ВІДЕО
     *
     * DELETE /api/videos/{video}
     *
     * Видаляє:
     * 1. запис з БД
     * 2. файл MP4
     * ========================================================
     */
    public function destroy(Video $video)
    {
        // ----------------------------------------------------
        // Видаляємо файл
        // ----------------------------------------------------

        if (
            $video->path
            &&
            Storage::disk('public')->exists(
                $video->path
            )
        ) {
            Storage::disk('public')->delete(
                $video->path
            );
        }

        // ----------------------------------------------------
        // Видаляємо запис
        // ----------------------------------------------------

        $video->delete();

        return response()->json([
            'success' => true,
            'message' => 'Відео видалено',
        ]);
    }
}
