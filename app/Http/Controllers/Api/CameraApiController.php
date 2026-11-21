<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Camera;
use Illuminate\Http\Request;

class CameraApiController extends Controller
{
    public function index()
    {
        $cameras = Camera::orderBy('id')->get();

        return response()->json([
            'success' => true,
            'count' => $cameras->count(),
            'cameras' => $cameras
        ]);
    }

    public function show(Camera $camera)
    {
        return response()->json([
            'success' => true,
            'camera' => $camera
        ]);
    }

    public function updateStatus(Request $request, Camera $camera)
    {
        $validated = $request->validate([
            'status' => 'required|in:online,offline,error',
        ]);

        $camera->status = $validated['status'];
        $camera->save();

        return response()->json([
            'success' => true,
            'camera' => $camera,
        ]);
    }
}