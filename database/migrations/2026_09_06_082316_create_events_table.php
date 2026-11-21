<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::create('events', function (Blueprint $table) {
            $table->id();

            // Камера
            $table->foreignId('camera_id')
                ->nullable()
                ->constrained('cameras')
                ->nullOnDelete();

            // Назва камери на момент створення події
            $table->string('camera_name')->nullable();

            // YOLO
            $table->string('object');
            $table->unsignedBigInteger('track_id')->nullable();
            $table->decimal('confidence', 5, 4)->default(0);

            // Координати об'єкта
            $table->integer('bbox_x1')->nullable();
            $table->integer('bbox_y1')->nullable();
            $table->integer('bbox_x2')->nullable();
            $table->integer('bbox_y2')->nullable();

            // Фото події
            $table->string('image')->nullable();

            // Статус події
            $table->string('status')->default('active');

            // Час появи / завершення
            $table->timestamp('detected_at')->nullable();
            $table->timestamp('ended_at')->nullable();

            $table->timestamps();

            // Індекси для швидкого журналу
            $table->index('object');
            $table->index('status');
            $table->index('detected_at');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('events');
    }
};