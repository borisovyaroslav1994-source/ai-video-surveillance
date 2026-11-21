<?php

namespace App\Console\Commands;

use App\Models\PanelSetting;
use App\Models\Video;
use Illuminate\Console\Command;
use Illuminate\Support\Facades\Storage;

class PruneVideos extends Command
{
    /**
     * Видаляє старі відео за retention + тримає квоту диска.
     *
     * Напр: archive_retention_days=7, max_gb=50:
     *   1. видаляє все старше 7 діб,
     *   2. якщо все одно > 50 ГБ — ріже найстаріше.
     */
    protected $signature = 'videos:prune
        {--retention= : скільки діб тримати (за замовчуванням з panel_settings)}
        {--max-gb= : квота диска в ГБ (0 = без квоти)}';

    protected $description = 'Автоочищення архіву відео: retention + квота диска';

    public function handle(): int
    {
        $retentionOpt = $this->option('retention');
        $maxGbOpt = $this->option('max-gb');

        $retentionDays = $retentionOpt !== null && $retentionOpt !== ''
            ? max(1, (int) $retentionOpt)
            : max(1, (int) PanelSetting::getValue('archive_retention_days', 30));

        $maxGb = $maxGbOpt !== null && $maxGbOpt !== ''
            ? max(0, (int) $maxGbOpt)
            : max(0, (int) PanelSetting::getValue('archive_max_gb', 0));

        $deletedByRetention = $this->pruneByRetention($retentionDays);
        $deletedByQuota = $maxGb > 0 ? $this->pruneByQuota($maxGb) : 0;

        $total = $deletedByRetention + $deletedByQuota;

        $this->info(
            "Prune готово: retention({$retentionDays} діб)={$deletedByRetention}, "
            . "квота({$maxGb} ГБ)={$deletedByQuota}, разом={$total}"
        );

        return self::SUCCESS;
    }

    /**
     * Крок 1: все старше retention — видалити (файл + рядок БД).
     */
    protected function pruneByRetention(int $days): int
    {
        $cutoff = now()->subDays($days);

        $videos = Video::query()
            ->where('started_at', '<', $cutoff)
            ->orderBy('started_at')
            ->limit(2000)
            ->get();

        $deleted = 0;

        foreach ($videos as $video) {
            $this->deleteVideo($video);
            $deleted++;
        }

        return $deleted;
    }

    /**
     * Крок 2: якщо сума size в БД перевищує квоту —
     * ріжемо найстаріші, поки не вліземо.
     */
    protected function pruneByQuota(int $maxGb): int
    {
        $maxBytes = $maxGb * 1024 * 1024 * 1024;

        $total = (int) Video::sum('size');

        if ($total <= $maxBytes) {
            return 0;
        }

        $videos = Video::query()
            ->orderBy('started_at')
            ->limit(2000)
            ->get();

        $deleted = 0;

        foreach ($videos as $video) {
            if ($total <= $maxBytes) {
                break;
            }

            $total -= (int) ($video->size ?? 0);

            $this->deleteVideo($video);
            $deleted++;
        }

        return $deleted;
    }

    protected function deleteVideo(Video $video): void
    {
        try {
            if (
                $video->path
                && Storage::disk('public')->exists($video->path)
            ) {
                Storage::disk('public')->delete($video->path);
            }
        } catch (\Throwable $e) {
            $this->warn(
                "Не вдалося видалити файл {$video->path}: {$e->getMessage()}"
            );
        }

        try {
            $video->delete();
        } catch (\Throwable $e) {
            $this->warn(
                "Не вдалося видалити запис video#{$video->id}: {$e->getMessage()}"
            );
        }
    }
}
