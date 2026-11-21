@extends('layouts.panel')

@section('page_title', 'Події AI')

@section('content')

<div class="page-header">

    <div>
        <h2>Події AI</h2>
        <p>
            Журнал розпізнавань: {{ $events->total() }}
            записів @if(request()->filled('date'))за {{ request('date') }}@endif
        </p>
    </div>

</div>

{{-- ==================== НОВІ ПОДІЇ ==================== --}}

<div class="alert alert-info" id="newEventsBanner" style="display:none;">

    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
         stroke-linecap="round" stroke-linejoin="round">
        <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/>
        <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>
    </svg>

    <span>Надійшли нові події AI.</span>

    <button type="button" class="btn btn-outline" onclick="location.reload()">
        Оновити
    </button>

</div>

{{-- ==================== ФІЛЬТРИ ==================== --}}

<div class="card" style="margin-bottom:18px;">

    <form id="eventsFilter" method="GET" action="{{ route('events.index') }}">

        <div class="card-pad filters-row">

            <div class="field">

                <label for="f-camera">Камера</label>

                <select id="f-camera" name="camera_id" class="input">

                    <option value="">Усі камери</option>

                    @foreach ($cameras as $camera)
                        <option value="{{ $camera->id }}"
                                @selected(request('camera_id') == $camera->id)>
                            {{ $camera->name }}
                        </option>
                    @endforeach

                </select>

            </div>

            <div class="field">

                <label for="f-object">Об'єкт</label>

                <select id="f-object" name="object" class="input">

                    <option value="">Усі об'єкти</option>

                    @foreach ($objects as $object)
                        <option value="{{ $object }}"
                                @selected(request('object') === $object)>
                            {{ \App\Support\ObjectIcon::badge($object) }}
                        </option>
                    @endforeach

                </select>

            </div>

            <div class="field">

                <label for="f-status">Статус</label>

                <select id="f-status" name="status" class="input">

                    <option value="">Усі</option>

                    <option value="active"
                            @selected(request('status') === 'active')>
                        Активні
                    </option>

                    <option value="completed"
                            @selected(request('status') === 'completed')>
                        Завершені
                    </option>

                </select>

            </div>

            <div class="field">

                <label for="f-date">Дата</label>

                <input id="f-date" type="date" name="date"
                       value="{{ request('date') }}" class="input">

            </div>

            <div class="field" style="justify-content:flex-end;">

                <button type="submit" class="btn btn-primary">
                    Застосувати
                </button>

            </div>

        </div>

    </form>

</div>

{{-- ==================== СПИСОК ПОДІЙ ==================== --}}

<div class="card">

    @if ($events->isEmpty())

        <div class="empty-state">

            <span class="empty-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"
                     stroke-linecap="round" stroke-linejoin="round">
                    <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/>
                    <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>
                </svg>
            </span>

            <h4>Подій не знайдено</h4>

            <p>
                Спробуйте змінити фільтри або перевірте, чи запущений
                Python AI-сервер — нові події з'являються тут автоматично.
            </p>

            <a href="{{ route('events.index') }}" class="btn btn-outline">
                Скинути фільтри
            </a>

        </div>

    @else

        <div style="padding:18px 22px;">

            <div class="events-grid">

                @foreach ($events as $event)

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

                                <span>
                                    {{ $event->camera_name ?? 'Камера #' . $event->camera_id }}
                                </span>

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
                                    · {{ $event->detected_at?->format('d.m.Y') ?? '' }}
                                </span>

                                <span class="mini-pill {{ $event->status === 'active' ? 'on' : 'off' }}">
                                    {{ $event->status === 'active' ? 'активна' : 'завершена' }}
                                </span>

                            </div>

                        </div>

                    </div>

                @endforeach

            </div>

        </div>

        <div style="padding: 6px 22px 20px;">
            {{ $events->links('pagination.custom') }}
        </div>

    @endif

</div>

{{-- ==================== JS: live-перевірка нових подій ==================== --}}

<script>
    document.body.setAttribute('data-newest-event-id', '{{ $newestId }}');
    document.body.setAttribute('data-events-api-url', '{{ url('api/events') }}');
</script>
<script src="{{ asset('assets/events.js') }}?v=1"></script>

@endsection
