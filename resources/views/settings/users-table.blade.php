<div class="card">
    <div class="card-head">
        <h3>Користувачі</h3>
        <span class="card-hint">{{ $users->count() }} у системі</span>
    </div>
    <div class="table-wrap">
        <table class="table">
            <thead>
                <tr>
                    <th>Користувач</th>
                    <th>Роль</th>
                    <th>Доступи</th>
                    <th>Статус</th>
                    <th style="text-align:right;">Дії</th>
                </tr>
            </thead>
            <tbody>
                @foreach ($users as $u)
                @php $eff = $u->effectivePermissions(); @endphp
                <tr>
                    <td>
                        <span class="cell-strong">{{ $u->name }}</span>
                        <span class="cell-sub">{{ $u->email }}</span>
                    </td>
                    <td><span class="badge badge-type">{{ $u->roleLabel() }}</span></td>
                    <td>
                        <div class="perm-badges">
                            @foreach ($sections as $section => $label)
                            <span class="mini-pill {{ !empty($eff[$section]) ? 'on' : 'off' }}">{{ $label }}</span>
                            @endforeach
                        </div>
                    </td>
                    <td>
                        <span class="mini-pill {{ $u->is_active ? 'on' : 'off' }}">
                            {{ $u->is_active ? 'активний' : 'вимкнений' }}
                        </span>
                    </td>
                    <td class="cell-actions">
                        <button type="button" class="btn-icon btn" title="Редагувати"
                                onclick="document.getElementById('edit-{{ $u->id }}').toggleAttribute('hidden')">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"
                                 stroke-linecap="round" stroke-linejoin="round">
                                <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>
                            </svg>
                        </button>
                        @if ($u->id !== $currentUser->id)
                        <form action="{{ route('settings.users.destroy', $u) }}"
                              method="POST" style="display:inline;"
                              data-confirm="Видалити користувача «{{ $u->name }}»?">
                            @csrf
                            @method('DELETE')
                            <button type="submit" class="btn-icon btn danger" title="Видалити">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"
                                     stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M3 6h18"/>
                                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/>
                                    <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                                </svg>
                            </button>
                        </form>
                        @endif
                    </td>
                </tr>
                <tr id="edit-{{ $u->id }}" hidden>
                    <td colspan="5" style="background:var(--surface-2);">
                        @include('settings.user-row', ['u' => $u, 'eff' => $eff])
                    </td>
                </tr>
                @endforeach
            </tbody>
        </table>
    </div>
</div>
