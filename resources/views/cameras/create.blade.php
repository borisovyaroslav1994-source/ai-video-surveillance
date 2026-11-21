@extends('layouts.panel')

@section('page_title', 'Додати камеру')

@section('content')

<div class="page-header">

    <div>
        <h2>Додати камеру</h2>
        <p>Нова камера з'явиться в Python AI-сервері після перезапуску.</p>
    </div>

    <div class="page-actions">
        <a href="{{ route('cameras.index') }}" class="btn btn-ghost">← До списку</a>
    </div>

</div>

<form method="POST" action="{{ route('cameras.store') }}">

    @csrf

    <div class="card">

        <div class="card-head">
            <h3>Основні параметри</h3>
        </div>

        <div class="card-pad form-grid">

            <div class="field">

                <label for="name">Назва камери *</label>

                <input id="name"
                       type="text"
                       name="name"
                       value="{{ old('name') }}"
                       required
                       class="input {{ $errors->has('name') ? 'invalid' : '' }}"
                       placeholder="Вхід до офісу">

            </div>

            <div class="field">

                <label for="type">Тип камери *</label>

                <select id="type" name="type" class="input">

                    <option value="usb" @selected(old('type') === 'usb')>
                        USB камера
                    </option>

                    <option value="rtsp" @selected(old('type') === 'rtsp')>
                        IP камера (RTSP)
                    </option>

                    <option value="http" @selected(old('type') === 'http')>
                        HTTP камера
                    </option>

                </select>

            </div>

            <div class="field span-2">

                <label for="source">Джерело відео *</label>

                <input id="source"
                       type="text"
                       name="source"
                       value="{{ old('source') }}"
                       required
                       class="input {{ $errors->has('source') ? 'invalid' : '' }}"
                       placeholder="0 або rtsp://192.168.1.100:554/stream">

                <span class="field-hint">
                    Індекс USB-камери (0, 1, …) або повна адреса RTSP/HTTP-потоку.
                </span>

            </div>

            <div class="field">

                <label for="location">Розташування</label>

                <input id="location"
                       type="text"
                       name="location"
                       value="{{ old('location') }}"
                       class="input"
                       placeholder="Головний вхід">

            </div>

            <div class="field">

                <label for="confidenceNumber">Поріг точності YOLO</label>

                <div class="range-row">

                    <input type="range"
                           id="confidenceRange"
                           min="0" max="1" step="0.01"
                           value="{{ old('confidence_threshold', $defaultConfidence ?? 0.5) }}">

                    <input type="number"
                           id="confidenceNumber"
                           name="confidence_threshold"
                           value="{{ old('confidence_threshold', $defaultConfidence ?? 0.5) }}"
                           min="0" max="1" step="0.01"
                           class="input">

                </div>

                <span class="field-hint">
                    0.4 — більше подій (з шумом), 0.7 — тільки впевнені детекції.
                </span>

            </div>

        </div>

    </div>

    <div class="card" style="margin-top:18px;">

        <div class="card-head">
            <h3>Режими роботи</h3>
        </div>

        <div class="card-pad" style="display:flex; flex-direction:column; gap:12px;">

            <label class="switch-card">

                <span>
                    <span class="switch-title">Камера активна</span>
                    <span class="switch-desc" style="display:block;">
                        Вимкнена камера ігнорується AI-сервером
                    </span>
                </span>

                <span class="switch">
                    <input type="checkbox" name="enabled" checked>
                    <span class="switch-track"></span>
                </span>

            </label>

            <label class="switch-card">

                <span>
                    <span class="switch-title">AI аналіз</span>
                    <span class="switch-desc" style="display:block;">
                        Розпізнавання об'єктів YOLO для цієї камери
                    </span>
                </span>

                <span class="switch">
                    <input type="checkbox" name="ai_enabled" checked>
                    <span class="switch-track"></span>
                </span>

            </label>

            <label class="switch-card">

                <span>
                    <span class="switch-title">Запис відео</span>
                    <span class="switch-desc" style="display:block;">
                        Збереження MP4-архіву в ai_server/videos
                    </span>
                </span>

                <span class="switch">
                    <input type="checkbox" name="recording_enabled" checked>
                    <span class="switch-track"></span>
                </span>

            </label>

        </div>

        <div class="card-pad form-footer" style="border-top:1px solid var(--border);">

            <button type="submit" class="btn btn-primary">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                     stroke-linecap="round" stroke-linejoin="round">
                    <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2Z"/>
                    <path d="M17 21v-8H7v8M7 3v5h8"/>
                </svg>
                Зберегти камеру
            </button>

            <a href="{{ route('cameras.index') }}" class="btn btn-ghost">Скасувати</a>

        </div>

    </div>

</form>

@endsection
