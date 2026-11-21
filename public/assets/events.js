/* Журнал подій AI */
(function () {

    var newestId = parseInt(
        document.body.getAttribute('data-newest-event-id') || '0',
        10
    );

    var apiUrl = document.body.getAttribute('data-events-api-url');

    if (!newestId || !apiUrl) return;

    setInterval(function () {

        fetch(apiUrl + '?per_page=1')
            .then(function (r) { return r.json(); })
            .then(function (json) {

                var data = json && json.events && json.events.data;

                if (!data || !data.length) return;

                if (parseInt(data[0].id, 10) > newestId) {

                    var banner = document.getElementById('newEventsBanner');

                    if (banner) banner.style.display = 'flex';

                    newestId = parseInt(data[0].id, 10);
                }

            })
            .catch(function () {});

    }, 15000);

    /* Автозастосування фільтрів */
    var form = document.getElementById('eventsFilter');

    if (form) {

        form.querySelectorAll('select, input[type="date"]').forEach(function (el) {

            el.addEventListener('change', function () {
                form.submit();
            });

        });

    }

})();
