<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="icon" href="{{ asset('favicon.ico') }}">

    <title>Відновлення пароля — AI Video Surveillance</title>

    <link rel="preconnect" href="https://fonts.bunny.net">
    <link href="https://fonts.bunny.net/css?family=inter:400,500,600,700,800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="{{ asset('assets/app.css') }}?v=1">
</head>
<body>

<div class="auth-page">

    <div class="auth-card">

        <h1 class="auth-title">Відновлення пароля</h1>

        <p class="auth-sub">
            Вкажіть email — ми надішлемо посилання для зміни пароля
        </p>

        @if (session('status'))
            <div class="alert alert-success">
                <span>{{ session('status') }}</span>
            </div>
        @endif

        <form method="POST" action="{{ route('password.email') }}" class="auth-form">

            @csrf

            <div class="field">

                <label for="email">Email адреса</label>

                <input id="email"
                       type="email"
                       name="email"
                       value="{{ old('email') }}"
                       required
                       autofocus
                       class="input {{ $errors->has('email') ? 'invalid' : '' }}">

                @error('email')
                    <span class="field-error">{{ $message }}</span>
                @enderror

            </div>

            <button type="submit" class="btn btn-primary" style="width:100%;">
                Надіслати посилання
            </button>

        </form>

        <p class="auth-alt">
            <a href="{{ route('login') }}">← Повернутися до входу</a>
        </p>

    </div>

</div>

</body>
</html>
