<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="icon" href="{{ asset('favicon.ico') }}">

    <title>Вхід — AI Video Surveillance</title>

    <link rel="preconnect" href="https://fonts.bunny.net">
    <link href="https://fonts.bunny.net/css?family=inter:400,500,600,700,800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="{{ asset('assets/app.css') }}?v=1">
</head>
<body>

<div class="auth-page">

    <div>

        <div class="auth-card">

            <div class="auth-brand">

                <span class="brand-mark">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"
                         stroke-linecap="round" stroke-linejoin="round" width="22" height="22">
                        <path d="M15 10l4.55-2.28A1 1 0 0 1 21 8.62v6.76a1 1 0 0 1-1.45.9L15 14"/>
                        <rect x="3" y="6" width="12" height="12" rx="2"/>
                    </svg>
                </span>

                <span>
                    <span class="brand-name" style="color:var(--text);">AI VIDEO</span>
                    <span class="brand-sub">Система спостереження</span>
                </span>

            </div>

            <h1 class="auth-title">Вхід до системи</h1>

            <p class="auth-sub">Введіть облікові дані для продовження</p>

            @if (session('status'))
                <div class="alert alert-success">
                    <span>{{ session('status') }}</span>
                </div>
            @endif

            <form method="POST" action="{{ route('login') }}" class="auth-form">

                @csrf

                <div class="field">

                    <label for="email">Email адреса</label>

                    <input id="email"
                           type="email"
                           name="email"
                           value="{{ old('email') }}"
                           required
                           autofocus
                           autocomplete="username"
                           placeholder="admin@example.com"
                           class="input {{ $errors->has('email') ? 'invalid' : '' }}">

                    @error('email')
                        <span class="field-error">{{ $message }}</span>
                    @enderror

                </div>

                <div class="field">

                    <label for="password">Пароль</label>

                    <input id="password"
                           type="password"
                           name="password"
                           required
                           autocomplete="current-password"
                           placeholder="••••••••"
                           class="input {{ $errors->has('password') ? 'invalid' : '' }}">

                    @error('password')
                        <span class="field-error">{{ $message }}</span>
                    @enderror

                </div>

                <div class="auth-row">

                    <label class="switch">
                        <input type="checkbox" name="remember">
                        <span class="switch-track"></span>
                        <span class="switch-text">Запам'ятати мене</span>
                    </label>

                    @if (Route::has('password.request'))
                        <a href="{{ route('password.request') }}">Забули пароль?</a>
                    @endif

                </div>

                <button type="submit" class="btn btn-primary" style="width:100%;">
                    Увійти
                </button>

            </form>
        </div>

        <p class="auth-footer">© {{ date('Y') }} AI Video Surveillance · Дипломний проєкт</p>

    </div>

</div>

</body>
</html>
