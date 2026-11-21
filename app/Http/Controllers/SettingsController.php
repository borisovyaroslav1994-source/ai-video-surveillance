<?php

namespace App\Http\Controllers;

use App\Models\PanelSetting;
use App\Models\User;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Hash;
use Illuminate\Validation\Rule;
use Illuminate\View\View;

class SettingsController extends Controller
{
    public function index(Request $request): View
    {
        $tab = $request->get('tab', 'panel');

        if (!in_array($tab, ['panel', 'users'], true)) {
            $tab = 'panel';
        }

        $catalogue = PanelSetting::catalogue();
        $stored = PanelSetting::all()->keyBy('key');
        $users = User::orderBy('name')->get();

        return view('settings.index', [
            'tab' => $tab,
            'catalogue' => $catalogue,
            'stored' => $stored,
            'users' => $users,
            'roles' => User::ROLES,
            'sections' => User::SECTIONS,
            'currentUser' => $request->user(),
        ]);
    }

    public function updatePanel(Request $request): RedirectResponse
    {
        $catalogue = PanelSetting::catalogue();

        foreach ($catalogue as $groupKey => $group) {
            foreach ($group['items'] as $item) {
                $key = $item['key'];
                $type = $item['type'] ?? 'string';
                $raw = $request->input('settings.'.$key);

                if ($type === 'boolean') {
                    $value = $request->has('settings.'.$key) ? '1' : '0';
                } elseif ($type === 'integer') {
                    $value = (string) max(0, (int) $raw);
                } else {
                    $value = is_string($raw) ? trim($raw) : (string) ($raw ?? '');
                }

                PanelSetting::updateOrCreate(
                    ['key' => $key],
                    [
                        'group' => $groupKey,
                        'value' => $value,
                        'type' => $type,
                        'label' => $item['label'] ?? $key,
                        'description' => $item['description'] ?? null,
                    ]
                );
            }
        }

        return redirect()
            ->route('settings.index', ['tab' => 'panel'])
            ->with('success', 'Налаштування панелі збережено.');
    }
}
