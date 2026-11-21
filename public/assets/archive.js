/* ВІДЕОАРХІВ v2: dayline + покращений плеєр (HEAD-check, overlay, retry) */
(function () {
    var CONFIG = window.ARCHIVE_CONFIG || {};
    var DATA_URL = CONFIG.dataUrl || '';
    var videos = [];
    var events = [];
    var currentVideoIndex = -1;
    var pendingSeek = null;
    var loadToken = 0;
    var retryCount = 0;
    var dayline = document.getElementById('dayline');
    var daylineHours = document.getElementById('daylineHours');
    var daylineCount = document.getElementById('daylineCount');
    var player = document.getElementById('archivePlayer');
    var playerWrap = document.getElementById('archivePlayerWrap');
    var playerTitle = document.getElementById('playerTitle');
    var playerTime = document.getElementById('playerTime');
    var statusEl = document.getElementById('archiveStatus');
    var cameraSelect = document.getElementById('archiveCamera');
    var dateInput = document.getElementById('archiveDate');
    var overlay = document.getElementById('playerOverlay');
    var overlayTitle = document.getElementById('playerOverlayTitle');
    var overlayText = document.getElementById('playerOverlayText');
    var overlayIcon = document.getElementById('playerOverlayIcon');
    var btnRetry = document.getElementById('playerRetry');
    var btnNextOverlay = document.getElementById('playerNextBtn');
    var bufferEl = document.getElementById('playerBuffer');
    var btnPrev = document.getElementById('btnPrev');
    var btnNext = document.getElementById('btnNext');
    var btnBack10 = document.getElementById('btnBack10');
    var btnFwd10 = document.getElementById('btnFwd10');
    var speedSel = document.getElementById('playerSpeed');
    var autoplayBox = document.getElementById('playerAutoplay');
    var loopBox = document.getElementById('playerLoop');
    var btnPip = document.getElementById('btnPip');
    var btnFull = document.getElementById('btnFull');
    var dayScroll = document.querySelector('.dayline-scroll');
    var btnZoomIn = document.getElementById('dayZoomIn');
    var btnZoomOut = document.getElementById('dayZoomOut');
    var btnZoomReset = document.getElementById('dayZoomReset');
    var zoomLabel = document.getElementById('dayZoomLabel');
    if (!dayline || !player) return;

    /* ---------- Зум хронології ---------- */

    var DAY_ZOOMS = [1, 1.5, 2, 3, 4, 6, 8, 12];
    var dayZoomIndex = 0;

    function applyDayZoom(keepCenterRatio) {
        var z = DAY_ZOOMS[dayZoomIndex] || 1;
        if (dayline) {
            dayline.style.minWidth = Math.round(900 * z) + 'px';
        }
        if (zoomLabel) {
            zoomLabel.textContent = Math.round(z * 100) + '%';
        }
        if (btnZoomOut) btnZoomOut.disabled = (dayZoomIndex <= 0);
        if (btnZoomIn) btnZoomIn.disabled = (dayZoomIndex >= DAY_ZOOMS.length - 1);
        if (dayScroll && typeof keepCenterRatio === 'number') {
            var max = dayScroll.scrollWidth - dayScroll.clientWidth;
            if (max > 0) {
                dayScroll.scrollLeft = Math.round(max * keepCenterRatio);
            }
        }
        try {
            localStorage.setItem('archive.dayZoom', String(dayZoomIndex));
        } catch (e) {}
    }

    function dayScrollCenter() {
        if (!dayScroll) return 0;
        var max = dayScroll.scrollWidth - dayScroll.clientWidth;
        if (max <= 0) return 0;
        return dayScroll.scrollLeft / max;
    }

    try {
        var savedZoom = parseInt(localStorage.getItem('archive.dayZoom') || '0', 10);
        if (savedZoom >= 0 && savedZoom < DAY_ZOOMS.length) dayZoomIndex = savedZoom;
    } catch (e) {}

    if (btnZoomIn) {
        btnZoomIn.addEventListener('click', function () {
            if (dayZoomIndex < DAY_ZOOMS.length - 1) {
                var c = dayScrollCenter();
                dayZoomIndex++;
                applyDayZoom(c);
            }
        });
    }

    if (btnZoomOut) {
        btnZoomOut.addEventListener('click', function () {
            if (dayZoomIndex > 0) {
                var c = dayScrollCenter();
                dayZoomIndex--;
                applyDayZoom(c);
            }
        });
    }

    if (btnZoomReset) {
        btnZoomReset.addEventListener('click', function () {
            dayZoomIndex = 0;
            applyDayZoom(0);
        });
    }

    applyDayZoom();

    /* ---------- Допоміжні ---------- */

    function timeToSeconds(value) {

        if (!value) return null;

        var parts = String(value).trim().split(' ');
        var time = parts[parts.length - 1];
        var chunks = time.split(':');

        if (chunks.length < 2) return null;

        var h = parseInt(chunks[0], 10) || 0;
        var m = parseInt(chunks[1], 10) || 0;
        var s = chunks.length > 2 ? (parseInt(chunks[2], 10) || 0) : 0;

        return h * 3600 + m * 60 + s;
    }

    function getClockTime(value) {

        if (!value) return '—';

        var parts = String(value).trim().split(' ');

        return parts[parts.length - 1];
    }

    function formatTime(totalSeconds) {

        var t = Math.max(0, Math.round(totalSeconds || 0));
        var h = String(Math.floor(t / 3600)).padStart(2, '0');
        var m = String(Math.floor((t % 3600) / 60)).padStart(2, '0');
        var s = String(t % 60).padStart(2, '0');

        return h + ':' + m + ':' + s;
    }

    function escapeHtml(value) {

        var div = document.createElement('div');

        div.textContent = (value === null || value === undefined) ? '' : String(value);

        return div.innerHTML;
    }

    function setStatus(text) {
        if (statusEl) statusEl.textContent = text;
    }
    function showBuffer(on) { if (bufferEl) bufferEl.hidden = !on; }
    function showOverlay(t, x, i) {
        if (!overlay) return;
        if (overlayTitle && t) overlayTitle.textContent = t;
        if (overlayText && x) overlayText.textContent = x;
        if (overlayIcon && i) overlayIcon.textContent = i;
        overlay.hidden = false;
    }
    function hideOverlay() { if (overlay) overlay.hidden = true; }
    function canPlayMp4() {
        try {
            var t = document.createElement('video');
            var r = t.canPlayType('video/mp4; codecs="avc1.42E01E, mp4a.40.2"');
            return r === 'probably' || r === 'maybe';
        } catch (e) { return true; }
    }
    function formatSize(b) {
        b = Number(b || 0);
        if (b <= 0) return '0 МБ';
        return (b / 1048576).toFixed(1) + ' МБ';
    }
    function pluralUA(n, one, few, many) {
        n = Math.abs(Math.round(Number(n) || 0)) % 100;
        var d = n % 10;
        if (n > 10 && n < 20) return many;
        if (d > 1 && d < 5) return few;
        if (d === 1) return one;
        return many;
    }
    function formatDuration(totalSeconds, short) {
        var t = Math.max(0, Math.round(Number(totalSeconds) || 0));
        var h = Math.floor(t / 3600);
        var m = Math.floor((t % 3600) / 60);
        var s = t % 60;
        if (short) {
            if (h > 0) return h + ' год ' + m + ' хв';
            if (m > 0 && s > 0) return m + ' хв ' + s + ' с';
            if (m > 0) return m + ' ' + pluralUA(m, 'хвилина', 'хвилини', 'хвилин');
            return s + ' ' + pluralUA(s, 'секунда', 'секунди', 'секунд');
        }
        var parts = [];
        if (h > 0) parts.push(h + ' ' + pluralUA(h, 'година', 'години', 'годин'));
        if (m > 0) parts.push(m + ' ' + pluralUA(m, 'хвилина', 'хвилини', 'хвилин'));
        if (s > 0 || parts.length === 0) parts.push(s + ' ' + pluralUA(s, 'секунда', 'секунди', 'секунд'));
        return parts.join(' ');
    }
    function objectBadge(e) {
        if (e && e.object_badge) return e.object_badge;
        var k = String((e && e.object) || '').toLowerCase().trim();
        var map = { person: '🧍 Людина', car: '🚗 Авто', truck: '🚚 Вантажівка', bus: '🚌 Автобус', bicycle: '🚲 Велосипед', motorbike: '🏍 Мотоцикл', motorcycle: '🏍 Мотоцикл', dog: '🐕 Собака', cat: '🐈 Кіт', bird: '🐦 Птах' };
        if (map[k]) return map[k];
        return '📦 ' + ((e && e.object) || 'Обʼєкт');
    }

    function plural(n, one, few, many) {

        var mod10 = n % 10;
        var mod100 = n % 100;

        if (mod10 === 1 && mod100 !== 11) return one;
        if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return few;

        return many;
    }

        /* ==========================================================
       ЗАВАНТАЖЕННЯ ДАНИХ
       ========================================================== */

    window.ArchiveLoad = function () {

        var date = dateInput.value;

        if (!date) {
            alert('Виберіть дату');
            return;
        }

        setStatus('Завантаження…');

        var url = DATA_URL + '?date=' + encodeURIComponent(date);

        if (cameraSelect.value) {
            url += '&camera_id=' + encodeURIComponent(cameraSelect.value);
        }

        fetch(url)
            .then(function (r) {

                if (!r.ok) throw new Error('HTTP ' + r.status);

                return r.json();

            })
            .then(function (json) {

                videos = json.videos || [];
                events = json.events || [];
                currentVideoIndex = -1;
                pendingSeek = null;
                retryCount = 0;

                renderDayline();

                var total = videos.reduce(function (a, v) { return a + (Number(v.size) || 0); }, 0);
                setStatus(
                    videos.length + ' ' + plural(videos.length, 'запис', 'записи', 'записів')
                    + ' · ' + events.length + ' ' + plural(events.length, 'подія', 'події', 'подій')
                    + ' · ' + formatSize(total)
                );

                if (videos.length > 0) { playVideo(0); }
                else {
                    playerTitle.textContent = 'Записів за цей день немає';
                    playerTime.textContent = '—';
                    showOverlay('Записів немає', 'За вибрану дату та камеру записів не знайдено.', '📼');
                }

            })
            .catch(function (e) {

                setStatus('Помилка: ' + e.message);
                showOverlay('Не вдалося завантажити список', String(e.message || e), '⚠');

            });
    };

    /* ==========================================================
       DAYLINE
       ========================================================== */

    function renderHours() {

        daylineHours.innerHTML = '';

        for (var h = 0; h <= 24; h++) {

            var label = document.createElement('div');

            label.className = 'dayline-hour';
            label.textContent = h;

            label.style.left = (h / 24 * 100) + '%';

            if (h === 0) label.classList.add('first');
            if (h === 24) label.classList.add('last');

            daylineHours.appendChild(label);

        }

        for (var g = 1; g < 24; g++) {

            var line = document.createElement('div');

            line.className = 'dayline-grid-line';

            line.style.left = (g / 24 * 100) + '%';

            dayline.appendChild(line);

        }
    }

    function clearDayline() {

        dayline.innerHTML = '';

        dayline.appendChild(daylineHours);

        renderHours();

    }

    function renderDayline() {

        if (!dayline) return;

        if (daylineHours && !dayline.contains(daylineHours)) {
            dayline.appendChild(daylineHours);
        }

        clearDayline();

        var total = videos.length + events.length;

        daylineCount.textContent =
            videos.length + ' ' + plural(videos.length, 'запис', 'записи', 'записів')
            + ' · ' + events.length + ' ' + plural(events.length, 'подія', 'події', 'подій');

        if (total === 0) {

            var empty = document.createElement('div');

            empty.className = 'dayline-empty';
            empty.textContent = 'За вибрану дату записів та подій немає.';

            dayline.appendChild(empty);

            return;
        }

        /* Сегменти відео */

        videos.forEach(function (video, index) {

            var start = timeToSeconds(video.started_at);

            if (start === null) return;

            var duration = Number(video.duration || 0);

            if (duration <= 0 && video.ended_at) {
                duration = timeToSeconds(video.ended_at) - start;
            }

            if (duration <= 0) duration = 1;

            var segment = document.createElement('div');

            segment.className = 'dayline-video'
                + (index === currentVideoIndex ? ' active' : '');

            segment.style.left = (start / 86400 * 100) + '%';
            segment.style.width = Math.max(duration / 86400 * 100, 0.25) + '%';

            segment.title = (video.camera_name || ('Camera ' + video.camera_id))
                + ' | ' + getClockTime(video.started_at)
                + ' | ' + formatDuration(duration);

            segment.onclick = function () { playVideo(index); };

            dayline.appendChild(segment);

        });

        /* Маркери подій */

        events.forEach(function (event) {

            var seconds = timeToSeconds(event.detected_at);

            if (seconds === null) return;

            var marker = document.createElement('div');

            marker.className = 'dayline-event';

            marker.style.left = (seconds / 86400 * 100) + '%';

            marker.title = objectBadge(event)
                + ' | ' + getClockTime(event.detected_at)
                + ' | клік — перемотка відео';

            marker.onclick = function () { seekToEvent(event); };

            dayline.appendChild(marker);

        });
    }

    /* ==========================================================
       ПЛЕЄР
       ========================================================== */

    function curVideo() {
        if (currentVideoIndex < 0 || currentVideoIndex >= videos.length) return null;
        return videos[currentVideoIndex];
    }
    function applySpeed() {
        if (speedSel) { var v = parseFloat(speedSel.value || '1'); if (!(v > 0)) v = 1; try { player.playbackRate = v; } catch (e) {} }
        if (loopBox) { try { player.loop = !!loopBox.checked; } catch (e) {} }
    }
    function playVideo(index, seekSeconds) {
        if (index < 0 || index >= videos.length) return;
        currentVideoIndex = index;
        retryCount = 0;
        var video = videos[index];
        playerTitle.textContent = (video.camera_name || ('Camera ' + video.camera_id)) + ' — ' + (video.filename || 'Відео');
        playerTime.textContent = getClockTime(video.started_at) + ' — ' + getClockTime(video.ended_at);
        hideOverlay();
        loadSource(video.url, seekSeconds, false);
        renderDayline();
    }
    function loadSource(src, seekSeconds, isRetry) {
        var token = ++loadToken;
        pendingSeek = (typeof seekSeconds === 'number') ? seekSeconds : null;
        if (!src) { showOverlay('Немає посилання', 'Сервер не повернув URL.', '⚠'); return; }
        if (!canPlayMp4()) { showOverlay('Браузер не підтримує MP4 (H.264)', 'Оновіть Chrome / Edge / Firefox.', '🎞'); return; }
        showBuffer(true);
        setStatus('Перевірка файлу…');
        fetch(src, { method: 'HEAD' }).then(function (r) {
            if (token !== loadToken) return;
            if (r.status === 404) { showBuffer(false); setStatus('Файл не знайдено (404)'); showOverlay('Файл не знайдено', 'AI-сервер ще записує файл або його видалено.', '📼'); return; }
            if (!r.ok && r.status !== 206) { showBuffer(false); showOverlay('Сервер відхилив запит (' + r.status + ')', 'Спробуйте інше відео.', '⚠'); return; }
            var len = r.headers.get('Content-Length') || r.headers.get('content-length');
            if (len !== null && Number(len) === 0) { showBuffer(false); showOverlay('Файл порожній', 'Запис іще триває. Зачекайте і натисніть Оновити.', '⏳'); return; }
            startPlayback(src, token, isRetry);
        }).catch(function () { if (token !== loadToken) return; startPlayback(src, token, isRetry); });
    }
    function startPlayback(src, token, isRetry) {
        showBuffer(true);
        setStatus('Завантаження відео…');
        player.setAttribute('data-src', src);
        var finalSrc = isRetry ? src + (src.indexOf('?') === -1 ? '?' : '&') + 't=' + Date.now() : src;
        try { player.pause(); } catch (e) {}
        player.removeAttribute('src');
        player.src = finalSrc;
        try { player.preload = 'auto'; } catch (e) {}
        applySpeed();
        player.load();
        var pr = null;
        try { pr = player.play(); } catch (e) {}
        if (pr && pr.catch) { pr.catch(function (err) { if (token !== loadToken) return; if (err && err.name === 'NotAllowedError') { showBuffer(false); setStatus('Натисніть ▶ для відтворення'); } }); }
    }
    function retryCurrent() {
        var v = curVideo();
        if (!v) return;
        retryCount++;
        hideOverlay();
        loadSource(v.url, Math.max(0, player.currentTime || 0), true);
        setStatus('Повторна спроба (' + retryCount + ')…');
    }

    /* Перемотка до події — головна фішка */

    function seekToEvent(event) {

        var t = timeToSeconds(event.detected_at);

        if (t === null) return;

        var found = -1;
        var offset = 0;

        for (var i = 0; i < videos.length; i++) {

            var vs = timeToSeconds(videos[i].started_at);

            if (vs === null) continue;

            var duration = Number(videos[i].duration || 0);
            var ve = timeToSeconds(videos[i].ended_at);

            if (!ve && duration > 0) ve = vs + duration;

            if (ve === null) ve = vs + 300;

            if (t >= vs && t <= ve) {
                found = i;
                offset = t - vs;
                break;
            }
        }

        if (found === -1) {

            setStatus('На ' + getClockTime(event.detected_at) + ' запису немає');

            return;
        }

        setStatus('Перемотка до ' + getClockTime(event.detected_at));

        playVideo(found, Math.max(0, offset - 2));
    }

    player.addEventListener('loadstart', function () { showBuffer(true); });
    player.addEventListener('waiting', function () { showBuffer(true); });
    player.addEventListener('stalled', function () { setStatus('Очікування даних…'); });
    player.addEventListener('canplay', function () { showBuffer(false); hideOverlay(); setStatus('Відтворення'); });
    player.addEventListener('playing', function () { showBuffer(false); hideOverlay(); setStatus('Відтворення'); });
    player.addEventListener('ended', function () {
        showBuffer(false);
        var auto = !autoplayBox || autoplayBox.checked;
        if (auto && currentVideoIndex + 1 < videos.length) playVideo(currentVideoIndex + 1);
        else setStatus('Завершено');
    });
    player.addEventListener('loadedmetadata', function () {
        if (pendingSeek !== null && isFinite(player.duration) && pendingSeek <= player.duration) {
            try { player.currentTime = pendingSeek; } catch (e) {}
        }
        pendingSeek = null;
    });
    player.addEventListener('timeupdate', function () {
        var v = curVideo();
        if (!v) return;
        playerTime.textContent = getClockTime(v.started_at) + ' — ' + getClockTime(v.ended_at) + ' · ▶ ' + formatTime(player.currentTime || 0);
    });
    player.addEventListener('error', function () {
        if (!loadToken) return;
        showBuffer(false);
        var code = player.error ? player.error.code : 0;
        var d = code === 4 ? 'Браузер не зміг декодувати файл: запис триває або кодек не H.264.'
            : code === 3 ? 'Файл пошкоджено під час запису.'
            : code === 2 ? 'Мережева помилка.'
            : 'Перевірте мережу та формат.';
        setStatus('Помилка відтворення (код ' + code + ')');
        showOverlay('Не вдалося відтворити відео', d + ' Спробуйте ще раз.', '🎞');
    });
    if (btnRetry) btnRetry.addEventListener('click', retryCurrent);
    if (btnNextOverlay) btnNextOverlay.addEventListener('click', function () { if (currentVideoIndex + 1 < videos.length) playVideo(currentVideoIndex + 1); });
    if (btnPrev) btnPrev.addEventListener('click', function () { if (currentVideoIndex > 0) playVideo(currentVideoIndex - 1); });
    if (btnNext) btnNext.addEventListener('click', function () { if (currentVideoIndex + 1 < videos.length) playVideo(currentVideoIndex + 1); });
    if (btnBack10) btnBack10.addEventListener('click', function () { try { player.currentTime = Math.max(0, (player.currentTime || 0) - 10); } catch (e) {} });
    if (btnFwd10) btnFwd10.addEventListener('click', function () { try { player.currentTime = (player.currentTime || 0) + 10; } catch (e) {} });
    if (speedSel) speedSel.addEventListener('change', applySpeed);
    if (loopBox) loopBox.addEventListener('change', applySpeed);
    if (btnPip) btnPip.addEventListener('click', function () { try { if (document.pictureInPictureElement) document.exitPictureInPicture(); else if (player.requestPictureInPicture) player.requestPictureInPicture(); } catch (e) {} });
    if (btnFull) btnFull.addEventListener('click', function () { try { var el = playerWrap || player; if (document.fullscreenElement) document.exitFullscreen(); else if (el.requestFullscreen) el.requestFullscreen(); else if (player.webkitEnterFullscreen) player.webkitEnterFullscreen(); } catch (e) {} });
    document.addEventListener('keydown', function (e) {
        var tag = (document.activeElement && document.activeElement.tagName) || '';
        if (tag === 'INPUT' || tag === 'SELECT' || tag === 'TEXTAREA') return;
        if (e.key === 'ArrowRight') { if (currentVideoIndex + 1 < videos.length) playVideo(currentVideoIndex + 1); }
        else if (e.key === 'ArrowLeft') { if (currentVideoIndex > 0) playVideo(currentVideoIndex - 1); }
        else if (e.key === ' ') { e.preventDefault(); try { if (player.paused) player.play(); else player.pause(); } catch (err) {} }
    });

    /* ---------- Автозавантаження при зміні фільтрів ---------- */

    if (cameraSelect) {
        cameraSelect.addEventListener('change', window.ArchiveLoad);
    }

    if (dateInput) {
        dateInput.addEventListener('change', window.ArchiveLoad);
    }

    /* ---------- Перший запуск ---------- */

    window.ArchiveLoad();

})();
