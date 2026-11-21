<div class="card" style="margin-bottom:18px;">

    <div class="card-head">

        <h3>Зміна пароля</h3>

        @if (session('status') === 'password-updated')
            <span class="card-hint" style="color:var(--success); font-weight:700;">
                ✓ Пароль оновлено
            </span>
        @endif

    </div>

    <div class="card-pad">

        <form method="post" action="{{ route('password.update') }}">

            @csrf
            @method('put')

            <div class="form-grid">

                <div class="field">

                    <label for="update_password_current_password">Поточний пароль</label>

                    <input id="update_password_current_password"
                           name="current_password"
                           type="password"
                           autocomplete="current-password"
                           class="input {{ $errors->updatePassword->has('current_password') ? 'invalid' : '' }}">

                    @error('current_password', 'updatePassword')
                        <span class="field-error">{{ $message }}</span>
                    @enderror

                </div>

                <div class="field">

                    <label for="update_password_password">Новий пароль</label>

                    <input id="update_password_password"
                           name="password"
                           type="password"
                           autocomplete="new-password"
                           class="input {{ $errors->updatePassword->has('password') ? 'invalid' : '' }}">

                    @error('password', 'updatePassword')
                        <span class="field-error">{{ $message }}</span>
                    @enderror

                </div>

                <div class="field span-2">

                    <label for="update_password_password_confirmation">
                        Підтвердження нового пароля
                    </label>

                    <input id="update_password_password_confirmation"
                           name="password_confirmation"
                           type="password"
                           autocomplete="new-password"
                           class="input {{ $errors->updatePassword->has('password_confirmation') ? 'invalid' : '' }}">

                    @error('password_confirmation', 'updatePassword')
                        <span class="field-error">{{ $message }}</span>
                    @enderror

                </div>

            </div>

            <div class="form-footer">

                <button type="submit" class="btn btn-primary">Оновити пароль</button>

            </div>

        </form>

    </div>

</div>
