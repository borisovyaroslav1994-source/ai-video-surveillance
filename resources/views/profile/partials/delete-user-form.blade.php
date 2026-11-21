<div class="card" style="border-color:#fecaca;">

    <div class="card-head">

        <h3 style="color:var(--danger);">Видалення акаунта</h3>

    </div>

    <div class="card-pad">

        <p style="margin:0 0 16px; color:var(--muted); font-size:13.5px;">
            Після видалення акаунта всі його дані буде безповоротно втрачено.
            Перед видаленням збережіть усе потрібне.
        </p>

        <form method="post"
              action="{{ route('profile.destroy') }}"
              data-confirm="Ви впевнені, що хочете видалити акаунт? Дію неможливо скасувати.">

            @csrf
            @method('delete')

            <div class="form-grid">

                <div class="field">

                    <label for="delete_password">Пароль для підтвердження</label>

                    <input id="delete_password"
                           name="password"
                           type="password"
                           required
                           autocomplete="current-password"
                           class="input {{ $errors->userDeletion->has('password') ? 'invalid' : '' }}"
                           placeholder="Ваш поточний пароль">

                    @error('password', 'userDeletion')
                        <span class="field-error">{{ $message }}</span>
                    @enderror

                </div>

            </div>

            <div class="form-footer">

                <button type="submit" class="btn btn-danger">
                    Видалити акаунт
                </button>

            </div>

        </form>

    </div>

</div>
