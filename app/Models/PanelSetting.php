<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class PanelSetting extends Model
{
    protected $table = 'panel_settings';

    protected $fillable = [
        'group',
        'key',
        'value',
        'type',
        'label',
        'description',
    ];

    /**
     * Каталог налаштувань панелі за групами.
     *
     * type: string | integer | boolean | json
     */
    public static function catalogue(): array
    {
        return [
            'general' => [
                'label' => 'Загальне',
                'items' => [
                    [
                        'key' => 'panel_name',
                        'label' => 'Назва панелі',
                        'type' => 'string',
                        'default' => 'AI VIDEO',
                        'description' => 'Показується в сайдбарі та заголовках.',
                    ],
                    [
                        'key' => 'panel_subtitle',
                        'label' => 'Підзаголовок',
                        'type' => 'string',
                        'default' => 'Система відеонагляду',
                        'description' => 'Малий текст під назвою панелі.',
                    ],
                    [
                        'key' => 'items_per_page_events',
                        'label' => 'Подій на сторінці',
                        'type' => 'integer',
                        'default' => '24',
                        'description' => 'Значення за замовчуванням для журналу подій (6–96).',
                    ],
                ],
            ],
            'ai' => [
                'label' => 'AI-сервер',
                'items' => [
                    [
                        'key' => 'ai_api_url',
                        'label' => 'API камер',
                        'type' => 'string',
                        'default' => 'http://diplom.local/api/cameras',
                        'description' => 'Звідки Python-сервер тягне список камер.',
                    ],
                    [
                        'key' => 'ai_events_api_url',
                        'label' => 'API подій',
                        'type' => 'string',
                        'default' => 'http://diplom.local/api/events',
                        'description' => 'Куди Python-сервер надсилає події AI.',
                    ],
                    [
                        'key' => 'default_confidence',
                        'label' => 'Поріг YOLO за замовчуванням',
                        'type' => 'string',
                        'default' => '0.5',
                        'description' => 'Підставляється у форму нової камери (0–1).',
                    ],
                ],
            ],
            'archive' => [
                'label' => 'Архів',
                'items' => [
                    [
                        'key' => 'segment_seconds',
                        'label' => 'Довжина сегмента (сек)',
                        'type' => 'integer',
                        'default' => '300',
                        'description' => 'Довжина одного MP4-файлу. Python підхоплює при наступному сегменті (до 5 хв затримки).',
                    ],
                    [
                        'key' => 'transcode_crf',
                        'label' => 'Якість стиснення (CRF)',
                        'type' => 'integer',
                        'default' => '28',
                        'description' => 'CRF libx264 для фонового пережаття (18–32). Менше = якісніше і більше місця.',
                    ],
                    [
                        'key' => 'archive_retention_days',
                        'label' => 'Зберігати архів (діб)',
                        'type' => 'integer',
                        'default' => '30',
                        'description' => 'Скільки діб тримати записи. Щодня о 04:00 команда videos:prune видаляє старіше.',
                    ],
                    [
                        'key' => 'archive_max_gb',
                        'label' => 'Квота архіву (ГБ)',
                        'type' => 'integer',
                        'default' => '0',
                        'description' => 'Макс. сумарний розмір архіву в ГБ. 0 = без квоти. Якщо перевищено — videos:prune ріже найстаріше.',
                    ],
                ],
            ],
        ];
    }

    /**
     * Значення налаштування з урахуванням БД, інакше default з каталогу.
     */
    public static function getValue(string $key, mixed $default = null): mixed
    {
        $row = static::where('key', $key)->first();

        if ($row && $row->value !== null) {
            return $row->value;
        }

        foreach (static::catalogue() as $group) {
            foreach ($group['items'] as $item) {
                if ($item['key'] === $key) {
                    return $item['default'] ?? $default;
                }
            }
        }

        return $default;
    }

    public static function castValue(string $type, mixed $value): mixed
    {
        return match ($type) {
            'boolean' => in_array($value, [1, '1', true, 'true', 'on', 'yes'], true),
            'integer' => (int) $value,
            default => (string) ($value ?? ''),
        };
    }

    public function getTypedValueAttribute(): mixed
    {
        return static::castValue($this->type, $this->value);
    }
}
