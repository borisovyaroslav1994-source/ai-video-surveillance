/* ==========================================================
   ОНЛАЙН-МОНІТОРИНГ: оновлення стану кожні 10 секунд
   ========================================================== */

(function () {

    var CONFIG = window.MONITOR_CONFIG || {};
    var DATA_URL = CONFIG.dataUrl || '';
    var newestId = parseInt(CONFIG.newestId || 0, 10);

    /* ---------- DOM ---------- */

    var lastUpdate = document.getElementById('lastUpdate');
    var statOnline = document.getElementById('statOnline');
    var statActive = document.getElementById('statActive');
    var statToday = document.getElementById('statToday');
    var camerasStatusText = document.getElementById('camerasStatusText');
    var monitorEventsList = document.getElementById('monitorEventsList');
    var monitorEventCount = document.getElementById('monitorEventCount');

    if (!DATA_URL) return;

    /* ---------- Допоміжні ---------- */

    function statusClass(status) {

        if (status === 'online') return 'badge-online';
        if (status === 'error') return 'badge-error';

        return 'badge-offline';
    }

    /* ---------- HLS / MJPEG live-прев'ю ---------- */

    function isHls(source) {
        return String(source || '').toLowerCase().indexOf('m3u8') !== -1;
    }

    function attachHls(videoEl, src) {

        var HlsLib = window.Hls;

        /* hls.js доступний */
        if (HlsLib && HlsLib.isSupported && HlsLib.isSupported()) {

            var hls = new HlsLib({ lowLatencyMode: false, maxLiveSyncPlaybackRate: 1.5 });

            hls.loadSource(src);
            hls.attachMedia(videoEl);

            videoEl._hls = hls;

            hls.on(HlsLib.Events.ERROR, function (evt, data) {

                if (!data || !data.fatal) return;

                if (data.type === HlsLib.ErrorTypes.NETWORK_ERROR) {

                    hls.startLoad();

                } else if (data.type === HlsLib.ErrorTypes.MEDIA_ERROR) {

                    hls.recoverMediaError();

                } else {

                    hls.destroy();
                    showStreamUnavailable(videoEl);
                }
            });

            videoEl.addEventListener('playing', function () {
                hideLoading(videoEl);
            });

            videoEl.play().catch(function () {});

            return true;
        }

        /* Нативний HLS (Safari / iOS) */
        if (videoEl.canPlayType('application/vnd.apple.mpegurl')) {

            videoEl.src = src;

            videoEl.addEventListener('playing', function () {
                hideLoading(videoEl);
            });

            videoEl.play().catch(function () {});

            return true;
        }

        showStreamUnavailable(videoEl);

        return false;
    }

    function hideLoading(videoEl) {
        var px = videoEl.closest('.monitor-preview');
        if (px) {
            var ld = px.querySelector('.monitor-loading');
            if (ld) ld.style.display = 'none';
        }
    }

    function showStreamUnavailable(videoEl) {

        var px = videoEl.closest('.monitor-preview');

        if (!px) return;

        px.classList.add('monitor-preview-off');

        px.innerHTML =
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round">'
            + '<path d="M15 10l4.55-2.28A1 1 0 0 1 21 8.62v6.76a1 1 0 0 1-1.45.9L15 14"/>'
            + '<rect x="3" y="6" width="12" height="12" rx="2"/></svg>'
            + '<span class="monitor-message">Немає сигналу</span>';
    }

    /* Створює live-прев'ю всередині tile за даними камери */
    function ensureLivePreview(tile, cam) {

        var preview = tile.querySelector('.monitor-preview');

        if (!preview) return;

        if (tile.dataset.liveReady) return;

        if (isHls(cam.source)) {

            preview.classList.remove('monitor-preview-off');
            preview.innerHTML =
                '<video class="monitor-live" muted autoplay playsinline></video>'
                + '<span class="monitor-loading">Завантаження потоку…</span>';

            var videoEl = preview.querySelector('.monitor-live');

            attachHls(videoEl, cam.source);

            tile.dataset.liveReady = '1';

        } else {

            preview.classList.remove('monitor-preview-off');
            preview.innerHTML = '';

            var img = document.createElement('img');

            img.src = cam.source;
            img.alt = cam.name;
            img.setAttribute('data-mjpeg', 'true');

            img.addEventListener('error', function () {
                preview.classList.add('monitor-preview-off');
                preview.innerHTML =
                    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round">'
                    + '<path d="M15 10l4.55-2.28A1 1 0 0 1 21 8.62v6.76a1 1 0 0 1-1.45.9L15 14"/>'
                    + '<rect x="3" y="6" width="12" height="12" rx="2"/></svg>'
                    + '<span class="monitor-message">Немає сигналу</span>';
            });

            preview.appendChild(img);

            tile.dataset.liveReady = '1';
        }
    }

    function showOfflinePreview(tile, cam) {

        var preview = tile.querySelector('.monitor-preview');

        if (!preview) return;

        preview.classList.add('monitor-preview-off');
        preview.innerHTML =
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round">'
            + '<path d="M15 10l4.55-2.28A1 1 0 0 1 21 8.62v6.76a1 1 0 0 1-1.45.9L15 14"/>'
            + '<rect x="3" y="6" width="12" height="12" rx="2"/></svg>'
            + '<span class="monitor-message">Камера ' + escapeHtml(String(cam.status).toUpperCase()) + '</span>';

        tile.dataset.liveReady = '';
    }

    /* Оновлення усіх live-прев'ю після першого рендеру */
    function setupExistingLive() {

        document.querySelectorAll('.monitor-live').forEach(function (videoEl) {

            var src = videoEl.getAttribute('data-live-src');

            if (!src) return;

            attachHls(videoEl, src);
        });
    }

    function escapeHtml(value) {

        var div = document.createElement('div');

        div.textContent = (value === null || value === undefined) ? '' : String(value);

        return div.innerHTML;
    }

    function prefix(n, one, few, many) {

        var mod10 = n % 10;
        var mod100 = n % 100;

        if (mod10 === 1 && mod100 !== 11) return one;
        if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return few;

        return many;
    }

    /* ---------- Оновлення статусів камер (БЕЗ рестарту MJPEG) ---------- */

    function updateCameraStatuses(cameras) {

        cameras.forEach(function (cam) {

            var tile = document.getElementById('cam-' + cam.id);

            if (!tile) return;

            var badge = tile.querySelector('.monitor-status');

            if (badge) {

                badge.className = 'badge ' + statusClass(cam.status) + ' monitor-status';
                badge.setAttribute('data-status', cam.status);

                badge.innerHTML = '<span class="dot"></span>'
                    + escapeHtml(String(cam.status).toUpperCase());
            }

            /* -- Стан прев'ю: online+http => live-потік, інакше заглушку -- */

            var preview = tile.querySelector('.monitor-preview');

            if (preview) {

                var offline = preview.classList.contains('monitor-preview-off');

                if (cam.status === 'online' && cam.type === 'http' && offline) {

                    ensureLivePreview(tile, cam);

                } else if (cam.status !== 'online' && !offline) {

                    showOfflinePreview(tile, cam);
                }
            }
        });
    }

    /* ---------- Оновлення зведеного стану ---------- */

    function updateStats(json) {

        if (statOnline) statOnline.textContent =
            json.online_cameras + ' / ' + json.total_cameras;

        if (statActive) statActive.textContent = json.active_events;

        if (statToday) statToday.textContent = json.events_today;

        if (camerasStatusText) camerasStatusText.textContent =
            json.total_cameras + ' у системі · '
            + json.online_cameras + ' онлайн';

        if (lastUpdate) lastUpdate.textContent = 'Оновлено: ' + json.server_time;
    }

    function objectBadge(e) {
        if (e && e.object_badge) return e.object_badge;
        return objectMeta(e && e.object).badge;
    }
    function objectMeta(raw) {
        var k = String(raw || '').toLowerCase().trim();
        var map = { person: ['🧍', 'Людина'], car: ['🚗', 'Авто'], truck: ['🚚', 'Вантажівка'], bus: ['🚌', 'Автобус'], bicycle: ['🚲', 'Велосипед'], motorbike: ['🏍', 'Мотоцикл'], motorcycle: ['🏍', 'Мотоцикл'], dog: ['🐕', 'Собака'], cat: ['🐈', 'Кіт'], bird: ['🐦', 'Птах'] };
        if (map[k]) return { icon: map[k][0], badge: map[k][0] + ' ' + map[k][1] };
        return { icon: '📦', badge: '📦 ' + (raw || 'Обʼєкт') };
    }

    function renderEvent(event) {

        var row = document.createElement('div');

        row.className = 'monitor-event monitor-event-new';
        row.setAttribute('data-id', event.id);

        var thumb = '';

        if (event.image_url) {
            thumb = '<span class="monitor-event-thumb"><img loading="lazy" src="'
                + escapeHtml(event.image_url) + '" alt="' + escapeHtml(objectBadge(event))
                + '"></span>';
        } else {
            thumb = '<span class="monitor-event-thumb monitor-event-thumb-ph">'
                + '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round">'
                + '<circle cx="12" cy="8" r="4"/><path d="M5 21c0-4 3-6 7-6s7 2 7 6"/></svg></span>';
        }

        row.innerHTML =
            thumb
            + '<span class="monitor-event-info"><strong>'
            + escapeHtml(objectBadge(event)) + '</strong>'
            + '<span>' + escapeHtml(event.camera_name || '') + '</span></span>'
            + '<span class="mini-pill on">активна</span>'
            + '<span class="monitor-event-time">' + escapeHtml(event.date || '') + ' '
            + escapeHtml(event.time || '—') + '</span>';

        return row;
    }

    function renderEmptyState() {

        var box = document.createElement('div');

        box.className = 'empty-state';

        box.innerHTML =
            '<span class="empty-icon">'
            + '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"'
            + ' stroke-linecap="round" stroke-linejoin="round">'
            + '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/>'
            + '<path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/></svg>'
            + '</span>'
            + '<h4>Подій ще немає</h4>'
            + '<p>Запустіть Python AI-сервер — нові події з\'являться тут автоматично.</p>';

        return box;
    }

    function updateEvents(events) {

        if (!monitorEventsList) return;

        /* ID, що є у відповіді сервера */
        var incoming = {};

        events.forEach(function (event) {
            incoming[String(event.id)] = true;
        });

        /* Прибираємо рядки, яких уже немає в відповіді
           (події могли бути видалено в журналі чи БД) */
        monitorEventsList.querySelectorAll('.monitor-event').forEach(function (el) {
            if (!incoming[el.getAttribute('data-id')]) {
                el.remove();
            }
        });

        var known = {};

        monitorEventsList.querySelectorAll('.monitor-event').forEach(function (el) {
            known[el.getAttribute('data-id')] = true;
        });

        var added = 0;
        var hasNew = false;

        /* Нові події з'явились — прибираємо пустий стан */
        if (events.length > 0) {
            var emptyStateEl = monitorEventsList.querySelector('.empty-state');
            if (emptyStateEl) emptyStateEl.remove();
        }

        events.forEach(function (event) {

            var id = String(event.id);

            if (known[id]) return;

            var first = monitorEventsList.querySelector(
                '.monitor-event:not(.empty-state), .monitor-event'
            );

            /* Вставляємо перед першим елементом списку */
            monitorEventsList.insertBefore(renderEvent(event), first);

            known[id] = true;
            added++;

            if (parseInt(event.id, 10) > newestId) hasNew = true;
        });

        /* Обрізаємо до 8 рядків */
        var all = monitorEventsList.querySelectorAll('.monitor-event');

        for (var i = all.length - 1; i >= 8; i--) {
            all[i].remove();
        }

        /* Якщо рядків не стало — повертаємо пустий стан */
        if (monitorEventsList.querySelectorAll('.monitor-event').length === 0
            && !monitorEventsList.querySelector('.empty-state')) {
            monitorEventsList.appendChild(renderEmptyState());
        }

        if (monitorEventCount) {

            monitorEventCount.textContent =
                all.length + ' ' + prefix(all.length, 'запис', 'записи', 'записів')
                + ' за останню добу'
                + (hasNew ? ' · +' + added + ' нов.' + (added === 1 ? 'а' : 'і') : '');
        }

        if (hasNew) {
            setTimeout(function () {
                monitorEventsList.querySelectorAll('.monitor-event-new').forEach(function (el) {
                    el.classList.remove('monitor-event-new');
                });
            }, 4000);
        }
    }

    /* ---------- Опитування ---------- */

    function poll() {

        fetch(DATA_URL)
            .then(function (r) {

                if (!r.ok) throw new Error('HTTP ' + r.status);

                return r.json();

            })
            .then(function (json) {

                if (!json.success) return;

                updateStats(json);
                updateCameraStatuses(json.cameras || []);
                updateEvents(json.events || []);

                if (json.newest_event_id > newestId) newestId = json.newest_event_id;

            })
            .catch(function () {
                /* тихо — мережа могла зникнути на момент */
            });
    }

    /* ---------- Перший запуск ---------- */

    setupExistingLive();

    poll();

    setInterval(poll, 10000);

})();