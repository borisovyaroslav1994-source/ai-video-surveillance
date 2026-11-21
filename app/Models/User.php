<?php

namespace App\Models;

// use Illuminate\Contracts\Auth\MustVerifyEmail;
use Database\Factories\UserFactory;
use Illuminate\Database\Eloquent\Attributes\Fillable;
use Illuminate\Database\Eloquent\Attributes\Hidden;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Foundation\Auth\User as Authenticatable;
use Illuminate\Notifications\Notifiable;

#[Fillable(['name', 'email', 'password', 'role', 'permissions', 'is_active'])]
#[Hidden(['password', 'remember_token'])]
class User extends Authenticatable
{
    /** @use HasFactory<UserFactory> */
    use HasFactory, Notifiable;

    public const ROLES = [
        'admin' => 'Адміністратор',
        'operator' => 'Оператор',
        'viewer' => 'Переглядач',
    ];

    /**
     * Розділи панелі, якими можна керувати правами.
     */
    public const SECTIONS = [
        'dashboard' => 'Головна',
        'cameras' => 'Камери',
        'monitoring' => 'Моніторинг',
        'events' => 'Події AI',
        'archive' => 'Відеоархів',
        'users' => 'Користувачі',
        'settings' => 'Налаштування',
    ];

    /**
     * Get the attributes that should be cast.
     *
     * @return array<string, string>
     */
    protected function casts(): array
    {
        return [
            'email_verified_at' => 'datetime',
            'password' => 'hashed',
            'permissions' => 'array',
            'is_active' => 'boolean',
        ];
    }

    public function roleLabel(): string
    {
        return self::ROLES[$this->role] ?? (string) $this->role;
    }

    /**
     * Права за замовчуванням для ролі (якщо permissions не задано явно).
     */
    public static function defaultPermissionsFor(string $role): array
    {
        return match ($role) {
            'admin' => [
                'dashboard' => true,
                'cameras' => true,
                'monitoring' => true,
                'events' => true,
                'archive' => true,
                'users' => true,
                'settings' => true,
            ],
            'operator' => [
                'dashboard' => true,
                'cameras' => true,
                'monitoring' => true,
                'events' => true,
                'archive' => true,
                'users' => false,
                'settings' => false,
            ],
            default => [
                'dashboard' => true,
                'cameras' => false,
                'monitoring' => true,
                'events' => true,
                'archive' => true,
                'users' => false,
                'settings' => false,
            ],
        };
    }

    /**
     * Ефективні права користувача: роль за замовчуванням + явні перевизначення.
     */
    public function effectivePermissions(): array
    {
        $defaults = self::defaultPermissionsFor((string) $this->role);
        $custom = is_array($this->permissions) ? $this->permissions : [];

        foreach (self::SECTIONS as $section => $label) {
            if (array_key_exists($section, $custom)) {
                $defaults[$section] = (bool) $custom[$section];
            }
        }

        // Адмін завжди має все.
        if ($this->role === 'admin') {
            foreach ($defaults as $section => $allowed) {
                $defaults[$section] = true;
            }
        }

        return $defaults;
    }

    public function canAccess(string $section): bool
    {
        if ($this->role === 'admin') {
            return true;
        }

        return (bool) ($this->effectivePermissions()[$section] ?? false);
    }

    public function isAdmin(): bool
    {
        return $this->role === 'admin';
    }
}

