"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { ArrowLeft, Play, TrendingUp, TrendingDown, Activity } from "lucide-react";
import toast, { Toaster } from 'react-hot-toast';

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
        fetch('http://localhost:8000/cryptos/list')
            .then(res => res.json())
            .then(data => setAvailableCryptos(data.cryptos || ["BTCUSDT"]))
            .catch(err => console.error(err));
    }, []);

    const runBacktest = async () => {
        setLoading(true);
        setResult(null);
        try {
            const response = await fetch(`http://localhost:8000/backtest?symbol=${symbol}&days=${days}`, {
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
        <main className="min-h-screen bg-gray-900 text-white p-10 font-sans">
            <Toaster position="top-right" />
            <div className="max-w-6xl mx-auto">
                <header className="flex items-center gap-4 mb-10">
                    <Link href="/" className="p-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition">
                        <ArrowLeft className="w-5 h-5 text-gray-400" />
                    </Link>
                    <h1 className="text-3xl font-bold">Backtest Simulation</h1>
                </header>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Configuration */}
                    <div className="lg:col-span-1 space-y-6">
                        <div className="bg-gray-800 rounded-2xl p-6 border border-gray-700">
                            <h2 className="text-xl font-semibold mb-6">Configuration</h2>
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm text-gray-400 mb-1">Crypto</label>
                                    <select
                                        value={symbol}
                                        onChange={(e) => setSymbol(e.target.value)}
                                        className="w-full bg-gray-900 border border-gray-700 rounded-lg p-3 text-white focus:ring-2 focus:ring-blue-500 outline-none"
                                    >
                                        {availableCryptos.map(c => <option key={c}>{c}</option>)}
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm text-gray-400 mb-1">Durée (Jours)</label>
                                    <input
                                        type="number"
                                        value={days}
                                        onChange={(e) => setDays(Number(e.target.value))}
                                        min="1"
                                        max="90"
                                        className="w-full bg-gray-900 border border-gray-700 rounded-lg p-3 text-white focus:ring-2 focus:ring-blue-500 outline-none"
                                    />
                                    <p className="text-xs text-gray-500 mt-1">Max 90 jours</p>
                                </div>
                                <button
                                    onClick={runBacktest}
                                    disabled={loading}
                                    className={`w-full py-3 rounded-xl font-bold flex items-center justify-center gap-2 transition ${loading
                                        ? 'bg-gray-700 cursor-not-allowed'
                                        : 'bg-blue-600 hover:bg-blue-700'
                                        }`}
                                >
                                    {loading ? (
                                        <Activity className="w-5 h-5 animate-spin" />
                                    ) : (
                                        <>
                                            <Play className="w-5 h-5" />
                                            Lancer Simulation
                                        </>
                                    )}
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* Results */}
                    <div className="lg:col-span-2">
                        {result ? (
                            <div className="space-y-6">
                                {/* Stats Cards */}
                                <div className="grid grid-cols-3 gap-4">
                                    <div className="bg-gray-800 p-6 rounded-2xl border border-gray-700">
                                        <p className="text-gray-400 text-sm mb-1">Win Rate</p>
                                        <p className={`text-2xl font-bold ${result.win_rate >= 50 ? 'text-green-400' : 'text-red-400'}`}>
                                            {result.win_rate.toFixed(1)}%
                                        </p>
                                    </div>
                                    <div className="bg-gray-800 p-6 rounded-2xl border border-gray-700">
                                        <p className="text-gray-400 text-sm mb-1">Profit Total</p>
                                        <p className={`text-2xl font-bold ${result.total_profit >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                            {result.total_profit.toFixed(2)}%
                                        </p>
                                    </div>
                                    <div className="bg-gray-800 p-6 rounded-2xl border border-gray-700">
                                        <p className="text-gray-400 text-sm mb-1">Total Trades</p>
                                        <p className="text-2xl font-bold text-white">
                                            {result.total_trades}
                                        </p>
                                    </div>
                                </div>

                                {/* Trades List */}
                                <div className="bg-gray-800 rounded-2xl border border-gray-700 overflow-hidden">
                                    <div className="p-4 border-b border-gray-700">
                                        <h3 className="font-bold">Historique des Trades</h3>
                                    </div>
                                    <div className="max-h-[400px] overflow-y-auto">
                                        <table className="w-full text-sm">
                                            <thead className="bg-gray-900/50">
                                                <tr>
                                                    <th className="text-left p-3 text-gray-400">Date</th>
                                                    <th className="text-left p-3 text-gray-400">Type</th>
                                                    <th className="text-right p-3 text-gray-400">Entrée</th>
                                                    <th className="text-right p-3 text-gray-400">Sortie</th>
                                                    <th className="text-right p-3 text-gray-400">Profit</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {result.trades.map((trade, i) => (
                                                    <tr key={i} className="border-b border-gray-700/50 hover:bg-gray-700/30">
                                                        <td className="p-3 text-gray-400">{new Date(trade.date).toLocaleDateString()}</td>
                                                        <td className="p-3">
                                                            <span className={`px-2 py-1 rounded text-xs font-bold ${trade.type === 'BUY' ? 'bg-green-900/30 text-green-400' : 'bg-red-900/30 text-red-400'}`}>
                                                                {trade.type}
                                                            </span>
                                                        </td>
                                                        <td className="p-3 text-right font-mono">${trade.entry_price.toFixed(2)}</td>
                                                        <td className="p-3 text-right font-mono">${trade.exit_price.toFixed(2)}</td>
                                                        <td className={`p-3 text-right font-bold ${trade.profit >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                                            {trade.profit > 0 ? '+' : ''}{trade.profit.toFixed(2)}%
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <div className="h-full flex flex-col items-center justify-center text-gray-500 bg-gray-800/50 rounded-2xl border border-gray-700 border-dashed p-10">
                                <Activity className="w-12 h-12 mb-4 opacity-50" />
                                <p>Lancez une simulation pour voir les résultats</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </main>
    );
}
