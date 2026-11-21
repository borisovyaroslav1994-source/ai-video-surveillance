<?php

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\Api\CameraApiController;
use App\Http\Controllers\Api\SettingsApiController;
use App\Http\Controllers\EventController;
use App\Http\Controllers\Api\VideoApiController;

Route::get('/cameras', [CameraApiController::class, 'index']);

Route::get('/recorder-settings', [SettingsApiController::class, 'recorder']);

Route::get('/cameras/{camera}', [CameraApiController::class, 'show']);

Route::post('/cameras/{camera}/status', [CameraApiController::class, 'updateStatus']);

Route::get('/events', [EventController::class, 'index']);

Route::post('/events', [EventController::class, 'store']);

Route::get('/events/{event}', [EventController::class, 'show']);

Route::post('/events/{event}/close', [EventController::class, 'close']);

Route::delete('/events/{event}', [EventController::class, 'destroy']);


Route::get(
    '/videos',
    [VideoApiController::class, 'index']
);

Route::get(
    '/videos/{video}',
    [VideoApiController::class, 'show']
);

Route::post(
    '/videos',
    [VideoApiController::class, 'store']
);

Route::post(
    '/videos/{video}/finish',
    [VideoApiController::class, 'finish']
);

Route::delete(
    '/videos/{video}',
    [VideoApiController::class, 'destroy']
);

