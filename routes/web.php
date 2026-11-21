<?php

use App\Http\Controllers\ProfileController;
use Illuminate\Support\Facades\Route;
use App\Http\Controllers\DashboardController;
use App\Http\Controllers\CameraController;
use App\Http\Controllers\EventJournalController;
use App\Http\Controllers\ArchiveController;
use App\Http\Controllers\MonitoringController;
use App\Http\Controllers\SettingsController;
use App\Http\Controllers\UserAdminController;

Route::middleware(['auth', 'verified'])->group(function () {

    Route::get('/', [DashboardController::class, 'index'])
        ->middleware('section:dashboard')
        ->name('dashboard');

    Route::resource('cameras', CameraController::class)
        ->except(['show'])
        ->middleware('section:cameras');

    Route::get('/profile', [ProfileController::class, 'edit'])
        ->name('profile.edit');

    Route::patch('/profile', [ProfileController::class, 'update'])
        ->name('profile.update');

    Route::delete('/profile', [ProfileController::class, 'destroy'])
        ->name('profile.destroy');

    Route::get(
        '/monitoring',
        [MonitoringController::class, 'index']
    )->middleware('section:monitoring')->name('monitoring.index');

    Route::get(
        '/monitoring/data',
        [MonitoringController::class, 'data']
    )->middleware('section:monitoring')->name('monitoring.data');

    Route::get(
        '/events',
        [EventJournalController::class, 'index']
    )->middleware('section:events')->name('events.index');

    Route::get(
        '/archive',
        [ArchiveController::class, 'index']
    )->middleware('section:archive')->name('archive.index');

    Route::get(
        '/archive/data',
        [ArchiveController::class, 'data']
    )->middleware('section:archive')->name('archive.data');

    Route::get(
        '/archive/video/{video}',
        [ArchiveController::class, 'video']
    )->middleware('section:archive')->whereNumber('video')->name('archive.video');

    Route::get(
        '/archive/event-image/{event}',
        [ArchiveController::class, 'image']
    )->middleware('section:archive')->whereNumber('event')->name('archive.image');

    Route::middleware(['panel.admin'])->group(function () {
        Route::get('/settings', [SettingsController::class, 'index'])
            ->name('settings.index');

        Route::put('/settings/panel', [SettingsController::class, 'updatePanel'])
            ->name('settings.panel.update');

        Route::post('/settings/users', [UserAdminController::class, 'store'])
            ->name('settings.users.store');

        Route::put('/settings/users/{user}', [UserAdminController::class, 'update'])
            ->name('settings.users.update');

        Route::put('/settings/users/{user}/password', [UserAdminController::class, 'password'])
            ->name('settings.users.password');

        Route::delete('/settings/users/{user}', [UserAdminController::class, 'destroy'])
            ->name('settings.users.destroy');
    });
    });

require __DIR__.'/auth.php';



