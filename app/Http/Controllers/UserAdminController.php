<?php

namespace App\Http\Controllers;

use App\Models\User;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Hash;
use Illuminate\Validation\Rule;

class UserAdminController extends Controller
{
    public function store(Request $request): RedirectResponse
    {
        $validated = $request->validate([
            'name' => ['required', 'string', 'max:255'],
            'email' => ['required', 'string', 'lowercase', 'email', 'max:255', 'unique:users,email'],
            'password' => ['required', 'string', 'min:8', 'confirmed'],
            'role' => ['required', Rule::in(array_keys(User::ROLES))],
        ]);

        User::create([
            'name' => $validated['name'],
            'email' => $validated['email'],
            'password' => Hash::make($validated['password']),
            'role' => $validated['role'],
            'permissions' => $this->permissionsFromRequest($request, $validated['role']),
            'is_active' => $request->boolean('is_active', true),
        ]);

        return redirect()
            ->route('settings.index', ['tab' => 'users'])
            ->with('success', 'Користувача створено.');
    }

    public function update(Request $request, User $user): RedirectResponse
    {
        $validated = $request->validate([
            'name' => ['required', 'string', 'max:255'],
            'role' => ['required', Rule::in(array_keys(User::ROLES))],
        ]);

        if ($user->id === $request->user()->id) {
            $validated['role'] = $user->role;
        } elseif ($user->role === 'admin' && $validated['role'] !== 'admin') {
            $left = User::where('role', 'admin')->where('id', '!=', $user->id)->count();
            if ($left < 1) {
                return redirect()
                    ->route('settings.index', ['tab' => 'users'])
                    ->with('error', 'Не можна зняти роль з останнього адміністратора.');
            }
        }

        $isActive = $user->id === $request->user()->id
            ? true
            : $request->boolean('is_active', true);

        $user->update([
            'name' => $validated['name'],
            'role' => $validated['role'],
            'permissions' => $this->permissionsFromRequest($request, $validated['role']),
            'is_active' => $isActive,
        ]);

        return redirect()
            ->route('settings.index', ['tab' => 'users'])
            ->with('success', 'Права користувача оновлено.');
    }

    public function password(Request $request, User $user): RedirectResponse
    {
        $validated = $request->validate([
            'password' => ['required', 'string', 'min:8', 'confirmed'],
        ]);

        $user->update(['password' => Hash::make($validated['password'])]);

        return redirect()
            ->route('settings.index', ['tab' => 'users'])
            ->with('success', 'Пароль оновлено.');
    }

    public function destroy(Request $request, User $user): RedirectResponse
    {
        if ($user->id === $request->user()->id) {
            return redirect()
                ->route('settings.index', ['tab' => 'users'])
                ->with('error', 'Не можна видалити самого себе.');
        }

        if ($user->role === 'admin' && User::where('role', 'admin')->count() <= 1) {
            return redirect()
                ->route('settings.index', ['tab' => 'users'])
                ->with('error', 'Не можна видалити останнього адміністратора.');
        }

        $user->delete();

        return redirect()
            ->route('settings.index', ['tab' => 'users'])
            ->with('success', 'Користувача видалено.');
    }

    private function permissionsFromRequest(Request $request, string $role): array
    {
        if ($role === 'admin') {
            return User::defaultPermissionsFor('admin');
        }

        $out = [];

        foreach (User::SECTIONS as $section => $label) {
            $out[$section] = $request->boolean('permissions.'.$section, false);
        }

        $out['dashboard'] = true;

        return $out;
    }
}
