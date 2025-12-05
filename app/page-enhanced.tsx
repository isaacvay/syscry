"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import toast, { Toaster } from 'react-hot-toast';
import {
    Settings,
    RefreshCw,
    Play,
    Pause,
    LayoutGrid,
    Maximize,
    TrendingUp,
    TrendingDown,
    Activity,
    Zap,
    BarChart3,
    DollarSign,
    Bell,
} from "lucide-react";

import { CryptoChart } from "./components/CryptoChart";
import { CryptoSelector } from "./components/CryptoSelector";
import { Watchlist } from "./components/Watchlist";
import { SignalHistory } from "./components/SignalHistory";
import { GridDashboard } from "./components/GridDashboard";
import { MarketHeatmap } from "./components/MarketHeatmap";
import { AlertManager } from "./components/AlertManager";
import { ConnectionStatus } from "./components/ConnectionStatus";
import { SignalCardSkeleton, WatchlistSkeleton } from "./components/Skeleton";
import { Button } from "./components/ui/Button";
import { Card, CardHeader, CardTitle, CardContent } from "./components/ui/Card";
import { Badge } from "./components/ui/Badge";
import { Tooltip } from "./components/ui/Tooltip";
import { fadeIn, slideUp, staggerContainer, staggerItem } from "./animations";
import { useWebSocketSignals } from "./hooks/useWebSocket";
import { useAppStore } from "./store/useAppStore";

interface SignalData {
    symbol: string;
    timeframe: string;
    signal: string;
    confidence: number;
    price: number;
    indicators: {
        rsi: number;
        ema20: number;
        ema50: number;
        macd: number;
    };
    chart_data: { time: number; open: number; high: number; low: number; close: number }[];
}

export default function Home() {
    const [viewMode, setViewMode] = useState<'single' | 'grid' | 'advanced'>('single');
    const [data, setData] = useState<SignalData | null>(null);
    const [watchlistData, setWatchlistData] = useState<SignalData[]>([]);
    const [loading, setLoading] = useState(true);

    const [availableCryptos, setAvailableCryptos] = useState<string[]>(["BTCUSDT"]);
    const [availableTimeframes, setAvailableTimeframes] = useState<string[]>(["1h"]);
    const [selectedCrypto, setSelectedCrypto] = useState("BTCUSDT");
    const [selectedTimeframe, setSelectedTimeframe] = useState("1h");

    const { preferences, updatePreferences } = useAppStore();
    const { autoRefresh, refreshInterval } = preferences;

    // WebSocket integration (optional - can be enabled/disabled)
    const [useWebSocket, setUseWebSocket] = useState(false);
    const { signals: wsSignals, isConnected, connectionStatus } = useWebSocketSignals({
        enabled: useWebSocket,
        onSignalUpdate: (signals) => {
            setWatchlistData(signals);
            const current = signals.find(s => s.symbol === selectedCrypto);
            if (current) setData(current as any);
        },
    });

    // Fetch available cryptos and timeframes
    useEffect(() => {
        fetch("http://localhost:8000/cryptos/list")
            .then((res) => res.json())
            .then((data) => {
                setAvailableCryptos(data.cryptos || ["BTCUSDT"]);
                setAvailableTimeframes(data.timeframes || ["1h"]);
            })
            .catch((err) => {
                console.error("Error fetching crypto list:", err);
                toast.error("Erreur de connexion au backend");
            });
    }, []);

    // Fetch watchlist data
    const fetchWatchlist = () => {
        if (useWebSocket) return; // Skip if using WebSocket

        fetch("http://localhost:8000/signals/multi", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                symbols: availableCryptos,
                timeframe: selectedTimeframe === 'all' ? '1w' : selectedTimeframe
            }),
        })
            .then((res) => res.json())
            .then((data) => setWatchlistData(data.signals || []))
            .catch((err) => {
                console.error("Error fetching watchlist:", err);
                toast.error("Erreur lors de la récupération de la watchlist");
            });
    };

    // Fetch single crypto signal
    const fetchSignal = () => {
        if (useWebSocket) return; // Skip if using WebSocket

        setLoading(true);
        fetch("http://localhost:8000/get-signal", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                symbol: selectedCrypto,
                timeframe: selectedTimeframe === 'all' ? '1w' : selectedTimeframe
            }),
        })
            .then((res) => {
                if (!res.ok) throw new Error("Erreur connexion backend");
                return res.json();
            })
            .then((signalData) => {
                setData(signalData);
                toast.success(`Signal ${selectedCrypto} mis à jour !`);
            })
            .catch((err) => {
                console.error(err);
                toast.error("Erreur de connexion au backend");
            })
            .finally(() => setLoading(false));
    };

    useEffect(() => {
        if (!useWebSocket) {
            fetchSignal();
            fetchWatchlist();
        }
    }, [selectedCrypto, selectedTimeframe, useWebSocket]);

    // Auto-refresh (only when not using WebSocket)
    useEffect(() => {
        if (!autoRefresh || useWebSocket) return;
        const interval = setInterval(() => {
            fetchSignal();
            fetchWatchlist();
        }, refreshInterval * 1000);
        return () => clearInterval(interval);
    }, [autoRefresh, refreshInterval, selectedCrypto, selectedTimeframe, useWebSocket]);

    // Calculate market stats
    const marketStats = {
        totalValue: watchlistData.reduce((acc, s) => acc + (s.price || 0), 0),
        buySignals: watchlistData.filter(s => s.signal?.includes("BUY")).length,
        sellSignals: watchlistData.filter(s => s.signal?.includes("SELL")).length,
        avgConfidence: watchlistData.length > 0
            ? (watchlistData.reduce((acc, s) => acc + (s.confidence || 0), 0) / watchlistData.length) * 100
            : 0,
    };

    return (
        <main className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-900 to-gray-800 text-white">
            <Toaster position="top-right" />

            {/* Background Effects */}
            <div className="fixed inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-0 right-0 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl" />
                <div className="absolute bottom-0 left-0 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl" />
            </div>

            <div className="relative z-10 max-w-[1800px] mx-auto px-6 py-8">
                {/* Header */}
                <motion.header
                    className="mb-10"
                    initial="initial"
                    animate="animate"
                    variants={staggerContainer}
                >
                    <motion.div variants={staggerItem} className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6 mb-8">
                        <div>
                            <h1 className="text-4xl lg:text-5xl font-black mb-2">
                                <span className="gradient-text">Crypto AI System</span>
                            </h1>
                            <div className="flex items-center gap-3 flex-wrap">
                                <Badge variant="success" dot>Live</Badge>
                                <span className="text-gray-400">Trading Signals & Analysis</span>
                                {useWebSocket && <ConnectionStatus isConnected={isConnected} status={connectionStatus} />}
                            </div>
                        </div>

                        <div className="flex gap-3 items-center flex-wrap">
                            <CryptoSelector
                                cryptos={availableCryptos}
                                timeframes={availableTimeframes}
                                selectedCrypto={selectedCrypto}
                                selectedTimeframe={selectedTimeframe}
                                onCryptoChange={setSelectedCrypto}
                                onTimeframeChange={setSelectedTimeframe}
                            />

                            <Tooltip content="Rafraîchir les données">
                                <Button
                                    variant="secondary"
                                    size="md"
                                    onClick={() => {
                                        fetchSignal();
                                        fetchWatchlist();
                                    }}
                                    leftIcon={<RefreshCw className="w-4 h-4" />}
                                />
                            </Tooltip>

                            <Tooltip content={autoRefresh ? "Désactiver auto-refresh" : "Activer auto-refresh"}>
                                <Button
                                    variant={autoRefresh ? "success" : "ghost"}
                                    size="md"
                                    onClick={() => updatePreferences({ autoRefresh: !autoRefresh })}
                                    leftIcon={autoRefresh ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                                />
                            </Tooltip>

                            <Tooltip content="Changer la vue">
                                <Button
                                    variant="ghost"
                                    size="md"
                                    onClick={() => setViewMode(v => v === 'single' ? 'grid' : v === 'grid' ? 'advanced' : 'single')}
                                    leftIcon={viewMode === 'single' ? <LayoutGrid className="w-4 h-4" /> : <Maximize className="w-4 h-4" />}
                                />
                            </Tooltip>

                            <Link href="/backtest">
                                <Button variant="ghost" size="md" leftIcon={<TrendingUp className="w-4 h-4" />}>
                                    Backtest
                                </Button>
                            </Link>

                            <Link href="/settings">
                                <Button variant="ghost" size="md" leftIcon={<Settings className="w-4 h-4" />}>
                                    Settings
                                </Button>
                            </Link>
                        </div>
                    </motion.div>

                    {/* Market Stats */}
                    <motion.div variants={staggerItem} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        <Card variant="glass" hover glow>
                            <CardContent className="flex items-center gap-4">
                                <div className="p-3 bg-cyan-500/10 rounded-xl">
                                    <DollarSign className="w-6 h-6 text-cyan-400" />
                                </div>
                                <div>
                                    <p className="text-sm text-gray-400">Total Market Value</p>
                                    <p className="text-2xl font-bold font-mono">${marketStats.totalValue.toFixed(0)}</p>
                                </div>
                            </CardContent>
                        </Card>

                        <Card variant="glass" hover glow>
                            <CardContent className="flex items-center gap-4">
                                <div className="p-3 bg-green-500/10 rounded-xl">
                                    <TrendingUp className="w-6 h-6 text-green-400" />
                                </div>
                                <div>
                                    <p className="text-sm text-gray-400">Buy Signals</p>
                                    <p className="text-2xl font-bold text-green-400">{marketStats.buySignals}</p>
                                </div>
                            </CardContent>
                        </Card>

                        <Card variant="glass" hover glow>
                            <CardContent className="flex items-center gap-4">
                                <div className="p-3 bg-red-500/10 rounded-xl">
                                    <TrendingDown className="w-6 h-6 text-red-400" />
                                </div>
                                <div>
                                    <p className="text-sm text-gray-400">Sell Signals</p>
                                    <p className="text-2xl font-bold text-red-400">{marketStats.sellSignals}</p>
                                </div>
                            </CardContent>
                        </Card>

                        <Card variant="glass" hover glow>
                            <CardContent className="flex items-center gap-4">
                                <div className="p-3 bg-purple-500/10 rounded-xl">
                                    <Zap className="w-6 h-6 text-purple-400" />
                                </div>
                                <div>
                                    <p className="text-sm text-gray-400">Avg Confidence</p>
                                    <p className="text-2xl font-bold text-purple-400">{marketStats.avgConfidence.toFixed(0)}%</p>
                                </div>
                            </CardContent>
                        </Card>
                    </motion.div>
                </motion.header>

                {/* Main Content */}
                {viewMode === 'grid' ? (
                    <GridDashboard />
                ) : viewMode === 'advanced' ? (
                    <div className="space-y-8">
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                            <MarketHeatmap />
                            <AlertManager />
                        </div>
                        <GridDashboard />
                    </div>
                ) : (
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                        {/* Main Signal Display */}
                        <div className="lg:col-span-2 space-y-8">
                            <AnimatePresence mode="wait">
                                {loading ? (
                                    <motion.div key="loading" {...fadeIn}>
                                        <SignalCardSkeleton />
                                    </motion.div>
                                ) : data && data.signal ? (
                                    <motion.div key="content" {...slideUp}>
                                        <Card variant="gradient" glow>
                                            <CardHeader>
                                                <div className="flex justify-between items-start">
                                                    <div>
                                                        <CardTitle className="text-3xl">{data.symbol}</CardTitle>
                                                        <p className="text-gray-400 text-sm mt-1">Timeframe: {data.timeframe}</p>
                                                    </div>
                                                    <div className="text-right">
                                                        <div className="text-3xl font-mono font-bold text-white">
                                                            ${data.price?.toFixed(2) || 'N/A'}
                                                        </div>
                                                    </div>
                                                </div>
                                            </CardHeader>

                                            <CardContent>
                                                <div className="grid grid-cols-2 gap-6 mb-6">
                                                    <div
                                                        className={`p-6 rounded-xl border-2 text-center transition-all ${data.signal?.includes("BUY")
                                                                ? "border-green-500 bg-green-900/20 shadow-lg shadow-green-500/20"
                                                                : data.signal?.includes("SELL")
                                                                    ? "border-red-500 bg-red-900/20 shadow-lg shadow-red-500/20"
                                                                    : "border-gray-500 bg-gray-700/30"
                                                            }`}
                                                    >
                                                        <p className="text-gray-400 text-xs uppercase tracking-wider mb-2">Signal AI</p>
                                                        <p
                                                            className={`text-4xl font-black ${data.signal?.includes("BUY")
                                                                    ? "text-green-400"
                                                                    : data.signal?.includes("SELL")
                                                                        ? "text-red-400"
                                                                        : "text-gray-300"
                                                                }`}
                                                        >
                                                            {data.signal || 'N/A'}
                                                        </p>
                                                    </div>

                                                    <div className="p-6 rounded-xl border border-gray-700 bg-gray-800/30 text-center">
                                                        <p className="text-gray-400 text-xs uppercase tracking-wider mb-2">Confiance</p>
                                                        <div className="flex items-center justify-center gap-2">
                                                            <span className="text-4xl font-bold text-cyan-400">
                                                                {((data.confidence || 0) * 100).toFixed(0)}%
                                                            </span>
                                                        </div>
                                                    </div>
                                                </div>

                                                <div className="space-y-4">
                                                    <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider border-b border-gray-700 pb-2">
                                                        Indicateurs Techniques
                                                    </h3>
                                                    <div className="grid grid-cols-2 gap-y-4 gap-x-8 text-sm">
                                                        <div className="flex justify-between">
                                                            <span className="text-gray-400">RSI (14)</span>
                                                            <span
                                                                className={`font-mono font-semibold ${(data.indicators?.rsi || 0) < 30
                                                                        ? "text-green-400"
                                                                        : (data.indicators?.rsi || 0) > 70
                                                                            ? "text-red-400"
                                                                            : "text-white"
                                                                    }`}
                                                            >
                                                                {data.indicators?.rsi?.toFixed(2) || 'N/A'}
                                                            </span>
                                                        </div>
                                                        <div className="flex justify-between">
                                                            <span className="text-gray-400">MACD</span>
                                                            <span className={`font-mono font-semibold ${(data.indicators?.macd || 0) > 0 ? "text-green-400" : "text-red-400"}`}>
                                                                {data.indicators?.macd?.toFixed(2) || 'N/A'}
                                                            </span>
                                                        </div>
                                                        <div className="flex justify-between">
                                                            <span className="text-gray-400">EMA (20)</span>
                                                            <span className="font-mono font-semibold text-white">{data.indicators?.ema20?.toFixed(2) || 'N/A'}</span>
                                                        </div>
                                                        <div className="flex justify-between">
                                                            <span className="text-gray-400">EMA (50)</span>
                                                            <span className="font-mono font-semibold text-white">{data.indicators?.ema50?.toFixed(2) || 'N/A'}</span>
                                                        </div>
                                                    </div>
                                                </div>
                                            </CardContent>
                                        </Card>

                                        {data.chart_data && data.chart_data.length > 0 && (
                                            <Card variant="gradient" className="mt-8">
                                                <CryptoChart
                                                    data={data.chart_data}
                                                    timeframe={selectedTimeframe}
                                                    onTimeframeChange={setSelectedTimeframe}
                                                    onRefresh={() => {
                                                        fetchSignal();
                                                        fetchWatchlist();
                                                    }}
                                                />
                                            </Card>
                                        )}

                                        <SignalHistory symbol={selectedCrypto} limit={15} />
                                    </motion.div>
                                ) : null}
                            </AnimatePresence>
                        </div>

                        {/* Watchlist Sidebar */}
                        <div className="lg:col-span-1">
                            {loading ? (
                                <WatchlistSkeleton />
                            ) : (
                                <Watchlist signals={watchlistData} onSelectCrypto={setSelectedCrypto} />
                            )}
                        </div>
                    </div>
                )}
            </div>
        </main>
    );
}
