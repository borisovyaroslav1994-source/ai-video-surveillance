<div class="edit-user-grid">
    <form method="POST" action="{{ route('settings.users.update', $u) }}">
        @csrf
        @method('PUT')
        <div class="form-grid">
            <div class="field">
                <label>Імʼя</label>
                <input type="text" name="name" value="{{ $u->name }}" class="input" required>
            </div>
            <div class="field">
                <label>Роль</label>
                <select name="role" class="input" @disabled($u->id === $currentUser->id)>
                    @foreach ($roles as $value => $label)
                    <option value="{{ $value }}" @selected($u->role === $value)>{{ $label }}</option>
                    @endforeach
                </select>
            </div>
            <div class="field span-2">
                <span class="field-label">Доступи</span>
                <div class="perm-grid">
                    @foreach ($sections as $section => $label)
                    <label class="perm-item">
                        <input type="checkbox" name="permissions[{{ $section }}]" value="1"
                               @checked(!empty($eff[$section]))
                               @disabled($section === 'dashboard' || $u->role === 'admin' || $u->id === $currentUser->id)>
                        <span>{{ $label }}</span>
                    </label>
                    @endforeach
                </div>
            </div>
            <div class="field">
                <label class="switch-card">
                    <span><span class="switch-title">Активний</span></span>
                    <span class="switch">
                        <input type="checkbox" name="is_active" value="1"
                               @checked($u->is_active)
                               @disabled($u->id === $currentUser->id)>
                        <span class="switch-track"></span>
                    </span>
                </label>
            </div>
        </div>
        <div style="margin-top:12px;">
            <button type="submit" class="btn btn-primary btn-sm">Зберегти</button>
        </div>
    </form>
    <form method="POST" action="{{ route('settings.users.password', $u) }}">
        @csrf
        @method('PUT')
        <div class="form-grid">
            <div class="field">
                <label>Новий пароль</label>
                <input type="password" name="password" class="input" required placeholder="Мінімум 8 символів">
            </div>
            <div class="field">
                <label>Підтвердження</label>
                <input type="password" name="password_confirmation" class="input" required>
            </div>
        </div>
        <div style="margin-top:12px;">
            <button type="submit" class="btn btn-outline btn-sm">Змінити пароль</button>
        </div>
    </form>
</div>
