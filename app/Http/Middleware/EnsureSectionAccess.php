<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

class EnsureSectionAccess
{
    /**
     * Перевірка доступу до розділу панелі.
     * Використання: ->middleware('section:cameras')
     */
    public function handle(Request $request, Closure $next, string $section): Response
    {
        $user = $request->user();

        if (!$user) {
            return redirect()->route('login');
        }

        if ($user->is_active === false) {
            auth()->logout();
            $request->session()->invalidate();
            $request->session()->regenerateToken();

            return redirect()
                ->route('login')
                ->withErrors(['email' => 'Обліковий запис деактивовано.']);
        }

        if (!$user->canAccess($section)) {
            abort(403, 'Немає доступу до розділу.');
        }

        return $next($request);
    }
}
