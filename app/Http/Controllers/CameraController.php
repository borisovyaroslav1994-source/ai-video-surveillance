<?php

namespace App\Http\Controllers;

use App\Models\Camera;
use App\Models\PanelSetting;
use Illuminate\Http\Request;

class CameraController extends Controller
{
    /**
     * Список камер
     */
    public function index()
    {
        $cameras = Camera::orderBy('id', 'desc')->get();

        return view('cameras.index', compact('cameras'));
    }

    /**
     * Форма додавання
     */
    public function create()
    {
        $defaultConfidence = 0.5;

        try {
            $defaultConfidence = max(
                0,
                min(
                    1,
                    (float) PanelSetting::getValue(
                        'default_confidence',
                        0.5
                    )
                )
            );
        } catch (\Throwable) {
            $defaultConfidence = 0.5;
        }

        return view('cameras.create', compact('defaultConfidence'));
    }

    /**
     * Збереження нової камери
     */
    public function store(Request $request)
    {
        $validated = $request->validate([
            'name' => 'required|string|max:255',
            'type' => 'required|in:usb,rtsp,http',
            'source' => 'required|string|max:1000',
            'location' => 'nullable|string|max:255',
            'confidence_threshold' => 'required|numeric|min:0|max:1',
        ]);

        $validated['enabled'] = $request->has('enabled');
        $validated['ai_enabled'] = $request->has('ai_enabled');
        $validated['recording_enabled'] = $request->has('recording_enabled');
        $validated['status'] = 'offline';

        Camera::create($validated);

        return redirect()
            ->route('cameras.index')
            ->with('success', 'Камеру успішно додано.');
    }

    /**
     * Форма редагування
     */
    public function edit(Camera $camera)
    {
        return view('cameras.edit', compact('camera'));
    }

    /**
     * Оновлення камери
     */
    public function update(Request $request, Camera $camera)
    {
        $validated = $request->validate([
            'name' => 'required|string|max:255',
            'type' => 'required|in:usb,rtsp,http',
            'source' => 'required|string|max:1000',
            'location' => 'nullable|string|max:255',
            'confidence_threshold' => 'required|numeric|min:0|max:1',
        ]);

        $validated['enabled'] = $request->has('enabled');
        $validated['ai_enabled'] = $request->has('ai_enabled');
        $validated['recording_enabled'] = $request->has('recording_enabled');

        $camera->update($validated);

        return redirect()
            ->route('cameras.index')
            ->with('success', 'Камеру успішно оновлено.');
    }

    /**
     * Видалення камери
     */
    public function destroy(Camera $camera)
    {
        $camera->delete();

        return redirect()
            ->route('cameras.index')
            ->with('success', 'Камеру видалено.');
    }
}