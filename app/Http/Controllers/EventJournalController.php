<?php

namespace App\Http\Controllers;

use App\Models\Camera;
use App\Models\Event;
use App\Models\PanelSetting;
use Illuminate\Http\Request;
use Illuminate\View\View;

class EventJournalController extends Controller
{
    /**
     * Журнал подій AI: фільтри + пагінація.
     */
    public function index(Request $request): View
    {
        $validated = $request->validate([
            'camera_id' => [
                'nullable',
                'integer',
                'exists:cameras,id',
            ],

            'object' => [
                'nullable',
                'string',
                'max:100',
            ],

            'status' => [
                'nullable',
                'in:active,completed',
            ],

            'date' => [
                'nullable',
                'date_format:Y-m-d',
            ],

            'per_page' => [
                'nullable',
                'integer',
                'min:6',
                'max:96',
            ],
        ]);

        $query = Event::query()
            ->with('camera')
            ->orderByDesc('detected_at')
            ->orderByDesc('id');

        if (!empty($validated['camera_id'])) {
            $query->where('camera_id', $validated['camera_id']);
        }

        if (!empty($validated['object'])) {
            $query->where('object', $validated['object']);
        }

        if (!empty($validated['status'])) {
            $query->where('status', $validated['status']);
        }

        if (!empty($validated['date'])) {
            $query->whereDate('detected_at', $validated['date']);
        }

        // Дефолт сторінки — з налаштувань «Загальне» (items_per_page_events),
        // у межах валідації per_page (6–96).
        $defaultPerPage = min(
            96,
            max(6, (int) PanelSetting::getValue('items_per_page_events', 24))
        );

        $events = $query
            ->paginate($validated['per_page'] ?? $defaultPerPage)
            ->withQueryString();

        $cameras = Camera::orderBy('name')->get();

        $objects = Event::query()
            ->select('object')
            ->distinct()
            ->orderBy('object')
            ->pluck('object');

        /*
        |----------------------------------------------------------------------
        | ID найновішої події — для live-перевірки нових записів
        |----------------------------------------------------------------------
        */

        $newestId = (int) Event::max('id');

        return view('events.index', [
            'events' => $events,
            'cameras' => $cameras,
            'objects' => $objects,
            'newestId' => $newestId,
        ]);
    }
}
