<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="csrf-token" content="{{ csrf_token() }}">
    <link rel="icon" href="{{ asset('favicon.ico') }}">

    <title>@yield('page_title', 'Огляд системи') — {{ \App\Models\PanelSetting::getValue('panel_name', 'AI VIDEO') }}</title>

    <link rel="preconnect" href="https://fonts.bunny.net">
    <link href="https://fonts.bunny.net/css?family=inter:400,500,600,700,800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="{{ asset('assets/app.css') }}?v=1">
</head>
<body>

@php
    $user = auth()->user();
    $userInitial = $user ? mb_strtoupper(mb_substr(trim($user->name) ?: 'U', 0, 1)) : 'U';
@endphp

<div class="app-shell" id="appShell">

    <!-- ==================== САЙДБАР ==================== -->
    <aside class="sidebar">

        <div class="sidebar-brand">
            <span class="brand-mark">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"
                     stroke-linecap="round" stroke-linejoin="round" width="22" height="22">
                    <path d="M15 10l4.55-2.28A1 1 0 0 1 21 8.62v6.76a1 1 0 0 1-1.45.9L15 14"/>
                    <rect x="3" y="6" width="12" height="12" rx="2"/>
                </svg>
            </span>
            <span>
                <span class="brand-name">{{ \App\Models\PanelSetting::getValue('panel_name', 'AI VIDEO') }}</span>
                <span class="brand-sub">{{ \App\Models\PanelSetting::getValue('panel_subtitle', 'Система відеонагляду') }}</span>
            </span>
        </div>

@php
    $perms = $user ? $user->effectivePermissions() : [];
@endphp

        <nav class="sidebar-nav">

            @if (($perms['dashboard'] ?? true))
            <a href="{{ route('dashboard') }}"
               class="nav-link {{ request()->routeIs('dashboard') ? 'active' : '' }}">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"
                     stroke-linecap="round" stroke-linejoin="round">
                    <path d="M3 10.5 12 3l9 7.5"/>
                    <path d="M5 9.5V21h14V9.5"/>
                    <path d="M9.5 21v-6h5v6"/>
                </svg>
                Головна
            </a>
            @endif

            @if (($perms['cameras'] ?? false))
            <a href="{{ route('cameras.index') }}"
               class="nav-link {{ request()->routeIs('cameras.*') ? 'active' : '' }}">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"
                     stroke-linecap="round" stroke-linejoin="round">
                    <path d="M15 10l4.55-2.28A1 1 0 0 1 21 8.62v6.76a1 1 0 0 1-1.45.9L15 14"/>
                    <rect x="3" y="6" width="12" height="12" rx="2"/>
                </svg>
                Камери
            </a>
            @endif

            @if (($perms['monitoring'] ?? false))
            <a href="{{ route('monitoring.index') }}"
               class="nav-link {{ request()->routeIs('monitoring.*') ? 'active' : '' }}">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"
                     stroke-linecap="round" stroke-linejoin="round">
                    <path d="M2 12h3l2-7 4 14 3-9 2 4h6"/>
                </svg>
                Моніторинг
            </a>
            @endif

            @if (($perms['events'] ?? false))
            <a href="{{ route('events.index') }}"
               class="nav-link {{ request()->routeIs('events.*') ? 'active' : '' }}">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"
                     stroke-linecap="round" stroke-linejoin="round">
                    <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/>
                    <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>
                </svg>
                Події AI
            </a>
            @endif

            @if (($perms['archive'] ?? false))
            <a href="{{ route('archive.index') }}"
               class="nav-link {{ request()->routeIs('archive.*') ? 'active' : '' }}">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"
                     stroke-linecap="round" stroke-linejoin="round">
                    <rect x="2" y="4" width="20" height="16" rx="2"/>
                    <path d="M10 9l5 3-5 3z"/>
                </svg>
                Відеоархів
            </a>
            @endif

            @if (($perms['settings'] ?? false))
            <a href="{{ route('settings.index') }}"
               class="nav-link {{ request()->routeIs('settings.*') ? 'active' : '' }}">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"
                     stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="3"/>
                    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1Z"/>
                </svg>
                Налаштування
            </a>
            @endif

        </nav>

        <div class="sidebar-user">
            <span class="user-avatar">{{ $userInitial }}</span>
            <span class="user-meta">
                <span class="user-name">{{ $user->name ?? 'Гість' }}</span>
                <span class="user-email">{{ $user->email ?? '' }}</span>
            </span>

            <form method="POST" action="{{ route('logout') }}">
                @csrf
                <button type="submit" class="logout-btn" title="Вийти">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"
                         stroke-linecap="round" stroke-linejoin="round">
                        <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                        <path d="m16 17 5-5-5-5"/>
                        <path d="M21 12H9"/>
                    </svg>
                </button>
            </form>
        </div>

    </aside>

    <div class="sidebar-overlay" id="sidebarOverlay"></div>

    <!-- ==================== КОНТЕНТ ==================== -->
    <div class="app-main">

        <header class="topbar">
            <button class="burger" id="sidebarToggle" type="button" aria-label="Меню">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                     stroke-linecap="round">
                    <path d="M4 6h16M4 12h16M4 18h16"/>
                </svg>
            </button>

            <h1>@yield('page_title', 'Огляд системи')</h1>

            <span class="topbar-date">{{ now()->format('d.m.Y · H:i') }}</span>
        </header>

        <main class="app-content">

            @if (session('success'))
                <div class="alert alert-success" data-autohide>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                         stroke-linecap="round" stroke-linejoin="round">
                        <path d="M22 11.1V12a10 10 0 1 1-5.9-9.1"/>
                        <path d="M22 4 12 14l-3-3"/>
                    </svg>
                    <span>{{ session('success') }}</span>
                    <button type="button" class="alert-close" aria-label="Закрити">&times;</button>
                </div>
            @endif

            @if (session('error'))
                <div class="alert alert-error">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                         stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="10"/>
                        <path d="M12 8v4M12 16h.01"/>
                    </svg>
                    <span>{{ session('error') }}</span>
                    <button type="button" class="alert-close" aria-label="Закрити">&times;</button>
                </div>
            @endif

            @if ($errors->any())
                <div class="alert alert-error">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                         stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="10"/>
                        <path d="M12 8v4M12 16h.01"/>
                    </svg>
                    <div>
                        <strong>Виправте помилки:</strong>
                        <ul class="alert-list">
                            @foreach ($errors->all() as $error)
                                <li>{{ $error }}</li>
                            @endforeach
                        </ul>
                    </div>
                    <button type="button" class="alert-close" aria-label="Закрити">&times;</button>
                </div>
            @endif

            @yield('content')

        </main>
    </div>
</div>

<script src="{{ asset('assets/app.js') }}?v=1"></script>
</body>
</html>
