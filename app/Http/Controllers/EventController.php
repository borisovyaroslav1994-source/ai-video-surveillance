<?php

namespace App\Http\Controllers;

use App\Models\Event;
use App\Models\Camera;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class EventController extends Controller
{
    /**
     * Отримати список подій.
     */
    public function index(Request $request): JsonResponse
    {
        $query = Event::with('camera')
            ->orderByDesc('detected_at')
            ->orderByDesc('id');

        if ($request->filled('camera_id')) {
            $query->where('camera_id', $request->camera_id);
        }

        if ($request->filled('object')) {
            $query->where('object', $request->object);
        }

        if ($request->filled('status')) {
            $query->where('status', $request->status);
        }

        $events = $query
            ->paginate($request->get('per_page', 50));

        return response()->json([
            'success' => true,
            'events' => $events,
        ]);
    }

    /**
     * Створити нову подію від Python AI сервера.
     */
    public function store(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'camera_id' => [
                'required',
                'integer',
                'exists:cameras,id',
            ],

            'camera_name' => [
                'nullable',
                'string',
                'max:255',
            ],

            'object' => [
                'required',
                'string',
                'max:100',
            ],

            'track_id' => [
                'nullable',
                'integer',
            ],

            'confidence' => [
                'required',
                'numeric',
                'between:0,1',
            ],

            'bbox_x1' => [
                'nullable',
                'integer',
            ],

            'bbox_y1' => [
                'nullable',
                'integer',
            ],

            'bbox_x2' => [
                'nullable',
                'integer',
            ],

            'bbox_y2' => [
                'nullable',
                'integer',
            ],

            'image' => [
                'nullable',
                'string',
                'max:500',
            ],

            'status' => [
                'nullable',
                'string',
                'max:50',
            ],

            'detected_at' => [
                'nullable',
                'date',
            ],

            'ended_at' => [
                'nullable',
                'date',
            ],
        ]);

        $camera = Camera::find($validated['camera_id']);

        $event = Event::create([
            'camera_id' => $camera->id,

            'camera_name' =>
                $validated['camera_name']
                ?? $camera->name,

            'object' => $validated['object'],

            'track_id' =>
                $validated['track_id']
                ?? null,

            'confidence' =>
                $validated['confidence'],

            'bbox_x1' =>
                $validated['bbox_x1']
                ?? null,

            'bbox_y1' =>
                $validated['bbox_y1']
                ?? null,

            'bbox_x2' =>
                $validated['bbox_x2']
                ?? null,

            'bbox_y2' =>
                $validated['bbox_y2']
                ?? null,

            'image' =>
                $validated['image']
                ?? null,

            'status' =>
                $validated['status']
                ?? 'active',

            'detected_at' =>
                $validated['detected_at']
                ?? now(),

            'ended_at' =>
                $validated['ended_at']
                ?? null,
        ]);

        return response()->json([
            'success' => true,
            'message' => 'Подію успішно збережено',
            'event' => $event,
        ], 201);
    }

    /**
     * Отримати одну подію.
     */
    public function show(Event $event): JsonResponse
    {
        $event->load('camera');

        return response()->json([
            'success' => true,
            'event' => $event,
        ]);
    }

    /**
     * Завершити подію.
     */
    public function close(Event $event): JsonResponse
    {
        $event->update([
            'status' => 'completed',
            'ended_at' => now(),
        ]);

        return response()->json([
            'success' => true,
            'message' => 'Подію завершено',
            'event' => $event,
        ]);
    }

    /**
     * Видалити подію.
     */
    public function destroy(Event $event): JsonResponse
    {
        $event->delete();

        return response()->json([
            'success' => true,
            'message' => 'Подію видалено',
        ]);
    }
}