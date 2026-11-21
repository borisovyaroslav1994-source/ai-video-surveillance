<?php

namespace App\Http\Controllers;

use App\Models\Camera;
use App\Models\Event;
use App\Models\Video;

class DashboardController extends Controller
{
    /**
     * Головна сторінка: статистика системи + останні події.
     */
    public function index()
    {
        $stats = [
            'cameras_total'  => Camera::count(),
            'cameras_online' => Camera::where('status', 'online')->count(),
            'events_today'   => Event::whereDate('detected_at', today())->count(),
            'videos_today'   => Video::whereDate('recording_date', today())->count(),
        ];

        $storageBytes = (int) Video::sum('size');

        $recentEvents = Event::query()
            ->orderByDesc('detected_at')
            ->orderByDesc('id')
            ->limit(9)
            ->get();

        $cameras = Camera::orderBy('name')->get();

        return view('dashboard', [
            'stats'        => $stats,
            'storageBytes' => $storageBytes,
            'recentEvents' => $recentEvents,
            'cameras'      => $cameras,
        ]);
    }
}
