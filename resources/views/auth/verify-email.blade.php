<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="icon" href="{{ asset('favicon.ico') }}">

    <title>Підтвердження email — AI Video Surveillance</title>

    <link rel="preconnect" href="https://fonts.bunny.net">
    <link href="https://fonts.bunny.net/css?family=inter:400,500,600,700,800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="{{ asset('assets/app.css') }}?v=1">
</head>
<body>

<div class="auth-page">

    <div class="auth-card">

        <h1 class="auth-title">Підтвердіть email</h1>

        <p class="auth-sub">
            Дякуємо за реєстрацію! Перейдіть за посиланням із листа,
            яке ми надіслали на вашу адресу.
        </p>

        @if (session('status') == 'verification-link-sent')
            <div class="alert alert-success">
                <span>Нове посилання для підтвердження надіслано.</span>
            </div>
        @endif

        <form method="POST" action="{{ route('verification.send') }}">

            @csrf

            <button type="submit" class="btn btn-primary" style="width:100%;">
                Надіслати лист ще раз
            </button>

        </form>

        <form method="POST" action="{{ route('logout') }}" style="margin-top:10px;">

            @csrf

            <button type="submit" class="btn btn-ghost" style="width:100%;">
                Вийти з акаунта
            </button>

        </form>

    </div>

</div>

</body>
</html>
