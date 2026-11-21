<?php

namespace App\Http\Controllers;

use App\Models\Camera;
use App\Models\Event;
use Illuminate\Http\JsonResponse;
use Illuminate\View\View;

class MonitoringController extends Controller
{
    /**
     * Сторінка онлайн-моніторингу.
     */
    public function index(): View
    {
        $cameras = Camera::orderBy('name')->get();

        $recentEvents = Event::query()
            ->orderByDesc('detected_at')
            ->orderByDesc('id')
            ->limit(8)
            ->get();

        return view('monitoring.index', [
            'cameras'        => $cameras,
            'recentEvents'   => $recentEvents,
            'onlineCameras'  => Camera::where('status', 'online')->count(),
            'activeEvents'   => Event::where('status', 'active')->count(),
            'eventsToday'    => Event::whereDate('detected_at', today())->count(),
            'newestEventId'  => (int) Event::max('id'),
        ]);
    }

    /**
     * JSON-стан для опитування з JS (кожні ~10 секунд).
     */
    public function data(): JsonResponse
    {
        $cameras = Camera::query()
            ->orderBy('name')
            ->get([
                'id',
                'name',
                'status',
                'type',
                'source',
                'location',
                'ai_enabled',
                'recording_enabled',
            ]);

        $events = Event::query()
            ->orderByDesc('detected_at')
            ->orderByDesc('id')
            ->limit(8)
            ->get();

        return response()->json([
            'success'        => true,
            'server_time'    => now()->format('H:i:s'),
            'online_cameras' => Camera::where('status', 'online')->count(),
            'total_cameras'  => Camera::count(),
            'active_events'  => Event::where('status', 'active')->count(),
            'events_today'   => Event::whereDate('detected_at', today())->count(),
            'newest_event_id'=> (int) Event::max('id'),
            'cameras'        => $cameras,
            'events'         => $events->map(function ($event) {
                return [
                    'id'          => $event->id,
                    'object'      => $event->object,
                    'object_icon' => \App\Support\ObjectIcon::icon($event->object),
                    'object_label' => \App\Support\ObjectIcon::label($event->object),
                    'object_badge' => \App\Support\ObjectIcon::badge($event->object),
                    'camera_name' => $event->camera_name
                        ?? ('Камера #' . $event->camera_id),
                    'confidence'  => (float) $event->confidence,
                    'status'      => $event->status,
                    'time'        => $event->detected_at?->format('H:i:s'),
                    'date'        => $event->detected_at?->format('d.m'),
                    'image_url'   => $event->image_url,
                ];
            }),
        ]);
    }
}
