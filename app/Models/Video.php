<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class Video extends Model
{
    protected $fillable = [
        'camera_id',
        'camera_name',
        'filename',
        'path',
        'recording_date',
        'started_at',
        'ended_at',
        'duration',
        'size',
        'status',
    ];

    protected $casts = [
        'recording_date' => 'date',
        'started_at' => 'datetime',
        'ended_at' => 'datetime',
    ];

    public function camera(): BelongsTo
    {
        return $this->belongsTo(Camera::class);
    }
}