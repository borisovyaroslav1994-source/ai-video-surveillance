<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="icon" href="{{ asset('favicon.ico') }}">

    <title>Новий пароль — AI Video Surveillance</title>

    <link rel="preconnect" href="https://fonts.bunny.net">
    <link href="https://fonts.bunny.net/css?family=inter:400,500,600,700,800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="{{ asset('assets/app.css') }}?v=1">
</head>
<body>

<div class="auth-page">

    <div class="auth-card">

        <h1 class="auth-title">Новий пароль</h1>

        <p class="auth-sub">Придумайте новий пароль для входу</p>

        <form method="POST" action="{{ route('password.store') }}" class="auth-form">

            @csrf

            <input type="hidden" name="token" value="{{ $request->route('token') }}">

            <div class="field">

                <label for="email">Email адреса</label>

                <input id="email"
                       type="email"
                       name="email"
                       value="{{ old('email', $request->email) }}"
                       required
                       autofocus
                       class="input {{ $errors->has('email') ? 'invalid' : '' }}">

                @error('email')
                    <span class="field-error">{{ $message }}</span>
                @enderror

            </div>

            <div class="field">

                <label for="password">Новий пароль</label>

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

            </div>

            <button type="submit" class="btn btn-primary" style="width:100%;">
                Змінити пароль
            </button>

        </form>

        <p class="auth-alt">
            <a href="{{ route('login') }}">← Повернутися до входу</a>
        </p>

    </div>

</div>

</body>
</html>
