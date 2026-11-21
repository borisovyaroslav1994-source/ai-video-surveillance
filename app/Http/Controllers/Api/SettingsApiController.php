<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\PanelSetting;

class SettingsApiController extends Controller
{
    /**
     * ========================================================
     * НАЛАШТУВАННЯ RECORDER ДЛЯ PYTHON
     *
     * GET /api/recorder-settings
     *
     * Єдине джерело правди для ai_server: довжина сегмента,
     * даунскейл, CRF/preset. Python тягне раз на ~60 сек,
     * при недоступності API працює на дефолтах.
     * ========================================================
     */
    public function recorder()
    {
        $int = static function (string $key, int $default, int $min, int $max): int {
            try {
                $value = (int) PanelSetting::getValue($key, $default);
            } catch (\Throwable) {
                $value = $default;
            }

            // 0 = "вимкнено" (для розмірів), тому min застосовуємо
            // тільки до ненульових значень.
            if ($value === 0 && $min === 0) {
                return 0;
            }

            return max($min, min($max, $value));
        };

        $preset = 'veryfast';

        try {
            $raw = (string) PanelSetting::getValue('transcode_preset', 'veryfast');
            $raw = strtolower(trim($raw));

            $allowed = [
                'ultrafast',
                'superfast',
                'veryfast',
                'faster',
                'fast',
                'medium',
                'slow',
                'slower',
                'veryslow',
            ];

            if (in_array($raw, $allowed, true)) {
                $preset = $raw;
            }
        } catch (\Throwable) {
            $preset = 'veryfast';
        }

        try {
            $defaultConfidence = (float) PanelSetting::getValue('default_confidence', 0.5);
            $defaultConfidence = max(0.0, min(1.0, $defaultConfidence));
        } catch (\Throwable) {
            $defaultConfidence = 0.5;
        }

        return response()->json([
            'success' => true,
            'settings' => [
                'segment_seconds' => $int('segment_seconds', 300, 30, 3600),
                'record_max_width' => $int('record_max_width', 1280, 0, 3840),
                'record_max_height' => $int('record_max_height', 720, 0, 2160),
                'transcode_crf' => $int('transcode_crf', 28, 18, 32),
                'transcode_preset' => $preset,
                'default_confidence' => $defaultConfidence,
            ],
        ]);
    }
}
