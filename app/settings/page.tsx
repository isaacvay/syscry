"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowLeft, Save, Check, Key, Settings as SettingsIcon, Bell } from "lucide-react";
import toast, { Toaster } from 'react-hot-toast';
import { API_CONFIG } from "../utils/config";
import { Button } from "../components/ui/Button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../components/ui/Card";
import { Input } from "../components/ui/Input";
import { slideUp, staggerContainer, staggerItem } from "../animations";

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

    useEffect(() => {
        fetch(`${API_CONFIG.BASE_URL}/settings`)
            .then(res => res.json())
            .then(data => setSettings(data))
            .catch(err => console.error('Error loading settings:', err));

        fetch(`${API_CONFIG.BASE_URL}/cryptos/list`)
            .then(res => res.json())
            .then(data => {
                setAvailableCryptos(data.cryptos || []);
                setAvailableTimeframes(data.timeframes || []);
            })
            .catch(err => console.error('Error loading options:', err));
    }, []);

    const handleSave = async () => {
        try {
            const response = await fetch(`${API_CONFIG.BASE_URL}/settings`, {
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
            toast.success('Paramètres sauvegardés !');
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
        <main className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-900 to-gray-800 text-white">
            <Toaster position="top-right" />

            {/* Background Effects */}
            <div className="fixed inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-0 right-0 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl" />
                <div className="absolute bottom-0 left-0 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl" />
            </div>

            <div className="relative z-10 max-w-4xl mx-auto px-6 py-10">
                <motion.header className="mb-10" {...slideUp}>
                    <div className="flex items-center gap-4 mb-6">
                        <Link href="/">
                            <Button variant="ghost" size="md" leftIcon={<ArrowLeft className="w-5 h-5" />}>
                                Retour
                            </Button>
                        </Link>
                    </div>
                    <h1 className="text-4xl font-black mb-2">
                        <span className="gradient-text">Paramètres</span>
                    </h1>
                    <p className="text-gray-400">Configurez votre système de trading</p>
                </motion.header>

                <motion.div
                    className="space-y-6"
                    variants={staggerContainer}
                    initial="initial"
                    animate="animate"
                >
                    {/* API Configuration */}
                    <motion.div variants={staggerItem}>
                        <Card variant="gradient" glow>
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    <Key className="w-5 h-5 text-cyan-400" />
                                    Configuration API
                                </CardTitle>
                                <CardDescription>
                                    Connectez votre compte Binance pour le trading en temps réel
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <Input
                                    label="Binance API Key"
                                    type="password"
                                    value={settings.binanceApiKey || ''}
                                    onChange={(e) => handleChange('binanceApiKey', e.target.value)}
                                    placeholder="Votre clé API Binance"
                                />
                                <Input
                                    label="Binance Secret Key"
                                    type="password"
                                    value={settings.binanceSecretKey || ''}
                                    onChange={(e) => handleChange('binanceSecretKey', e.target.value)}
                                    placeholder="Votre clé secrète Binance"
                                />
                            </CardContent>
                        </Card>
                    </motion.div>

                    {/* Trading Preferences */}
                    <motion.div variants={staggerItem}>
                        <Card variant="gradient" glow>
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    <SettingsIcon className="w-5 h-5 text-purple-400" />
                                    Préférences de Trading
                                </CardTitle>
                                <CardDescription>
                                    Définissez vos paramètres par défaut
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-2">
                                        Paire par défaut
                                    </label>
                                    <select
                                        value={settings.defaultCrypto || ''}
                                        onChange={(e) => handleChange('defaultCrypto', e.target.value)}
                                        className="w-full px-4 py-3 bg-gray-900/50 border border-gray-700/50 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 transition-all"
                                    >
                                        {availableCryptos.map(c => <option key={c}>{c}</option>)}
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-2">
                                        Timeframe par défaut
                                    </label>
                                    <select
                                        value={settings.defaultTimeframe || ''}
                                        onChange={(e) => handleChange('defaultTimeframe', e.target.value)}
                                        className="w-full px-4 py-3 bg-gray-900/50 border border-gray-700/50 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 transition-all"
                                    >
                                        {availableTimeframes.map(t => <option key={t}>{t}</option>)}
                                    </select>
                                </div>
                            </CardContent>
                        </Card>
                    </motion.div>

                    {/* Telegram Alerts */}
                    <motion.div variants={staggerItem}>
                        <Card variant="gradient" glow>
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    <Bell className="w-5 h-5 text-yellow-400" />
                                    Alertes Telegram
                                </CardTitle>
                                <CardDescription>
                                    Recevez des notifications sur Telegram
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <Input
                                    label="Bot Token"
                                    type="text"
                                    value={settings.telegramBotToken || ''}
                                    onChange={(e) => handleChange('telegramBotToken', e.target.value)}
                                    placeholder="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
                                />
                                <Input
                                    label="Chat ID"
                                    type="text"
                                    value={settings.telegramChatId || ''}
                                    onChange={(e) => handleChange('telegramChatId', e.target.value)}
                                    placeholder="123456789"
                                />
                                <div className="flex items-center gap-3 pt-2">
                                    <input
                                        type="checkbox"
                                        id="alerts"
                                        checked={settings.alertsEnabled || false}
                                        onChange={(e) => handleChange('alertsEnabled', e.target.checked)}
                                        className="w-5 h-5 rounded border-gray-700 bg-gray-900 text-cyan-600 focus:ring-cyan-500"
                                    />
                                    <label htmlFor="alerts" className="text-gray-300 cursor-pointer">
                                        Activer les notifications automatiques
                                    </label>
                                </div>
                            </CardContent>
                        </Card>
                    </motion.div>

                    <motion.div variants={staggerItem}>
                        <Button
                            variant={saved ? "success" : "primary"}
                            size="lg"
                            onClick={handleSave}
                            className="w-full"
                            leftIcon={saved ? <Check className="w-5 h-5" /> : <Save className="w-5 h-5" />}
                        >
                            {saved ? 'Sauvegardé !' : 'Sauvegarder les paramètres'}
                        </Button>
                    </motion.div>
                </motion.div>
            </div>
        </main>
    );
}
