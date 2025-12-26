'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import {
    ArrowLeft, Play, Pause, Activity, TrendingUp, TrendingDown,
    Target, BarChart3, RefreshCw, Server, Zap, DollarSign,
    Percent, Clock, Wallet, LineChart, PieChart, ArrowUpRight,
    ArrowDownRight, Sparkles, Shield, Flame
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import TradingStrategy, { STRATEGIES, Strategy } from '../components/TradingStrategy';
import SessionManager from '../components/SessionManager';
import { staggerContainer, staggerItem } from '../animations';
import toast from 'react-hot-toast';

interface Trade {
    id: number;
    symbol: string;
    type: string;
    price: number;
    quantity: number;
    timestamp: string;
    confidence: number;
    signalReason: string;
    pnl: number;
}

interface Position {
    id: number;
    symbol: string;
    quantity: number;
    averagePrice: number;
    currentPrice: number;
    pnl: number;
    stopLoss: number;
    takeProfit: number;
    trailingStopPrice?: number;
}

interface SessionStats {
    totalTrades: number;
    winningTrades: number;
    losingTrades: number;
    winRate: number;
}

interface TradingSession {
    id: string;
    name: string;
    strategy: Strategy;
    symbols: string[];
    initialBalance: number;
    currentBalance: number;
    isActive: boolean;
    autoTrade: boolean;
    stats: SessionStats;
    positions?: Position[];
    trades?: Trade[];
    createdAt: string;
    updatedAt: string;
}

const API_URL = 'http://localhost:8000';

// Animated counter component
const AnimatedValue = ({ value, prefix = '', suffix = '', decimals = 2 }: { value: number; prefix?: string; suffix?: string; decimals?: number }) => {
    return (
        <motion.span
            key={value}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="font-mono"
        >
            {prefix}{value.toFixed(decimals)}{suffix}
        </motion.span>
    );
};

// Glowing stat card
const StatCard = ({
    title,
    value,
    subValue,
    icon: Icon,
    color = 'cyan',
    isPositive,
    prefix = '',
    suffix = ''
}: {
    title: string;
    value: number;
    subValue?: string;
    icon: React.ElementType;
    color?: 'cyan' | 'green' | 'red' | 'purple' | 'orange';
    isPositive?: boolean;
    prefix?: string;
    suffix?: string;
}) => {
    const colorClasses = {
        cyan: 'from-cyan-500/20 to-blue-500/20 border-cyan-500/30',
        green: 'from-green-500/20 to-emerald-500/20 border-green-500/30',
        red: 'from-red-500/20 to-rose-500/20 border-red-500/30',
        purple: 'from-purple-500/20 to-pink-500/20 border-purple-500/30',
        orange: 'from-orange-500/20 to-amber-500/20 border-orange-500/30',
    };

    const iconColors = {
        cyan: 'text-cyan-400',
        green: 'text-green-400',
        red: 'text-red-400',
        purple: 'text-purple-400',
        orange: 'text-orange-400',
    };

    return (
        <motion.div
            whileHover={{ scale: 1.02, y: -2 }}
            className={`relative overflow-hidden rounded-2xl border bg-gradient-to-br ${colorClasses[color]} p-5 backdrop-blur-xl`}
        >
            {/* Glow effect */}
            <div className={`absolute -top-10 -right-10 w-32 h-32 rounded-full blur-3xl opacity-30 bg-${color}-500`} />

            <div className="relative z-10">
                <div className="flex items-center justify-between mb-3">
                    <span className="text-sm text-gray-400 font-medium">{title}</span>
                    <div className={`p-2 rounded-lg bg-gray-800/50 ${iconColors[color]}`}>
                        <Icon className="w-4 h-4" />
                    </div>
                </div>

                <div className="flex items-end gap-2">
                    <span className="text-3xl font-bold text-white">
                        <AnimatedValue value={value} prefix={prefix} suffix={suffix} />
                    </span>
                    {isPositive !== undefined && (
                        <span className={`flex items-center text-sm ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
                            {isPositive ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
                        </span>
                    )}
                </div>

                {subValue && (
                    <p className="text-sm text-gray-400 mt-1">{subValue}</p>
                )}
            </div>
        </motion.div>
    );
};

export default function TradingSimulation() {
    const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
    const [session, setSession] = useState<TradingSession | null>(null);
    const [loading, setLoading] = useState(false);
    const [currentStrategy, setCurrentStrategy] = useState<Strategy>(STRATEGIES[0]);
    const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
    const [priceFlash, setPriceFlash] = useState<{ [key: string]: 'up' | 'down' | null }>({});

    // Fetch session details
    const fetchSessionDetails = useCallback(async () => {
        if (!selectedSessionId) {
            setSession(null);
            return;
        }

        try {
            const response = await fetch(`${API_URL}/trading/sessions/${selectedSessionId}`);
            if (response.ok) {
                const data = await response.json();

                // Check for price changes for flash effect
                if (session?.positions) {
                    const flashes: { [key: string]: 'up' | 'down' | null } = {};
                    data.session.positions?.forEach((newPos: Position) => {
                        const oldPos = session.positions?.find(p => p.symbol === newPos.symbol);
                        if (oldPos && oldPos.currentPrice !== newPos.currentPrice) {
                            flashes[newPos.symbol] = newPos.currentPrice > oldPos.currentPrice ? 'up' : 'down';
                        }
                    });
                    setPriceFlash(flashes);
                    setTimeout(() => setPriceFlash({}), 1000);
                }

                setSession(data.session);
                setLastUpdate(new Date());
            }
        } catch (error) {
            console.error('Error fetching session:', error);
        }
    }, [selectedSessionId, session?.positions]);

    // Auto-refresh session details
    useEffect(() => {
        fetchSessionDetails();
        const interval = setInterval(fetchSessionDetails, 5000);
        return () => clearInterval(interval);
    }, [selectedSessionId]); // Only depend on selectedSessionId to avoid infinite loop

    // Toggle session active state
    const toggleSession = async () => {
        if (!session) return;

        const endpoint = session.isActive ? 'stop' : 'start';
        try {
            const response = await fetch(
                `${API_URL}/trading/sessions/${session.id}/${endpoint}`,
                { method: 'POST' }
            );

            if (response.ok) {
                toast.success(session.isActive ? 'Session stopped' : 'Session started!');
                fetchSessionDetails();
            }
        } catch (error) {
            console.error('Error toggling session:', error);
            toast.error('Failed to update session');
        }
    };

    // Toggle auto-trade
    const toggleAutoTrade = async () => {
        if (!session) return;

        try {
            const response = await fetch(
                `${API_URL}/trading/sessions/${session.id}`,
                {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ autoTrade: !session.autoTrade })
                }
            );

            if (response.ok) {
                toast.success(session.autoTrade ? 'Auto-trade disabled' : 'Auto-trade enabled!');
                fetchSessionDetails();
            }
        } catch (error) {
            console.error('Error toggling auto-trade:', error);
        }
    };

    // Calculate totals from session
    const positions = session?.positions || [];
    const trades = session?.trades || [];
    const balance = session?.currentBalance || 0;
    const totalValue = balance + positions.reduce((sum, p) => sum + (p.quantity * p.currentPrice), 0);
    const totalPnL = session ? totalValue - session.initialBalance : 0;
    const totalPnLPercent = session ? (totalPnL / session.initialBalance) * 100 : 0;
    const unrealizedPnL = positions.reduce((sum, p) => sum + p.pnl, 0);
    const avgWinRate = session?.stats?.winRate || 0;

    return (
        <main className="min-h-screen bg-[#0a0b0f] text-white">
            {/* Animated background */}
            <div className="fixed inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-0 left-1/4 w-[600px] h-[600px] bg-cyan-500/10 rounded-full blur-[120px] animate-pulse" />
                <div className="absolute bottom-0 right-1/4 w-[500px] h-[500px] bg-purple-500/10 rounded-full blur-[120px] animate-pulse" style={{ animationDelay: '1s' }} />
                <div className="absolute top-1/2 left-1/2 w-[400px] h-[400px] bg-blue-500/5 rounded-full blur-[100px]" />
            </div>

            <div className="relative z-10 p-6 lg:p-8">
                <div className="max-w-7xl mx-auto">
                    {/* Header */}
                    <motion.div
                        initial={{ opacity: 0, y: -20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="mb-8"
                    >
                        <Link href="/" className="inline-flex items-center text-gray-400 hover:text-cyan-400 mb-4 transition-all group">
                            <ArrowLeft className="w-4 h-4 mr-2 group-hover:-translate-x-1 transition-transform" />
                            Retour au Dashboard
                        </Link>

                        <div className="flex flex-col lg:flex-row lg:justify-between lg:items-center gap-4">
                            <div>
                                <h1 className="text-4xl lg:text-5xl font-bold mb-2 flex items-center gap-3">
                                    <span className="bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-500 bg-clip-text text-transparent">
                                        Trading Bot
                                    </span>
                                    <Sparkles className="w-8 h-8 text-yellow-400 animate-pulse" />
                                </h1>
                                <div className="flex items-center gap-4 text-sm">
                                    <span className="flex items-center gap-2 text-gray-400">
                                        <Server className="w-4 h-4" />
                                        24/7 Server-side Trading
                                    </span>
                                    <span className="flex items-center gap-2 text-gray-500">
                                        <Clock className="w-4 h-4" />
                                        Last update: {lastUpdate.toLocaleTimeString()}
                                    </span>
                                </div>
                            </div>

                            {session && (
                                <div className="flex flex-wrap gap-3">
                                    <Button
                                        variant={session.autoTrade ? "success" : "secondary"}
                                        size="lg"
                                        onClick={toggleAutoTrade}
                                        disabled={!session.isActive}
                                        leftIcon={session.autoTrade ? <Zap className="w-5 h-5 animate-pulse" /> : <Pause className="w-5 h-5" />}
                                        className={session.autoTrade ? 'shadow-lg shadow-green-500/25' : ''}
                                    >
                                        {session.autoTrade ? 'Auto-Trading' : 'Manual Mode'}
                                    </Button>
                                    <Button
                                        variant={session.isActive ? "danger" : "primary"}
                                        size="lg"
                                        onClick={toggleSession}
                                        leftIcon={session.isActive ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
                                        className={session.isActive ? 'shadow-lg shadow-red-500/25' : 'shadow-lg shadow-cyan-500/25'}
                                    >
                                        {session.isActive ? 'Stop Bot' : 'Start Bot'}
                                    </Button>
                                </div>
                            )}
                        </div>
                    </motion.div>

                    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                        {/* Session Manager - Left Column */}
                        <motion.div
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            className="lg:col-span-4"
                        >
                            <SessionManager
                                selectedSessionId={selectedSessionId}
                                onSelectSession={setSelectedSessionId}
                                onSessionsChange={fetchSessionDetails}
                            />
                        </motion.div>

                        {/* Session Details - Right Columns */}
                        <div className="lg:col-span-8">
                            {!selectedSessionId ? (
                                <motion.div
                                    initial={{ opacity: 0, scale: 0.95 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                >
                                    <Card variant="glass" className="border-dashed border-2 border-gray-700">
                                        <CardContent className="p-16 text-center">
                                            <div className="w-24 h-24 mx-auto mb-6 rounded-full bg-gradient-to-br from-cyan-500/20 to-purple-500/20 flex items-center justify-center">
                                                <LineChart className="w-12 h-12 text-cyan-400" />
                                            </div>
                                            <h3 className="text-2xl font-bold mb-3">Select a Trading Session</h3>
                                            <p className="text-gray-400 max-w-md mx-auto">
                                                Choose an existing session or create a new one to start automated trading with your preferred strategy.
                                            </p>
                                        </CardContent>
                                    </Card>
                                </motion.div>
                            ) : !session ? (
                                <Card variant="glass">
                                    <CardContent className="p-16 text-center">
                                        <RefreshCw className="w-12 h-12 animate-spin mx-auto mb-4 text-cyan-400" />
                                        <p className="text-gray-400">Loading session data...</p>
                                    </CardContent>
                                </Card>
                            ) : (
                                <motion.div
                                    initial="initial"
                                    animate="animate"
                                    variants={staggerContainer}
                                    className="space-y-6"
                                >
                                    {/* Stats Grid */}
                                    <motion.div variants={staggerItem} className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                                        <StatCard
                                            title="Portfolio Value"
                                            value={totalValue}
                                            prefix="$"
                                            subValue={`${totalPnL >= 0 ? '+' : ''}${totalPnLPercent.toFixed(2)}% total`}
                                            icon={Wallet}
                                            color={totalPnL >= 0 ? 'green' : 'red'}
                                            isPositive={totalPnL >= 0}
                                        />
                                        <StatCard
                                            title="Cash Balance"
                                            value={balance}
                                            prefix="$"
                                            subValue={`${totalValue > 0 ? ((balance / totalValue) * 100).toFixed(0) : 0}% available`}
                                            icon={DollarSign}
                                            color="cyan"
                                        />
                                        <StatCard
                                            title="Win Rate"
                                            value={avgWinRate}
                                            suffix="%"
                                            subValue={`${session.stats.winningTrades}W / ${session.stats.losingTrades}L`}
                                            icon={Target}
                                            color={avgWinRate >= 50 ? 'green' : 'orange'}
                                        />
                                        <StatCard
                                            title="Total Trades"
                                            value={session.stats.totalTrades}
                                            subValue={`${positions.length} open positions`}
                                            icon={BarChart3}
                                            color="purple"
                                        />
                                    </motion.div>

                                    {/* Session Info Banner */}
                                    <motion.div variants={staggerItem}>
                                        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-gray-900 via-gray-800 to-gray-900 border border-gray-700/50 p-6">
                                            {/* Animated gradient border */}
                                            <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-cyan-500/20 via-purple-500/20 to-cyan-500/20 opacity-50"
                                                style={{ backgroundSize: '200% 100%', animation: 'shimmer 3s linear infinite' }} />

                                            <div className="relative z-10">
                                                <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
                                                    <div className="flex items-center gap-3">
                                                        <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${session.strategy.name === 'High Gain'
                                                                ? 'bg-gradient-to-br from-orange-500/30 to-red-500/30'
                                                                : 'bg-gradient-to-br from-cyan-500/30 to-blue-500/30'
                                                            }`}>
                                                            {session.strategy.name === 'High Gain' ? (
                                                                <Flame className="w-6 h-6 text-orange-400" />
                                                            ) : (
                                                                <Shield className="w-6 h-6 text-cyan-400" />
                                                            )}
                                                        </div>
                                                        <div>
                                                            <h3 className="font-bold text-lg">{session.name}</h3>
                                                            <p className="text-sm text-gray-400">Strategy: {session.strategy.name}</p>
                                                        </div>
                                                    </div>

                                                    <div className="flex items-center gap-2">
                                                        <Badge
                                                            variant={session.isActive ? "success" : "default"}
                                                            className={session.isActive ? 'animate-pulse' : ''}
                                                        >
                                                            {session.isActive ? '🟢 Live' : '⚪ Stopped'}
                                                        </Badge>
                                                        {session.autoTrade && (
                                                            <Badge variant="info" className="flex items-center gap-1">
                                                                <Zap className="w-3 h-3" />
                                                                Auto
                                                            </Badge>
                                                        )}
                                                    </div>
                                                </div>

                                                <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
                                                    <div className="bg-gray-800/50 rounded-lg p-3">
                                                        <span className="text-gray-400 block text-xs mb-1">Risk/Trade</span>
                                                        <span className="font-bold text-cyan-400">{(session.strategy.riskPerTrade * 100).toFixed(1)}%</span>
                                                    </div>
                                                    <div className="bg-gray-800/50 rounded-lg p-3">
                                                        <span className="text-gray-400 block text-xs mb-1">Stop-Loss</span>
                                                        <span className="font-bold text-red-400">-{(session.strategy.stopLoss * 100).toFixed(1)}%</span>
                                                    </div>
                                                    <div className="bg-gray-800/50 rounded-lg p-3">
                                                        <span className="text-gray-400 block text-xs mb-1">Take-Profit</span>
                                                        <span className="font-bold text-green-400">+{(session.strategy.takeProfit * 100).toFixed(1)}%</span>
                                                    </div>
                                                    <div className="bg-gray-800/50 rounded-lg p-3">
                                                        <span className="text-gray-400 block text-xs mb-1">Max Positions</span>
                                                        <span className="font-bold">{session.strategy.maxPositions}</span>
                                                    </div>
                                                    <div className="bg-gray-800/50 rounded-lg p-3">
                                                        <span className="text-gray-400 block text-xs mb-1">R/R Ratio</span>
                                                        <span className="font-bold text-purple-400">1:{(session.strategy.takeProfit / session.strategy.stopLoss).toFixed(1)}</span>
                                                    </div>
                                                </div>

                                                <div className="mt-4 flex flex-wrap gap-2">
                                                    {session.symbols.map(s => (
                                                        <Badge key={s} variant="default" size="sm" className="bg-gray-800/50">
                                                            {s.replace('USDT', '')}
                                                        </Badge>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>
                                    </motion.div>

                                    {/* Positions and Trades */}
                                    <motion.div variants={staggerItem} className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                        {/* Open Positions */}
                                        <Card variant="glass" className="overflow-hidden">
                                            <CardHeader className="border-b border-gray-700/50">
                                                <div className="flex justify-between items-center">
                                                    <CardTitle className="flex items-center gap-2">
                                                        <PieChart className="w-5 h-5 text-cyan-400" />
                                                        Open Positions
                                                    </CardTitle>
                                                    <Badge variant="info" className="font-mono">{positions.length}</Badge>
                                                </div>
                                            </CardHeader>
                                            <CardContent className="p-0">
                                                {positions.length === 0 ? (
                                                    <div className="text-center text-gray-500 py-12">
                                                        <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-800/50 flex items-center justify-center">
                                                            <TrendingUp className="w-8 h-8 text-gray-600" />
                                                        </div>
                                                        No open positions
                                                    </div>
                                                ) : (
                                                    <div className="divide-y divide-gray-700/50">
                                                        {positions.map((pos) => (
                                                            <motion.div
                                                                key={pos.id}
                                                                className={`p-4 transition-colors ${priceFlash[pos.symbol] === 'up' ? 'bg-green-500/10' :
                                                                        priceFlash[pos.symbol] === 'down' ? 'bg-red-500/10' : ''
                                                                    }`}
                                                                layout
                                                            >
                                                                <div className="flex justify-between items-start">
                                                                    <div>
                                                                        <div className="flex items-center gap-2">
                                                                            <span className="font-bold text-lg">{pos.symbol.replace('USDT', '')}</span>
                                                                            <span className="text-xs text-gray-500">/USDT</span>
                                                                        </div>
                                                                        <p className="text-sm text-gray-400 mt-1">
                                                                            Qty: <span className="font-mono">{pos.quantity.toFixed(4)}</span>
                                                                        </p>
                                                                        <p className="text-xs text-gray-500 mt-1">
                                                                            Entry: ${pos.averagePrice.toFixed(2)} →
                                                                            <span className={`ml-1 font-bold ${pos.currentPrice > pos.averagePrice ? 'text-green-400' : 'text-red-400'
                                                                                }`}>
                                                                                ${pos.currentPrice.toFixed(2)}
                                                                            </span>
                                                                        </p>
                                                                    </div>
                                                                    <div className="text-right">
                                                                        <p className={`text-xl font-bold ${pos.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                                                            {pos.pnl >= 0 ? '+' : ''}${pos.pnl.toFixed(2)}
                                                                        </p>
                                                                        <div className="text-xs text-gray-500 mt-2 space-y-1">
                                                                            <p>SL: <span className="text-red-400">${pos.stopLoss.toFixed(2)}</span></p>
                                                                            <p>TP: <span className="text-green-400">${pos.takeProfit.toFixed(2)}</span></p>
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                                {/* Progress bar to TP/SL */}
                                                                <div className="mt-3 h-1.5 bg-gray-700 rounded-full overflow-hidden">
                                                                    <div
                                                                        className={`h-full transition-all ${pos.pnl >= 0 ? 'bg-green-500' : 'bg-red-500'}`}
                                                                        style={{
                                                                            width: `${Math.min(100, Math.abs(pos.pnl / (pos.quantity * pos.averagePrice * (session?.strategy.takeProfit || 0.06))) * 100)}%`
                                                                        }}
                                                                    />
                                                                </div>
                                                            </motion.div>
                                                        ))}
                                                    </div>
                                                )}
                                            </CardContent>
                                        </Card>

                                        {/* Trade History */}
                                        <Card variant="glass" className="overflow-hidden">
                                            <CardHeader className="border-b border-gray-700/50">
                                                <div className="flex justify-between items-center">
                                                    <CardTitle className="flex items-center gap-2">
                                                        <Activity className="w-5 h-5 text-purple-400" />
                                                        Trade History
                                                    </CardTitle>
                                                    <Badge variant="default" className="font-mono">{trades.length}</Badge>
                                                </div>
                                            </CardHeader>
                                            <CardContent className="p-0">
                                                {trades.length === 0 ? (
                                                    <div className="text-center text-gray-500 py-12">
                                                        <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-800/50 flex items-center justify-center">
                                                            <BarChart3 className="w-8 h-8 text-gray-600" />
                                                        </div>
                                                        No trades yet
                                                    </div>
                                                ) : (
                                                    <div className="divide-y divide-gray-700/50 max-h-[400px] overflow-y-auto">
                                                        <AnimatePresence>
                                                            {trades.slice(0, 20).map((trade, index) => (
                                                                <motion.div
                                                                    key={trade.id}
                                                                    initial={{ opacity: 0, x: -20 }}
                                                                    animate={{ opacity: 1, x: 0 }}
                                                                    transition={{ delay: index * 0.05 }}
                                                                    className="p-4 hover:bg-gray-800/30 transition-colors"
                                                                >
                                                                    <div className="flex justify-between items-center">
                                                                        <div className="flex items-center gap-3">
                                                                            <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${trade.type === 'BUY'
                                                                                    ? 'bg-green-500/20 text-green-400'
                                                                                    : 'bg-red-500/20 text-red-400'
                                                                                }`}>
                                                                                {trade.type === 'BUY' ? (
                                                                                    <ArrowUpRight className="w-5 h-5" />
                                                                                ) : (
                                                                                    <ArrowDownRight className="w-5 h-5" />
                                                                                )}
                                                                            </div>
                                                                            <div>
                                                                                <p className="font-bold">{trade.symbol.replace('USDT', '')}</p>
                                                                                <p className="text-xs text-gray-500">
                                                                                    {new Date(trade.timestamp).toLocaleString()}
                                                                                </p>
                                                                            </div>
                                                                        </div>
                                                                        <div className="text-right">
                                                                            <p className="font-mono font-bold">${trade.price.toFixed(2)}</p>
                                                                            {trade.type === 'SELL' && (
                                                                                <p className={`text-sm font-bold ${trade.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                                                                    {trade.pnl >= 0 ? '+' : ''}${trade.pnl.toFixed(2)}
                                                                                </p>
                                                                            )}
                                                                        </div>
                                                                    </div>
                                                                </motion.div>
                                                            ))}
                                                        </AnimatePresence>
                                                    </div>
                                                )}
                                            </CardContent>
                                        </Card>
                                    </motion.div>
                                </motion.div>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* CSS for shimmer animation */}
            <style jsx>{`
                @keyframes shimmer {
                    0% { background-position: -200% 0; }
                    100% { background-position: 200% 0; }
                }
            `}</style>
        </main>
    );
}
