<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Support\Facades\File;
use Illuminate\Support\Str;

class Event extends Model
{
    use HasFactory;

    protected $fillable = [
        'camera_id',
        'camera_name',
        'object',
        'track_id',
        'confidence',
        'bbox_x1',
        'bbox_y1',
        'bbox_x2',
        'bbox_y2',
        'image',
        'status',
        'detected_at',
        'ended_at',
    ];

    protected $casts = [
        'confidence' => 'float',
        'detected_at' => 'datetime',
        'ended_at' => 'datetime',
    ];

    public function camera(): BelongsTo
    {
        return $this->belongsTo(Camera::class);
    }

    /**
     * URL фото події:
     *  1) зовнішній URL — як є;
     *  2) файл у каталозі ai_server — через захищений роут;
     *  3) файл у public — звичайний asset();
     *  4) файлу немає — null.
     */
    public function getImageUrlAttribute(): ?string
    {
        if (empty($this->image)) {
            return null;
        }

        if (Str::startsWith($this->image, ['http://', 'https://'])) {
            return $this->image;
        }

        $relative = str_replace(
            ['/', '\\'],
            DIRECTORY_SEPARATOR,
            ltrim($this->image, '/\\')
        );

        if (File::exists(base_path('ai_server') . DIRECTORY_SEPARATOR . $relative)) {
            return route('archive.image', ['event' => $this->id]);
        }

        if (File::exists(public_path($this->image))) {
            return asset($this->image);
        }

        return null;
    }
}