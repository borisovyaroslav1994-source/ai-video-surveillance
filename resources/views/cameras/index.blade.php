@extends('layouts.panel')

@section('page_title', 'Камери')

@section('content')

<div class="page-header">

    <div>
        <h2>Камери</h2>
        <p>
            Керування джерелами відео: {{ $cameras->count() }}
            у системі, {{ $cameras->where('status', 'online')->count() }} онлайн
        </p>
    </div>

    <div class="page-actions">

        <a href="{{ route('cameras.create') }}" class="btn btn-primary">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                 stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 5v14M5 12h14"/>
            </svg>
            Додати камеру
        </a>

    </div>

</div>

<div class="card">

    @if ($cameras->isEmpty())

        <div class="empty-state">

            <span class="empty-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"
                     stroke-linecap="round" stroke-linejoin="round">
                    <path d="M15 10l4.55-2.28A1 1 0 0 1 21 8.62v6.76a1 1 0 0 1-1.45.9L15 14"/>
                    <rect x="3" y="6" width="12" height="12" rx="2"/>
                </svg>
            </span>

            <h4>Камер ще не додано</h4>

            <p>
                Додайте USB-, RTSP- або HTTP-камеру, щоб Python AI-сервер
                міг підключитися до неї та розпізнавати об'єкти.
            </p>

            <a href="{{ route('cameras.create') }}" class="btn btn-primary">
                Додати першу камеру
            </a>

        </div>

    @else

        <div class="table-wrap">

            <table class="table">

                <thead>

                    <tr>
                        <th>Камера</th>
                        <th>Тип</th>
                        <th>Джерело</th>
                        <th>Статус</th>
                        <th>AI</th>
                        <th>Запис</th>
                        <th>Поріг</th>
                        <th style="text-align:right;">Дії</th>
                    </tr>

                </thead>

                <tbody>

                    @foreach ($cameras as $camera)

                        <tr>

                            <td>
                                <span class="cell-strong">{{ $camera->name }}</span>
                                <span class="cell-sub">
                                    {{ $camera->location ?? 'Без розташування' }}
                                </span>
                            </td>

                            <td>
                                <span class="badge badge-type">
                                    {{ strtoupper($camera->type) }}
                                </span>
                            </td>

                            <td>
                                <span class="cell-code" title="{{ $camera->source }}">
                                    {{ $camera->source }}
                                </span>
                            </td>

                            <td>
                                <span class="badge {{ $camera->status === 'online' ? 'badge-online' : ($camera->status === 'error' ? 'badge-error' : 'badge-offline') }}">
                                    <span class="dot"></span>
                                    {{ strtoupper($camera->status) }}
                                </span>
                            </td>

                            <td>
                                <span class="mini-pill {{ $camera->ai_enabled ? 'on' : 'off' }}">
                                    {{ $camera->ai_enabled ? '✓' : '—' }}
                                </span>
                            </td>

                            <td>
                                <span class="mini-pill {{ $camera->recording_enabled ? 'on' : 'off' }}">
                                    {{ $camera->recording_enabled ? '✓' : '—' }}
                                </span>
                            </td>

                            <td>
                                {{ number_format($camera->confidence_threshold, 2) }}
                            </td>

                            <td class="cell-actions">

                                <a href="{{ route('cameras.edit', $camera) }}"
                                   class="btn-icon btn" title="Редагувати">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"
                                         stroke-linecap="round" stroke-linejoin="round">
                                        <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>
                                    </svg>
                                </a>

                                <form action="{{ route('cameras.destroy', $camera) }}"
                                      method="POST"
                                      style="display:inline;"
                                      data-confirm="Видалити камеру «{{ $camera->name }}»? Дію неможливо скасувати.">

                                    @csrf
                                    @method('DELETE')

                                    <button type="submit"
                                            class="btn-icon btn danger"
                                            title="Видалити">
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"
                                             stroke-linecap="round" stroke-linejoin="round">
                                            <path d="M3 6h18"/>
                                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/>
                                            <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                                        </svg>
                                    </button>

                                </form>

                            </td>

                        </tr>

                    @endforeach

                </tbody>

            </table>

        </div>

    @endif

</div>

@endsection
