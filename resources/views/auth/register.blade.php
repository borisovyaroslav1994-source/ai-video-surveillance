<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="icon" href="{{ asset('favicon.ico') }}">

    <title>Реєстрація — AI Video Surveillance</title>

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

            <h1 class="auth-title">Створення акаунта</h1>

            <p class="auth-sub">Заповніть форму для реєстрації</p>

            <form method="POST" action="{{ route('register') }}" class="auth-form">

                @csrf

                <div class="field">

                    <label for="name">Ім'я</label>

                    <input id="name"
                           type="text"
                           name="name"
                           value="{{ old('name') }}"
                           required
                           autofocus
                           autocomplete="name"
                           class="input {{ $errors->has('name') ? 'invalid' : '' }}">

                    @error('name')
                        <span class="field-error">{{ $message }}</span>
                    @enderror

                </div>

                <div class="field">

                    <label for="email">Email адреса</label>

                    <input id="email"
                           type="email"
                           name="email"
                           value="{{ old('email') }}"
                           required
                           autocomplete="username"
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
                           autocomplete="new-password"
                           class="input {{ $errors->has('password') ? 'invalid' : '' }}">

                    @error('password')
                        <span class="field-error">{{ $message }}</span>
                    @enderror

                </div>

                <div class="field">

                    <label for="password_confirmation">Підтвердження пароля</label>

                    <input id="password_confirmation"
                           type="password"
                           name="password_confirmation"
                           required
                           autocomplete="new-password"
                           class="input">

                    @error('password_confirmation')
                        <span class="field-error">{{ $message }}</span>
                    @enderror

                </div>

                <button type="submit" class="btn btn-primary" style="width:100%; margin-top:6px;">
                    Зареєструватися
                </button>

            </form>

            <p class="auth-alt">
                Вже маєте акаунт?
                <a href="{{ route('login') }}">Увійти</a>
            </p>

        </div>

        <p class="auth-footer">© {{ date('Y') }} AI Video Surveillance · Дипломний проєкт</p>

    </div>

</div>

</body>
</html>
