@extends('layouts.panel')

@section('page_title', 'Відеоархів')

@section('content')

<div class="page-header">

    <div>
        <h2>Відеоархів</h2>
        <p>Записи та події за добу · клік по події на шкалі перемотує відео</p>
    </div>

</div>

{{-- ==================== ФІЛЬТРИ ==================== --}}

<div class="card" style="margin-bottom:18px;">

    <form id="archiveFilter" onsubmit="return false;">

        <div class="card-pad filters-row">

            <div class="field">

                <label for="archiveCamera">Камера</label>

                <select id="archiveCamera" class="input">

                    <option value="">Усі камери</option>

                    @foreach ($cameras as $camera)
                        <option value="{{ $camera->id }}"
                                @selected($cameraId == $camera->id)>
                            {{ $camera->name }}
                        </option>
                    @endforeach

                </select>

            </div>

            <div class="field">

                <label for="archiveDate">Дата</label>

                <input id="archiveDate" type="date"
                       value="{{ $date }}" class="input">

            </div>

            <div class="field" style="justify-content:flex-end;">

                <button type="button" class="btn btn-outline" onclick="window.ArchiveLoad()">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                         stroke-linecap="round" stroke-linejoin="round">
                        <path d="M21 12a9 9 0 1 1-2.64-6.36"/>
                        <path d="M21 3v6h-6"/>
                    </svg>
                    Оновити
                </button>

            </div>

        </div>

    </form>

</div>

{{-- ==================== ПЛЕЄР ==================== --}}

<div class="card" style="margin-bottom:18px;">

    <div class="card-head">

        <h3>Плеєр</h3>

        <span class="card-hint" id="archiveStatus">Готово</span>

    </div>

    <div class="card-pad">

        <div class="archive-player" id="archivePlayerWrap">

            <video id="archivePlayer" controls playsinline preload="metadata"></video>

            <div class="player-overlay" id="playerOverlay" hidden>
                <div class="player-overlay-card">
                    <span class="player-overlay-icon" id="playerOverlayIcon">⚠</span>
                    <strong id="playerOverlayTitle">Не вдалося відтворити відео</strong>
                    <p id="playerOverlayText">Файл пошкоджено або браузер не підтримує кодек.</p>
                    <div class="player-overlay-actions">
                        <button type="button" class="btn btn-primary btn-sm" id="playerRetry">Спробувати ще раз</button>
                        <button type="button" class="btn btn-outline btn-sm" id="playerNextBtn">Наступне відео →</button>
                    </div>
                </div>
            </div>

            <div class="player-buffer" id="playerBuffer" hidden>
                <span class="spinner"></span> Завантаження…
            </div>

            <div class="player-badge" id="playerBadge" hidden>LIVE</div>

        </div>

        <div class="archive-player-info">

            <strong id="playerTitle">Відео не вибрано</strong>

            <span id="playerTime">—</span>

        </div>

        <div class="player-toolbar">
            <div class="player-toolbar-group">
                <button type="button" class="btn btn-outline btn-sm" id="btnPrev" title="Попереднє відео (←)">← Попереднє</button>
                <button type="button" class="btn btn-outline btn-sm" id="btnNext" title="Наступне відео (→)">Наступне →</button>
                <button type="button" class="btn btn-outline btn-sm" id="btnBack10" title="Назад на 10 сек (J)">−10 сек</button>
                <button type="button" class="btn btn-outline btn-sm" id="btnFwd10" title="Вперед на 10 сек (L)">+10 сек</button>
            </div>
            <div class="player-toolbar-group">
                <label class="player-speed">Швидкість
                    <select id="playerSpeed" class="input input-sm">
                        <option value="0.5">0.5×</option>
                        <option value="0.75">0.75×</option>
                        <option value="1" selected>1×</option>
                        <option value="1.25">1.25×</option>
                        <option value="1.5">1.5×</option>
                        <option value="2">2×</option>
                    </select>
                </label>
                <label class="player-check"><input type="checkbox" id="playerAutoplay" checked> Автоперехід</label>
                <label class="player-check"><input type="checkbox" id="playerLoop"> Повтор</label>
                <button type="button" class="btn btn-outline btn-sm" id="btnPip" title="Картинка в картинці">⧉ PiP</button>
                <button type="button" class="btn btn-outline btn-sm" id="btnFull" title="На весь екран (F)">⛶ Full</button>
            </div>
        </div>

    </div>

</div>

{{-- ==================== ХРОНОЛОГІЯ ДОБИ (під плеєром) ==================== --}}

<div class="card" style="margin-bottom:18px;">

    <div class="card-head">

        <h3>Хронологія доби</h3>

        <div class="dayline-head-right">
            <span class="card-hint" id="daylineCount">—</span>
            <div class="dayline-zoom">
                <button type="button" class="btn btn-outline btn-sm" id="dayZoomOut" title="Зменшити">−</button>
                <span class="dayline-zoom-label" id="dayZoomLabel">100%</span>
                <button type="button" class="btn btn-outline btn-sm" id="dayZoomIn" title="Збільшити">+</button>
                <button type="button" class="btn btn-outline btn-sm" id="dayZoomReset" title="Показати всю добу">24 г</button>
            </div>
        </div>

    </div>

    <div class="card-pad">

        <div class="dayline-scroll">

            <div class="dayline" id="dayline">

                <div class="dayline-hours" id="daylineHours"></div>

            </div>

        </div>

        <div class="dayline-legend">

            <span class="dayline-legend-item">
                <span class="dayline-legend-video"></span> Запис відео
            </span>

            <span class="dayline-legend-item">
                <span class="dayline-legend-event"></span> Подія AI (клік → перемотка)
            </span>

        </div>

    </div>

</div>

{{-- ==================== КОНФІГ + JS ==================== --}}

<script>
    window.ARCHIVE_CONFIG = {
        dataUrl: '{{ route('archive.data') }}'
    };
</script>
<script src="{{ asset('assets/archive.js') }}?v=6"></script>

@endsection