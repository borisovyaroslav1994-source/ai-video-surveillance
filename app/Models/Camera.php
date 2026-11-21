<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Camera extends Model
{
    protected $table = 'cameras';

    protected $fillable = [
        'name',
        'type',
        'source',
        'location',
        'enabled',
        'ai_enabled',
        'recording_enabled',
        'status',
        'confidence_threshold',
    ];

    protected $casts = [
        'enabled' => 'boolean',
        'ai_enabled' => 'boolean',
        'recording_enabled' => 'boolean',
        'confidence_threshold' => 'float',
    ];
}