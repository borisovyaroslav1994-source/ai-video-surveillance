<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="icon" href="{{ asset('favicon.ico') }}">

    <title>Підтвердження пароля — AI Video Surveillance</title>

    <link rel="preconnect" href="https://fonts.bunny.net">
    <link href="https://fonts.bunny.net/css?family=inter:400,500,600,700,800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="{{ asset('assets/app.css') }}?v=1">
</head>
<body>

<div class="auth-page">

    <div class="auth-card">

        <h1 class="auth-title">Підтвердіть пароль</h1>

        <p class="auth-sub">
            Це захищена частина системи — введіть пароль ще раз
        </p>

        <form method="POST" action="{{ route('password.confirm') }}" class="auth-form">

            @csrf

            <div class="field">

                <label for="password">Пароль</label>

                <input id="password"
                       type="password"
                       name="password"
                       required
                       autocomplete="current-password"
                       class="input {{ $errors->has('password') ? 'invalid' : '' }}">

                @error('password')
                    <span class="field-error">{{ $message }}</span>
                @enderror

            </div>

            <button type="submit" class="btn btn-primary" style="width:100%;">
                Підтвердити
            </button>

        </form>

    </div>

</div>

</body>
</html>
