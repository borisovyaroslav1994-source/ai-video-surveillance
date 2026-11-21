/* Авто-приховування повідомлень */
(function () {
    document.querySelectorAll('[data-autohide]').forEach(function (el) {
        setTimeout(function () {
            el.classList.add('alert-hide');
            setTimeout(function () { el.remove(); }, 400);
        }, 5000);
    });

    document.querySelectorAll('.alert-close').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var el = btn.closest('.alert');
            if (el) {
                el.classList.add('alert-hide');
                setTimeout(function () { el.remove(); }, 400);
            }
        });
    });
})();

/* Мобільний сайдбар */
(function () {
    var shell = document.getElementById('appShell');
    var toggle = document.getElementById('sidebarToggle');
    var overlay = document.getElementById('sidebarOverlay');

    function close() { if (shell) shell.classList.remove('sidebar-open'); }

    if (toggle) toggle.addEventListener('click', function () {
        shell.classList.toggle('sidebar-open');
    });

    if (overlay) overlay.addEventListener('click', close);

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') close();
    });
})();

/* Підтвердження форм */
(function () {
    document.querySelectorAll('form[data-confirm]').forEach(function (form) {
        form.addEventListener('submit', function (e) {
            if (!window.confirm(form.getAttribute('data-confirm'))) {
                e.preventDefault();
            }
        });
    });
})();

/* Синхронізація range + number (поріг YOLO) */
(function () {
    var range = document.getElementById('confidenceRange');
    var number = document.getElementById('confidenceNumber');
    if (!range || !number) return;

    range.addEventListener('input', function () { number.value = range.value; });
    number.addEventListener('input', function () { range.value = number.value; });
})();

/* ==========================================================
   LIGHTBOX: перегляд фото подій у великому розмірі
   Працює для мініатюр .event-thumb / .monitor-event-thumb
   та img[data-lightbox]; делеговано — охоплює динамічно
   додані фото (моніторинг)
   ========================================================== */

(function () {
    var box = null;
    var imgEl = null;
    var capEl = null;
    var counterEl = null;
    var images = [];
    var current = 0;

    var SELECTOR =
        '.event-thumb img, .monitor-event-thumb img, ' +
        '[data-lightbox] img, img[data-lightbox]';

    function ensure() {
        if (box) return;

        box = document.createElement('div');
        box.className = 'lightbox';
        box.setAttribute('role', 'dialog');
        box.setAttribute('aria-modal', 'true');

        box.innerHTML =
            '<div class="lightbox-figure">' +
            '<img alt="">' +
            '<span class="lightbox-caption"></span>' +
            '<span class="lightbox-counter"></span>' +
            '</div>' +
            '<button type="button" class="lightbox-btn lightbox-close" aria-label="Закрити">&times;</button>' +
            '<button type="button" class="lightbox-btn lightbox-prev" aria-label="Попереднє фото">&#8249;</button>' +
            '<button type="button" class="lightbox-btn lightbox-next" aria-label="Наступне фото">&#8250;</button>';

        document.body.appendChild(box);

        imgEl = box.querySelector('.lightbox-figure img');
        capEl = box.querySelector('.lightbox-caption');
        counterEl = box.querySelector('.lightbox-counter');

        box.addEventListener('click', function (e) {
            if (e.target === box) close();
        });

        box.querySelector('.lightbox-close').addEventListener('click', close);
        box.querySelector('.lightbox-prev').addEventListener('click', prev);
        box.querySelector('.lightbox-next').addEventListener('click', next);
    }

    function collect() {
        images = Array.prototype.slice.call(
            document.querySelectorAll(SELECTOR)
        );
    }

    function show() {
        if (!images.length) return;

        var img = images[current];

        imgEl.setAttribute('src', img.getAttribute('src') || img.src);
        imgEl.setAttribute('alt', img.getAttribute('alt') || '');

        capEl.textContent = img.getAttribute('alt') || 'Фото події';

        counterEl.textContent = (current + 1) + ' / ' + images.length;

        box.classList.add('open');

        document.body.style.overflow = 'hidden';
    }

    function openFrom(source) {
        ensure();
        collect();

        var idx = images.indexOf(source);

        current = idx >= 0 ? idx : 0;

        show();
    }

    function close() {
        if (!box) return;

        box.classList.remove('open');

        document.body.style.overflow = '';

        setTimeout(function () {
            if (imgEl) imgEl.removeAttribute('src');
        }, 220);
    }

    function next() {
        if (!images.length) return;
        current = (current + 1) % images.length;
        show();
    }

    function prev() {
        if (!images.length) return;
        current = (current - 1 + images.length) % images.length;
        show();
    }

    /* Клік по мініатюрі — відкрити */
    document.addEventListener('click', function (e) {
        var el = e.target.closest
            ? e.target.closest(SELECTOR)
            : null;

        if (!el) return;

        e.preventDefault();
        openFrom(el);
    });

    /* Клавіатура */
    document.addEventListener('keydown', function (e) {
        if (!box || !box.classList.contains('open')) return;

        if (e.key === 'Escape') { close(); e.preventDefault(); }
        if (e.key === 'ArrowRight') { next(); e.preventDefault(); }
        if (e.key === 'ArrowLeft') { prev(); e.preventDefault(); }
    });
})();
