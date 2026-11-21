<?php

namespace App\Support;

final class ObjectIcon
{
    /**
     * Значок + українська назва для кожного класу YOLO.
     * Використовується у Blade, monitoring.js, archive.js.
     */
    public const MAP = [
        'person'   => ['icon' => '🧍', 'label' => 'Людина'],
        'car'      => ['icon' => '🚗', 'label' => 'Авто'],
        'truck'    => ['icon' => '🚚', 'label' => 'Вантажівка'],
        'bus'      => ['icon' => '🚌', 'label' => 'Автобус'],
        'bicycle'  => ['icon' => '🚲', 'label' => 'Велосипед'],
        'motorbike' => ['icon' => '🏍', 'label' => 'Мотоцикл'],
        'motorcycle' => ['icon' => '🏍', 'label' => 'Мотоцикл'],
        'dog'      => ['icon' => '🐕', 'label' => 'Собака'],
        'cat'      => ['icon' => '🐈', 'label' => 'Кіт'],
        'bird'     => ['icon' => '🐦', 'label' => 'Птах'],
    ];

    public const FALLBACK = ['icon' => '📦', 'label' => null];

    public static function for(?string $object): array
    {
        $key = strtolower(trim((string) $object));

        if (isset(self::MAP[$key])) {
            return self::MAP[$key];
        }

        return ['icon' => self::FALLBACK['icon'], 'label' => $object];
    }

    public static function icon(?string $object): string
    {
        return self::for($object)['icon'];
    }

    public static function label(?string $object): string
    {
        $meta = self::for($object);

        if (!empty($meta['label'])) {
            return $meta['label'];
        }

        $raw = trim((string) $object);

        return $raw !== '' ? ucfirst($raw) : 'Обʼєкт';
    }

    public static function badge(?string $object): string
    {
        $meta = self::for($object);

        if (!empty($meta['label'])) {
            return $meta['icon'] . ' ' . $meta['label'];
        }

        $raw = trim((string) $object);

        return $meta['icon'] . ' ' . ($raw !== '' ? ucfirst($raw) : 'Обʼєкт');
    }
}
