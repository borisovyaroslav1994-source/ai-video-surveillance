<div class="card" style="margin-bottom:18px;">
    <div class="card-head"><h3>Новий користувач</h3></div>
    <form method="POST" action="{{ route('settings.users.store') }}">
        @csrf
        <div class="card-pad form-grid">
            <div class="field">
                <label for="nu-name">Імʼя *</label>
                <input id="nu-name" type="text" name="name" value="{{ old('name') }}"
                       required class="input" placeholder="Оператор">
            </div>
            <div class="field">
                <label for="nu-email">Email *</label>
                <input id="nu-email" type="email" name="email" value="{{ old('email') }}"
                       required class="input" placeholder="operator@example.com">
            </div>
            <div class="field">
                <label for="nu-password">Пароль *</label>
                <input id="nu-password" type="password" name="password"
                       required class="input" placeholder="Мінімум 8 символів">
            </div>
            <div class="field">
                <label for="nu-password-conf">Підтвердження *</label>
                <input id="nu-password-conf" type="password" name="password_confirmation"
                       required class="input">
            </div>
            <div class="field">
                <label for="nu-role">Роль *</label>
                <select id="nu-role" name="role" class="input">
                    @foreach ($roles as $value => $label)
                    <option value="{{ $value }}" @selected(old('role', 'viewer') === $value)>
                        {{ $label }}
                    </option>
                    @endforeach
                </select>
            </div>
            <div class="field">
                <label>Статус</label>
                <label class="switch-card">
                    <span><span class="switch-title">Активний</span></span>
                    <span class="switch">
                        <input type="checkbox" name="is_active" value="1"
                               @checked(old('is_active', true))>
                        <span class="switch-track"></span>
                    </span>
                </label>
            </div>
            <div class="field span-2">
                <span class="field-label">Доступи до розділів</span>
                <div class="perm-grid">
                    @foreach ($sections as $section => $label)
                    <label class="perm-item">
                        <input type="checkbox" name="permissions[{{ $section }}]" value="1"
                               @checked($section === 'dashboard' || (bool) old('permissions.'.$section, in_array($section, ['monitoring', 'events', 'archive'])))>
                        <span>{{ $label }}</span>
                    </label>
                    @endforeach
                </div>
                <span class="field-hint">«Головна» доступна завжди. Адміністратор має все автоматично.</span>
            </div>
        </div>
        <div class="card-pad form-footer" style="border-top:1px solid var(--border);">
            <button type="submit" class="btn btn-primary">Створити користувача</button>
        </div>
    </form>
</div>
