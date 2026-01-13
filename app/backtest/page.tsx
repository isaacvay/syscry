"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowLeft, Play, TrendingUp, TrendingDown, Activity, BarChart3 } from "lucide-react";
import toast, { Toaster } from 'react-hot-toast';
import { API_CONFIG } from "../utils/config";
import { Button } from "../components/ui/Button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../components/ui/Card";
import { Input } from "../components/ui/Input";
import { Badge } from "../components/ui/Badge";
import { slideUp, staggerContainer, staggerItem } from "../animations";

interface BacktestResult {
    symbol: string;
    days: number;
    total_trades: number;
    win_rate: number;
    total_profit: number;
    trades: Array<{
        type: string;
        entry_price: number;
        exit_price: number;
        profit: number;
        date: string;
    }>;
}

export default function BacktestPage() {
    const [symbol, setSymbol] = useState("BTCUSDT");
    const [days, setDays] = useState(30);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<BacktestResult | null>(null);
    const [availableCryptos, setAvailableCryptos] = useState<string[]>([]);

    useEffect(() => {
        fetch(`${API_CONFIG.BASE_URL}/cryptos/list`)
            .then(res => res.json())
            .then(data => setAvailableCryptos(data.cryptos || ["BTCUSDT"]))
            .catch(err => console.error(err));
    }, []);

    const runBacktest = async () => {
        setLoading(true);
        setResult(null);
        try {
            const response = await fetch(`${API_CONFIG.BASE_URL}/backtest?symbol=${symbol}&days=${days}`, {
                method: 'POST'
            });
            if (!response.ok) throw new Error('Erreur backtest');
            const data = await response.json();
            setResult(data);
            toast.success('Backtest terminé !');
        } catch (e) {
            toast.error('Erreur lors du backtest');
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    return (
        <main className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-900 to-gray-800 text-white">
            <Toaster position="top-right" />

            {/* Background Effects */}
            <div className="fixed inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-0 left-0 w-96 h-96 bg-green-500/10 rounded-full blur-3xl" />
                <div className="absolute bottom-0 right-0 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl" />
            </div>

            <div className="relative z-10 max-w-7xl mx-auto px-6 py-10">
                <motion.header className="mb-10" {...slideUp}>
                    <div className="flex items-center gap-4 mb-6">
                        <Link href="/">
                            <Button variant="ghost" size="md" leftIcon={<ArrowLeft className="w-5 h-5" />}>
                                Retour
                            </Button>
                        </Link>
                    </div>
                    <h1 className="text-4xl font-black mb-2">
                        <span className="gradient-text">Backtest Simulation</span>
                    </h1>
                    <p className="text-gray-400">Testez vos stratégies sur des données historiques</p>
                </motion.header>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Configuration */}
                    <motion.div className="lg:col-span-1" {...slideUp}>
                        <Card variant="gradient" glow>
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    <BarChart3 className="w-5 h-5 text-cyan-400" />
                                    Configuration
                                </CardTitle>
                                <CardDescription>
                                    Paramètres de simulation
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-2">
                                        Crypto
                                    </label>
                                    <select
                                        value={symbol}
                                        onChange={(e) => setSymbol(e.target.value)}
                                        className="w-full px-4 py-3 bg-gray-900/50 border border-gray-700/50 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 transition-all"
                                    >
                                        {availableCryptos.map(c => <option key={c}>{c}</option>)}
                                    </select>
                                </div>
                                <Input
                                    label="Durée (Jours)"
                                    type="number"
                                    value={days}
                                    onChange={(e) => setDays(Number(e.target.value))}
                                    min={1}
                                    max={90}
                                    helperText="Maximum 90 jours"
                                />
                                <Button
                                    variant="primary"
                                    size="lg"
                                    onClick={runBacktest}
                                    isLoading={loading}
                                    className="w-full"
                                    leftIcon={loading ? undefined : <Play className="w-5 h-5" />}
                                >
                                    {loading ? 'Simulation en cours...' : 'Lancer Simulation'}
                                </Button>
                            </CardContent>
                        </Card>
                    </motion.div>

                    {/* Results */}
                    <div className="lg:col-span-2">
                        {result ? (
                            <motion.div
                                className="space-y-6"
                                variants={staggerContainer}
                                initial="initial"
                                animate="animate"
                            >
                                {/* Stats Cards */}
                                <motion.div variants={staggerItem} className="grid grid-cols-3 gap-4">
                                    <Card variant="glass" hover glow>
                                        <CardContent>
                                            <p className="text-gray-400 text-sm mb-2">Win Rate</p>
                                            <p className={`text-3xl font-bold ${result.win_rate >= 50 ? 'text-green-400' : 'text-red-400'}`}>
                                                {result.win_rate.toFixed(1)}%
                                            </p>
                                        </CardContent>
                                    </Card>
                                    <Card variant="glass" hover glow>
                                        <CardContent>
                                            <p className="text-gray-400 text-sm mb-2">Profit Total</p>
                                            <p className={`text-3xl font-bold ${result.total_profit >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                                {result.total_profit >= 0 ? '+' : ''}{result.total_profit.toFixed(2)}%
                                            </p>
                                        </CardContent>
                                    </Card>
                                    <Card variant="glass" hover glow>
                                        <CardContent>
                                            <p className="text-gray-400 text-sm mb-2">Total Trades</p>
                                            <p className="text-3xl font-bold text-cyan-400">
                                                {result.total_trades}
                                            </p>
                                        </CardContent>
                                    </Card>
                                </motion.div>

                                {/* Trades List */}
                                <motion.div variants={staggerItem}>
                                    <Card variant="gradient">
                                        <CardHeader>
                                            <CardTitle>Historique des Trades</CardTitle>
                                        </CardHeader>
                                        <CardContent>
                                            <div className="max-h-[500px] overflow-y-auto">
                                                <table className="w-full text-sm">
                                                    <thead className="sticky top-0 bg-gray-900/95 backdrop-blur-sm">
                                                        <tr className="border-b border-gray-700">
                                                            <th className="text-left p-3 text-gray-400 font-semibold">Date</th>
                                                            <th className="text-left p-3 text-gray-400 font-semibold">Type</th>
                                                            <th className="text-right p-3 text-gray-400 font-semibold">Entrée</th>
                                                            <th className="text-right p-3 text-gray-400 font-semibold">Sortie</th>
                                                            <th className="text-right p-3 text-gray-400 font-semibold">Profit</th>
                                                        </tr>
                                                    </thead>
                                                    <tbody>
                                                        {result.trades.map((trade, i) => (
                                                            <tr key={i} className="border-b border-gray-700/30 hover:bg-gray-800/30 transition-colors">
                                                                <td className="p-3 text-gray-400">
                                                                    {new Date(trade.date).toLocaleDateString('fr-FR')}
                                                                </td>
                                                                <td className="p-3">
                                                                    <Badge
                                                                        variant={trade.type === 'BUY' ? 'success' : 'danger'}
                                                                        size="sm"
                                                                    >
                                                                        {trade.type === 'BUY' ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                                                                        {trade.type}
                                                                    </Badge>
                                                                </td>
                                                                <td className="p-3 text-right font-mono text-white">
                                                                    ${trade.entry_price.toFixed(2)}
                                                                </td>
                                                                <td className="p-3 text-right font-mono text-white">
                                                                    ${trade.exit_price.toFixed(2)}
                                                                </td>
                                                                <td className={`p-3 text-right font-bold font-mono ${trade.profit >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                                                    {trade.profit > 0 ? '+' : ''}{trade.profit.toFixed(2)}%
                                                                </td>
                                                            </tr>
                                                        ))}
                                                    </tbody>
                                                </table>
                                            </div>
                                        </CardContent>
                                    </Card>
                                </motion.div>
                            </motion.div>
                        ) : (
                            <Card variant="glass" className="h-full">
                                <CardContent className="flex flex-col items-center justify-center text-gray-500 p-20">
                                    <Activity className="w-16 h-16 mb-4 opacity-50" />
                                    <p className="text-lg">Lancez une simulation pour voir les résultats</p>
                                </CardContent>
                            </Card>
                        )}
                    </div>
                </div>
            </div>
        </main>
    );
}
