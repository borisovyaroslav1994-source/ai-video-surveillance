@if ($paginator->hasPages())

<nav class="pager">

    {{-- Попередня --}}

    @if ($paginator->onFirstPage())
        <span class="pager-btn disabled">‹</span>
    @else
        <a class="pager-btn" href="{{ $paginator->previousPageUrl() }}" rel="prev">‹</a>
    @endif

    {{-- Сторінки --}}

    @foreach ($elements as $element)

        @if (is_string($element))
            <span class="pager-dots">{{ $element }}</span>
        @endif

        @if (is_array($element))

            @foreach ($element as $page => $url)

                @if ($page == $paginator->currentPage())
                    <span class="pager-btn active">{{ $page }}</span>
                @else
                    <a class="pager-btn" href="{{ $url }}">{{ $page }}</a>
                @endif

            @endforeach

        @endif

    @endforeach

    {{-- Наступна --}}

    @if ($paginator->hasMorePages())
        <a class="pager-btn" href="{{ $paginator->nextPageUrl() }}" rel="next">›</a>
    @else
        <span class="pager-btn disabled">›</span>
    @endif

</nav>

@endif
