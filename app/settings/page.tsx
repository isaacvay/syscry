"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { ArrowLeft, Save, Check } from "lucide-react";
import toast, { Toaster } from 'react-hot-toast';

interface SettingsData {
    binanceApiKey: string;
    binanceSecretKey: string;
    defaultCrypto: string;
    defaultTimeframe: string;
    telegramBotToken: string;
    telegramChatId: string;
    alertsEnabled: boolean;
}

export default function SettingsPage() {
    const [settings, setSettings] = useState<SettingsData>({
        binanceApiKey: '',
        binanceSecretKey: '',
        defaultCrypto: 'BTCUSDT',
        defaultTimeframe: '1h',
        telegramBotToken: '',
        telegramChatId: '',
        alertsEnabled: true
    });

    const [saved, setSaved] = useState(false);
    const [availableCryptos, setAvailableCryptos] = useState<string[]>([]);
    const [availableTimeframes, setAvailableTimeframes] = useState<string[]>([]);

    // Load settings and available options
    useEffect(() => {
        // Fetch settings
        fetch('http://localhost:8000/settings')
            .then(res => res.json())
            .then(data => setSettings(data))
            .catch(err => console.error('Error loading settings:', err));

        // Fetch available options
        fetch('http://localhost:8000/cryptos/list')
            .then(res => res.json())
            .then(data => {
                setAvailableCryptos(data.cryptos || []);
                setAvailableTimeframes(data.timeframes || []);
            })
            .catch(err => console.error('Error loading options:', err));
    }, []);

    const handleSave = async () => {
        try {
            const response = await fetch('http://localhost:8000/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    binance_api_key: settings.binanceApiKey,
                    binance_secret_key: settings.binanceSecretKey,
                    default_crypto: settings.defaultCrypto,
                    default_timeframe: settings.defaultTimeframe,
                    telegram_bot_token: settings.telegramBotToken,
                    telegram_chat_id: settings.telegramChatId,
                    alerts_enabled: settings.alertsEnabled
                })
            });

            if (!response.ok) throw new Error('Erreur sauvegarde');

            setSaved(true);
            toast.success('Paramètres sauvegardés sur le serveur !');
            setTimeout(() => setSaved(false), 2000);
        } catch (e) {
            toast.error('Erreur lors de la sauvegarde');
            console.error('Error saving settings:', e);
        }
    };

    const handleChange = (field: keyof SettingsData, value: string | boolean) => {
        setSettings(prev => ({ ...prev, [field]: value }));
    };

    return (
        <main className="min-h-screen bg-gray-900 text-white p-10 font-sans">
            <Toaster position="top-right" />
            <div className="max-w-2xl mx-auto">
                <header className="flex items-center gap-4 mb-10">
                    <Link href="/" className="p-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition">
                        <ArrowLeft className="w-5 h-5 text-gray-400" />
                    </Link>
                    <h1 className="text-3xl font-bold">Paramètres</h1>
                </header>

                <div className="space-y-6">
                    {/* API Configuration */}
                    <div className="bg-gray-800 rounded-2xl p-8 shadow-lg border border-gray-700">
                        <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
                            🔑 Configuration API
                        </h2>
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm text-gray-400 mb-1">Binance API Key</label>
                                <input
                                    type="password"
                                    value={settings.binanceApiKey || ''}
                                    onChange={(e) => handleChange('binanceApiKey', e.target.value)}
                                    className="w-full bg-gray-900 border border-gray-700 rounded-lg p-3 text-white focus:ring-2 focus:ring-blue-500 outline-none"
                                    placeholder="Votre clé API Binance"
                                />
                            </div>
                            <div>
                                <label className="block text-sm text-gray-400 mb-1">Binance Secret Key</label>
                                <input
                                    type="password"
                                    value={settings.binanceSecretKey || ''}
                                    onChange={(e) => handleChange('binanceSecretKey', e.target.value)}
                                    className="w-full bg-gray-900 border border-gray-700 rounded-lg p-3 text-white focus:ring-2 focus:ring-blue-500 outline-none"
                                    placeholder="Votre clé secrète Binance"
                                />
                            </div>
                        </div>
                    </div>

                    {/* Trading Preferences */}
                    <div className="bg-gray-800 rounded-2xl p-8 shadow-lg border border-gray-700">
                        <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
                            ⚙️ Préférences de Trading
                        </h2>
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm text-gray-400 mb-1">Paire par défaut</label>
                                <select
                                    value={settings.defaultCrypto || ''}
                                    onChange={(e) => handleChange('defaultCrypto', e.target.value)}
                                    className="w-full bg-gray-900 border border-gray-700 rounded-lg p-3 text-white focus:ring-2 focus:ring-blue-500 outline-none"
                                >
                                    {availableCryptos.map(c => <option key={c}>{c}</option>)}
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm text-gray-400 mb-1">Timeframe par défaut</label>
                                <select
                                    value={settings.defaultTimeframe || ''}
                                    onChange={(e) => handleChange('defaultTimeframe', e.target.value)}
                                    className="w-full bg-gray-900 border border-gray-700 rounded-lg p-3 text-white focus:ring-2 focus:ring-blue-500 outline-none"
                                >
                                    {availableTimeframes.map(t => <option key={t}>{t}</option>)}
                                </select>
                            </div>
                        </div>
                    </div>

                    {/* Telegram Alerts */}
                    <div className="bg-gray-800 rounded-2xl p-8 shadow-lg border border-gray-700">
                        <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
                            🔔 Alertes Telegram
                        </h2>
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm text-gray-400 mb-1">Bot Token</label>
                                <input
                                    type="text"
                                    value={settings.telegramBotToken || ''}
                                    onChange={(e) => handleChange('telegramBotToken', e.target.value)}
                                    className="w-full bg-gray-900 border border-gray-700 rounded-lg p-3 text-white focus:ring-2 focus:ring-blue-500 outline-none"
                                    placeholder="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
                                />
                            </div>
                            <div>
                                <label className="block text-sm text-gray-400 mb-1">Chat ID</label>
                                <input
                                    type="text"
                                    value={settings.telegramChatId || ''}
                                    onChange={(e) => handleChange('telegramChatId', e.target.value)}
                                    className="w-full bg-gray-900 border border-gray-700 rounded-lg p-3 text-white focus:ring-2 focus:ring-blue-500 outline-none"
                                    placeholder="123456789"
                                />
                            </div>
                            <div className="flex items-center gap-3 mt-4">
                                <input
                                    type="checkbox"
                                    id="alerts"
                                    checked={settings.alertsEnabled || false}
                                    onChange={(e) => handleChange('alertsEnabled', e.target.checked)}
                                    className="w-5 h-5 rounded border-gray-700 bg-gray-900 text-blue-600 focus:ring-blue-500"
                                />
                                <label htmlFor="alerts" className="text-gray-300">Activer les notifications automatiques</label>
                            </div>
                        </div>
                    </div>

                    <button
                        onClick={handleSave}
                        className={`w-full font-bold py-4 rounded-xl transition flex items-center justify-center gap-2 ${saved
                            ? 'bg-green-600 hover:bg-green-700'
                            : 'bg-blue-600 hover:bg-blue-700'
                            } text-white`}
                    >
                        {saved ? (
                            <>
                                <Check className="w-5 h-5" />
                                Sauvegardé !
                            </>
                        ) : (
                            <>
                                <Save className="w-5 h-5" />
                                Sauvegarder les paramètres
                            </>
                        )}
                    </button>
                </div>
            </div>
        </main>
    );
}
