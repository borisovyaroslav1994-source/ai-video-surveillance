@extends('layouts.panel')

@section('page_title', 'Онлайн-моніторинг')

@section('content')

<div class="page-header">

    <div>
        <h2>Онлайн-моніторинг</h2>
        <p>
            Стан камер у реальному часі
            · автоматичне оновлення кожні 10 секунд
        </p>
    </div>

    <div class="page-actions">

        <span class="live-chip">
            <span class="dot"></span>
            LIVE
        </span>

        <span class="topbar-date" id="lastUpdate">—</span>

    </div>

</div>

{{-- ==================== ЗВЕДЕННЯ ==================== --}}

<div class="stats-grid">

    <div class="stat-card">

        <span class="stat-icon green">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"
                 stroke-linecap="round" stroke-linejoin="round">
                <path d="M2 12h3l2-7 4 14 3-9 2 4h6"/>
            </svg>
        </span>

        <div>
            <div class="stat-value" id="statOnline">
                {{ $onlineCameras }} / {{ $cameras->count() }}
            </div>
            <div class="stat-label">Камер онлайн</div>
        </div>

    </div>

    <div class="stat-card">

        <span class="stat-icon amber">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"
                 stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="9"/>
                <path d="M12 8v4M12 16h.01"/>
            </svg>
        </span>

        <div>
            <div class="stat-value" id="statActive">{{ $activeEvents }}</div>
            <div class="stat-label">Активні події зараз</div>
        </div>

    </div>

    <div class="stat-card">

        <span class="stat-icon blue">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"
                 stroke-linecap="round" stroke-linejoin="round">
                <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/>
                <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>
            </svg>
        </span>

        <div>
            <div class="stat-value" id="statToday">{{ $eventsToday }}</div>
            <div class="stat-label">Подій за сьогодні</div>
        </div>

    </div>

    <div class="stat-card">

        <span class="stat-icon red">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"
                 stroke-linecap="round" stroke-linejoin="round">
                <path d="M15 10l4.55-2.28A1 1 0 0 1 21 8.62v6.76a1 1 0 0 1-1.45.9L15 14"/>
                <rect x="3" y="6" width="12" height="12" rx="2"/>
            </svg>
        </span>

        <div>
            <div class="stat-value">
                {{ $cameras->where('recording_enabled')->count() }}
            </div>
            <div class="stat-label">Камер із записом</div>
        </div>

    </div>

</div>

{{-- ==================== СІТКА КАМЕР ==================== --}}

<div class="card" style="margin-bottom:18px;">

    <div class="card-head">

        <h3>Камери</h3>

        <span class="card-hint" id="camerasStatusText">
            {{ $cameras->count() }} у системі
        </span>

    </div>

    <div class="card-pad">

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

                <p>Додайте камеру, щоб бачити її стан у режимі реального часу.</p>

                <a href="{{ route('cameras.create') }}" class="btn btn-primary">
                    Додати камеру
                </a>

            </div>

        @else

            <div class="monitor-grid" id="monitorGrid">

                @foreach ($cameras as $camera)

                    <div class="monitor-tile" id="cam-{{ $camera->id }}">

                        {{-- LIVE: HLS (.m3u8) => <video>+hls.js, інакше MJPEG => <img> --}}
                        @if ($camera->status === 'online' && $camera->type === 'http' && str_contains(strtolower($camera->source), 'm3u8'))
                            <div class="monitor-preview">
                                <video class="monitor-live" data-live-src="{{ $camera->source }}" muted autoplay playsinline></video>
                                <span class="monitor-loading">Завантаження потоку…</span>
                            </div>
                        @elseif ($camera->status === 'online' && $camera->type === 'http')
                            <div class="monitor-preview">
                                <img src="{{ $camera->source }}" alt="{{ $camera->name }}"
                                     data-mjpeg="true">
                            </div>
                        @else
                            <div class="monitor-preview monitor-preview-off">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                                     stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M15 10l4.55-2.28A1 1 0 0 1 21 8.62v6.76a1 1 0 0 1-1.45.9L15 14"/>
                                    <rect x="3" y="6" width="12" height="12" rx="2"/>
                                </svg>
                                <span class="monitor-message">
                                    @if ($camera->status === 'offline')
                                        Камера offline
                                    @else
                                        Прямий перегляд недоступний для {{ strtoupper($camera->type) }}
                                    @endif
                                </span>
                            </div>
                        @endif

                        <div class="monitor-tile-body">

                            <div class="monitor-tile-row">

                                <strong class="monitor-name">{{ $camera->name }}</strong>

                                <span class="badge badge-offline monitor-status"
                                      data-status="{{ $camera->status }}">
                                    <span class="dot"></span>
                                    {{ strtoupper($camera->status) }}
                                </span>

                            </div>

                            <span class="monitor-sub">
                                {{ $camera->location ?? 'Без розташування' }} ·
                                {{ strtoupper($camera->type) }}
                            </span>

                            <div class="monitor-pills">

                                @if ($camera->ai_enabled)
                                    <span class="mini-pill on">AI</span>
                                @endif

                                @if ($camera->recording_enabled)
                                    <span class="mini-pill on">REC</span>
                                @endif

                            </div>

                        </div>

                    </div>

                @endforeach

            </div>

        @endif

    </div>

</div>

{{-- ==================== ЖИВИЙ ЖУРНАЛ ПОДІЙ ==================== --}}

<div class="card">

    <div class="card-head">

        <h3>Останні події</h3>

        <div class="page-actions" style="gap:8px;">

            <span class="card-hint" id="monitorEventCount">
                {{ $recentEvents->count() }} за останню добу
            </span>

            <a href="{{ route('events.index') }}" class="card-hint">Журнал →</a>

        </div>

    </div>

    <div class="monitor-events-list" id="monitorEventsList">

        @forelse ($recentEvents as $event)

            <div class="monitor-event" data-id="{{ $event->id }}">

                @if ($event->image_url)
                    <span class="monitor-event-thumb">
                        <img src="{{ $event->image_url }}" alt="{{ \App\Support\ObjectIcon::badge($event->object) }}" loading="lazy">
                    </span>
                @else
                    <span class="monitor-event-thumb monitor-event-thumb-ph">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4"
                             stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="12" cy="8" r="4"/>
                            <path d="M5 21c0-4 3-6 7-6s7 2 7 6"/>
                        </svg>
                    </span>
                @endif

                <span class="monitor-event-info">
                    <strong>{{ \App\Support\ObjectIcon::badge($event->object) }}</strong>
                    <span>{{ $event->camera_name ?? 'Камера #' . $event->camera_id }}</span>
                </span>

                <span class="mini-pill {{ $event->status === 'active' ? 'on' : 'off' }}">
                    {{ $event->status === 'active' ? 'активна' : 'завершена' }}
                </span>

                <span class="monitor-event-time">
                    {{ $event->detected_at?->format('d.m H:i:s') ?? '—' }}
                </span>

            </div>

        @empty

            <div class="empty-state">

                <span class="empty-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"
                         stroke-linecap="round" stroke-linejoin="round">
                        <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/>
                        <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>
                    </svg>
                </span>

                <h4>Подій ще немає</h4>

                <p>Запустіть Python AI-сервер — нові події з'являться тут автоматично.</p>

            </div>

        @endforelse

    </div>

</div>

{{-- ==================== КОНФІГ + JS ==================== --}}

<script>
    window.MONITOR_CONFIG = {
        dataUrl: '{{ route('monitoring.data') }}',
        newestId: {{ $newestEventId }}
    };
</script>
<script src="https://cdn.jsdelivr.net/npm/hls.js@1.5.13/dist/hls.min.js"></script>
<script src="{{ asset('assets/monitoring.js') }}?v=2"></script>

@endsection