<?php

use Illuminate\Foundation\Inspiring;
use Illuminate\Support\Facades\Artisan;
use Illuminate\Support\Facades\Schedule;

Artisan::command('inspire', function () {
    $this->comment(Inspiring::quote());
})->purpose('Display an inspiring quote');

// Автоочищення архіву відео: щодня о 04:00.
// retention (діб) + квота (ГБ) беруться з panel_settings:
// archive_retention_days / archive_max_gb.
Schedule::command('videos:prune')->dailyAt('04:00');
