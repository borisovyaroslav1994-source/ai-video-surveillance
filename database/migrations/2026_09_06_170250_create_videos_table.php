<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up()
    {
        Schema::create('videos', function (Blueprint $table) {
            $table->id();

            $table->foreignId('camera_id')
                ->nullable()
                ->constrained('cameras')
                ->nullOnDelete();

            $table->string('camera_name')->nullable();

            $table->string('filename');

            $table->string('path');

            $table->date('recording_date');

            $table->timestamp('started_at')->nullable();

            $table->timestamp('ended_at')->nullable();

            $table->unsignedBigInteger('duration')
                ->nullable();

            $table->unsignedBigInteger('size')
                ->nullable();

            $table->string('status')
                ->default('recording');

            $table->timestamps();

            $table->index('camera_id');
            $table->index('recording_date');
            $table->index('started_at');
            $table->index('status');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('videos');
    }
};
