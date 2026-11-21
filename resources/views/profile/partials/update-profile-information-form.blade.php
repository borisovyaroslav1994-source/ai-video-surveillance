<div class="card" style="margin-bottom:18px;">

    <div class="card-head">

        <h3>Інформація профілю</h3>

        @if (session('status') === 'profile-updated')
            <span class="card-hint" style="color:var(--success); font-weight:700;">
                ✓ Збережено
            </span>
        @endif

    </div>

    <div class="card-pad">

        <form method="POST" action="{{ route('profile.update') }}">

            @csrf
            @method('patch')

            <div class="form-grid">

                <div class="field">

                    <label for="name">Ім'я</label>

                    <input id="name"
                           type="text"
                           name="name"
                           value="{{ old('name', $user->name) }}"
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
                           value="{{ old('email', $user->email) }}"
                           required
                           autocomplete="username"
                           class="input {{ $errors->has('email') ? 'invalid' : '' }}">

                    @error('email')
                        <span class="field-error">{{ $message }}</span>
                    @enderror

                </div>

            </div>

            <div class="form-footer">

                <button type="submit" class="btn btn-primary">Зберегти</button>

            </div>

        </form>

        @if ($user instanceof \Illuminate\Contracts\Auth\MustVerifyEmail && ! $user->hasVerifiedEmail())

            <form id="send-verification" method="post" action="{{ route('verification.send') }}">
                @csrf
            </form>

            <p style="margin:0; color:var(--warning); font-size:13px;">

                ⚠ Ваш email не підтверджено.

                <button form="send-verification" type="submit"
                        style="background:none; border:0; color:var(--primary); cursor:pointer; font:inherit; padding:0;">
                    Надіслати лист ще раз
                </button>

            </p>

            @if (session('status') === 'verification-link-sent')
                <p style="margin:8px 0 0; color:var(--success); font-size:13px;">
                    Нове посилання надіслано на вашу адресу.
                </p>
            @endif

        @endif

    </div>

</div>
