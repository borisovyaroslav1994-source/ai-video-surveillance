@extends('layouts.panel')

@section('page_title', 'Налаштування')

@section('content')

<div class="page-header">
    <div>
        <h2>Налаштування</h2>
        <p>Параметри панелі та права доступу користувачів</p>
    </div>
</div>

<div class="tabs">
    <a href="{{ route('settings.index', ['tab' => 'panel']) }}"
       class="tab {{ $tab === 'panel' ? 'active' : '' }}">Панель</a>
    <a href="{{ route('settings.index', ['tab' => 'users']) }}"
       class="tab {{ $tab === 'users' ? 'active' : '' }}">Користувачі ({{ $users->count() }})</a>
</div>

@if ($tab === 'panel')
<form method="POST" action="{{ route('settings.panel.update') }}">
    @csrf
    @method('PUT')
    @foreach ($catalogue as $groupKey => $group)
    <div class="card" style="margin-bottom:18px;">
        <div class="card-head"><h3>{{ $group['label'] ?? $groupKey }}</h3></div>
        <div class="card-pad" style="display:flex; flex-direction:column; gap:16px;">
            @foreach ($group['items'] as $item)
            @php
                $k = $item['key'];
                $row = $stored->get($k);
                $cur = $row ? $row->value : ($item['default'] ?? '');
            @endphp
            <div class="field">
                <label for="set-{{ $k }}">{{ $item['label'] ?? $k }}</label>
                @if (($item['type'] ?? 'string') === 'integer')
                <input id="set-{{ $k }}" type="number" min="0"
                       name="settings[{{ $k }}]" value="{{ old('settings.'.$k, $cur) }}"
                       class="input" style="max-width:280px;">
                @else
                <input id="set-{{ $k }}" type="text"
                       name="settings[{{ $k }}]" value="{{ old('settings.'.$k, $cur) }}"
                       class="input">
                @endif
                @if (!empty($item['description']))
                <span class="field-hint">{{ $item['description'] }}</span>
                @endif
            </div>
            @endforeach
        </div>
    </div>
    @endforeach
    <button type="submit" class="btn btn-primary">Зберегти налаштування</button>
</form>
@else
@include('settings.users', ['users' => $users])
@endif

@endsection
