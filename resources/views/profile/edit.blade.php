@extends('layouts.panel')

@section('page_title', 'Профіль')

@section('content')

<div class="page-header">

    <div>
        <h2>Профіль</h2>
        <p>Керування обліковим записом</p>
    </div>

</div>

<div style="max-width:760px;">

    @include('profile.partials.update-profile-information-form')

    @include('profile.partials.update-password-form')

    @include('profile.partials.delete-user-form')

</div>

@endsection
