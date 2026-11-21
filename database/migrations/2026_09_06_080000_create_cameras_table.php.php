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
        Schema::create('cameras', function (Blueprint $table) {
            $table->id();

            // Основна інформація
            $table->string('name');
            $table->string('type')->default('usb');
            $table->string('source');
            $table->string('location')->nullable();

            // AI
            $table->decimal('confidence_threshold', 5, 4)
                ->default(0.5000);

            // Керування камерою
            $table->boolean('enabled')->default(true);
            $table->boolean('ai_enabled')->default(true);
            $table->boolean('recording_enabled')->default(true);

            // Статус
            $table->string('status')->default('offline');

            $table->timestamps();

            // Індекси
            $table->index('enabled');
            $table->index('status');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('cameras');
    }
};