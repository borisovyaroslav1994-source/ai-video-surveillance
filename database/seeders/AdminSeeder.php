<?php

namespace Database\Seeders;

use App\Models\User;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\Hash;

class AdminSeeder extends Seeder
{
    /**
     * Перший адміністратор: створюється тільки якщо адмінів ще немає.
     */
    public function run(): void
    {
        if (User::where('role', 'admin')->exists()) {
            $this->command->info('Адміністратор вже існує — пропуск.');

            return;
        }

        User::create([
            'name' => 'Адміністратор',
            'email' => 'admin@example.com',
            'password' => Hash::make('password'),
            'role' => 'admin',
            'permissions' => User::defaultPermissionsFor('admin'),
            'is_active' => true,
            'email_verified_at' => now(),
        ]);

        $this->command->info('Створено admin@example.com / password');
    }
}
