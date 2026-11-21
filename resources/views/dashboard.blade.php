@extends('layouts.panel')

@section('page_title', 'Огляд системи')

@section('content')

<div class="page-header">

    <div>
        <h2>Вітаємо, {{ auth()->user()->name }} 👋</h2>
        <p>
            Стан камер, подій AI та архіву записів
            на {{ now()->format('d.m.Y') }}
        </p>
    </div>

    <div class="page-actions">

        <a href="{{ route('monitoring.index') }}" class="btn btn-outline">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                 stroke-linecap="round" stroke-linejoin="round">
                <path d="M2 12h3l2-7 4 14 3-9 2 4h6"/>
            </svg>
            Моніторинг
        </a>

        <a href="{{ route('cameras.create') }}" class="btn btn-primary">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                 stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 5v14M5 12h14"/>
            </svg>
            Додати камеру
        </a>

        <a href="{{ route('archive.index') }}" class="btn btn-outline">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                 stroke-linecap="round" stroke-linejoin="round">
                <rect x="2" y="4" width="20" height="16" rx="2"/>
                <path d="M10 9l5 3-5 3z"/>
            </svg>
            Відеоархів
        </a>

    </div>

</div>

{{-- ==================== СТАТИСТИКА ==================== --}}

<div class="stats-grid">

    <a href="{{ route('cameras.index') }}" class="stat-card">

        <span class="stat-icon blue">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"
                 stroke-linecap="round" stroke-linejoin="round">
                <path d="M15 10l4.55-2.28A1 1 0 0 1 21 8.62v6.76a1 1 0 0 1-1.45.9L15 14"/>
                <rect x="3" y="6" width="12" height="12" rx="2"/>
            </svg>
        </span>

        <div>
            <div class="stat-value">{{ $stats['cameras_total'] }}</div>
            <div class="stat-label">Камер у системі</div>
        </div>

    </a>

    <div class="stat-card">

        <span class="stat-icon green">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"
                 stroke-linecap="round" stroke-linejoin="round">
                <path d="M2 12h3l2-7 4 14 3-9 2 4h6"/>
            </svg>
        </span>

        <div>
            <div class="stat-value">
                {{ $stats['cameras_online'] }}
                <span style="font-size:14px; color:var(--muted); font-weight:600;">
                    / {{ $stats['cameras_total'] }}
                </span>
            </div>
            <div class="stat-label">Камер онлайн</div>
        </div>

    </div>

    <a href="{{ route('events.index') }}" class="stat-card">

        <span class="stat-icon amber">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"
                 stroke-linecap="round" stroke-linejoin="round">
                <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/>
                <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>
            </svg>
        </span>

        <div>
            <div class="stat-value">{{ $stats['events_today'] }}</div>
            <div class="stat-label">Подій AI за сьогодні</div>
        </div>

    </a>

    <a href="{{ route('archive.index') }}" class="stat-card">

        <span class="stat-icon red">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"
                 stroke-linecap="round" stroke-linejoin="round">
                <rect x="2" y="4" width="20" height="16" rx="2"/>
                <path d="M10 9l5 3-5 3z"/>
            </svg>
        </span>

        <div>
            <div class="stat-value">
                {{ $stats['videos_today'] }}
                <span style="font-size:13px; color:var(--muted); font-weight:600;">
                    ({{ number_format($storageBytes / 1024 / 1024 / 1024, 2, '.', '') }} GB)
                </span>
            </div>
            <div class="stat-label">Записів за сьогодні</div>
        </div>

    </a>

</div>

{{-- ==================== ПОДІЇ ТА КАМЕРИ ==================== --}}

<div class="grid-2">

    {{-- Останні події --}}

    <div class="card">

        <div class="card-head">
            <h3>Останні події AI</h3>
            <a href="{{ route('events.index') }}" class="card-hint">Усі події →</a>
        </div>

        @if ($recentEvents->isEmpty())

            <div class="empty-state">

                <span class="empty-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"
                         stroke-linecap="round" stroke-linejoin="round">
                        <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/>
                        <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>
                    </svg>
                </span>

                <h4>Подій ще немає</h4>

                <p>
                    Запустіть Python AI-сервер — події розпізнавання
                    з'являться тут автоматично.
                </p>

                <a href="{{ route('events.index') }}" class="btn btn-outline">
                    Перейти до журналу подій
                </a>

            </div>

        @else

            <div style="padding:18px 22px;">

                <div class="events-grid">

                    @foreach ($recentEvents as $event)

                        <div class="event-card">

                            <div class="event-thumb">

                                @if ($event->image_url)
                                    <img src="{{ $event->image_url }}" alt="{{ \App\Support\ObjectIcon::badge($event->object) }}" loading="lazy">
                                @else
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                                         stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round">
                                        <circle cx="12" cy="8" r="4"/>
                                        <path d="M5 21c0-4 3-6 7-6s7 2 7 6"/>
                                    </svg>
                                @endif

                                <span class="badge badge-object event-object">
                                    {{ \App\Support\ObjectIcon::badge($event->object) }}
                                </span>

                            </div>

                            <div class="event-body">

                                <div class="event-meta">

                                    <span>{{ $event->camera_name ?? 'Камера #' . $event->camera_id }}</span>

                                    <span>
                                        {{ $event->detected_at?->format('H:i:s') ?? '—' }}
                                    </span>

                                </div>

                                <div class="confidence-bar">
                                    <span style="width: {{ (int) round($event->confidence * 100) }}%;"></span>
                                </div>

                                <div class="event-meta" style="margin-top:7px;">

                                    <span>
                                        Точність {{ number_format($event->confidence * 100, 0) }}%
                                    </span>

                                    <span>
                                        {{ $event->detected_at?->format('d.m') ?? '' }}
                                        @if ($event->status === 'active')
                                            · <span style="color:var(--success);">активна</span>
                                        @endif
                                    </span>

                                </div>

                            </div>

                        </div>

                    @endforeach

                </div>

            </div>

        @endif

    </div>

    {{-- Стан камер --}}

    <div class="card">

        <div class="card-head">
            <h3>Камери</h3>
            <a href="{{ route('cameras.index') }}" class="card-hint">Керувати →</a>
        </div>

        @if ($cameras->isEmpty())

            <div class="empty-state">

                <span class="empty-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"
                         stroke-linecap="round" stroke-linejoin="round">
                        <path d="M15 10l4.55-2.28A1 1 0 0 1 21 8.62v6.76a1 1 0 0 1-1.45.9L15 14"/>
                        <rect x="3" y="6" width="12" height="12" rx="2"/>
                    </svg>
                </span>

                <h4>Камер не додано</h4>

                <p>Додайте першу камеру, щоб почати спостереження.</p>

                <a href="{{ route('cameras.create') }}" class="btn btn-primary">
                    Додати камеру
                </a>

            </div>

        @else

            @foreach ($cameras as $camera)

                <div class="camera-row">

                    <span class="badge {{ $camera->status === 'online' ? 'badge-online' : ($camera->status === 'error' ? 'badge-error' : 'badge-offline') }}">
                        <span class="dot"></span>
                    </span>

                    <div>
                        <span class="cell-strong">{{ $camera->name }}</span>
                        <span class="cell-sub">
                            {{ $camera->location ?? 'Без розташування' }}
                        </span>
                    </div>

                    <div class="camera-row-icons">

                        @if ($camera->ai_enabled)
                            <span class="mini-pill on">AI</span>
                        @endif

                        @if ($camera->recording_enabled)
                            <span class="mini-pill on">REC</span>
                        @endif

                    </div>

                </div>

            @endforeach

        @endif

    </div>

</div>

@endsection
