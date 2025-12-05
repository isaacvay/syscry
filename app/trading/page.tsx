'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { ArrowLeft, Play, Pause, Activity, TrendingUp, TrendingDown, Target, BarChart3 } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import TradingStrategy, { STRATEGIES, Strategy } from '../components/TradingStrategy';
import PortfolioChart from '../components/PortfolioChart';
import { staggerContainer, staggerItem } from '../animations';
import toast from 'react-hot-toast';

interface Trade {
    id: string;
    symbol: string;
    type: 'BUY' | 'SELL';
    price: number;
    quantity: number;
    timestamp: Date;
    confidence: number;
    signal: string;
}

interface Position {
    symbol: string;
    quantity: number;
    averagePrice: number;
    currentPrice: number;
    pnl: number;
    stopLoss: number;
    takeProfit: number;
    trailingStopPrice?: number;
}

interface Stats {
    totalTrades: number;
    winningTrades: number;
    losingTrades: number;
    winRate: number;
}

export default function TradingSimulation() {
    const [isActive, setIsActive] = useState(false);
    const [autoTrade, setAutoTrade] = useState(false);
    const [balance, setBalance] = useState(10000);
    const [trades, setTrades] = useState<Trade[]>([]);
    const [positions, setPositions] = useState<Position[]>([]);
    const [stats, setStats] = useState<Stats>({
        totalTrades: 0,
        winningTrades: 0,
        losingTrades: 0,
        winRate: 0,
    });
    const [portfolioHistory, setPortfolioHistory] = useState<{ time: number; value: number }[]>([]);
    const [currentStrategy, setCurrentStrategy] = useState<Strategy>(STRATEGIES[1]); // Default: Balanced
    const [initialBalance, setInitialBalance] = useState(10000);

    const selectedSymbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT'];

    const totalValue = balance + positions.reduce((sum, p) => sum + (p.quantity * p.currentPrice), 0);
    const totalPnL = totalValue - initialBalance;
    const totalPnLPercent = (totalPnL / initialBalance) * 100;

    // Fetch signals from API and execute trades
    const fetchSignalsAndTrade = useCallback(async () => {
        if (!isActive || !autoTrade) return;

        try {
            const response = await fetch('http://localhost:8000/signals/multi', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ symbols: selectedSymbols }),
            });

            if (!response.ok) {
                console.error('Failed to fetch signals');
                return;
            }

            const data = await response.json();

            // Execute trades based on signals
            for (const signalData of data.signals) {
                if (signalData.signal === 'BUY' && signalData.confidence > 0.6) {
                    executeTrade(
                        signalData.symbol,
                        'BUY',
                        signalData.current_price,
                        signalData.confidence,
                        signalData.signal
                    );
                } else if (signalData.signal === 'SELL' && signalData.confidence > 0.6) {
                    // Check if we have a position to sell
                    const position = positions.find(p => p.symbol === signalData.symbol);
                    if (position) {
                        executeTrade(
                            signalData.symbol,
                            'SELL',
                            signalData.current_price,
                            signalData.confidence,
                            signalData.signal
                        );
                    }
                }
            }
        } catch (error) {
            console.error('Error fetching signals:', error);
        }
    }, [isActive, autoTrade, selectedSymbols, positions]);

    // Execute a trade
    const executeTrade = (
        symbol: string,
        type: 'BUY' | 'SELL',
        price: number,
        confidence: number,
        signal: string
    ) => {
        const riskAmount = balance * currentStrategy.riskPerTrade;
        const quantity = riskAmount / price;

        if (type === 'BUY') {
            // Check max positions limit
            if (positions.length >= currentStrategy.maxPositions) {
                toast.error(`Maximum de ${currentStrategy.maxPositions} positions atteint`);
                return;
            }

            const cost = quantity * price;
            if (cost > balance) {
                toast.error(`Solde insuffisant pour acheter ${symbol}`);
                return;
            }

            // Calculate stop-loss and take-profit
            const stopLoss = price * (1 - currentStrategy.stopLoss);
            const takeProfit = price * (1 + currentStrategy.takeProfit);

            // Deduct from balance
            setBalance(prev => prev - cost);

            // Update or create position
            setPositions(prev => {
                const existingPosition = prev.find(p => p.symbol === symbol);
                if (existingPosition) {
                    const totalQuantity = existingPosition.quantity + quantity;
                    const totalCost = (existingPosition.averagePrice * existingPosition.quantity) + cost;
                    const newAvgPrice = totalCost / totalQuantity;
                    const newStopLoss = newAvgPrice * (1 - currentStrategy.stopLoss);
                    const newTakeProfit = newAvgPrice * (1 + currentStrategy.takeProfit);

                    return prev.map(p =>
                        p.symbol === symbol
                            ? {
                                ...p,
                                quantity: totalQuantity,
                                averagePrice: newAvgPrice,
                                currentPrice: price,
                                stopLoss: newStopLoss,
                                takeProfit: newTakeProfit,
                            }
                            : p
                    );
                } else {
                    return [
                        ...prev,
                        {
                            symbol,
                            quantity,
                            averagePrice: price,
                            currentPrice: price,
                            pnl: 0,
                            stopLoss,
                            takeProfit,
                        },
                    ];
                }
            });

            // Add trade to history
            const newTrade: Trade = {
                id: Date.now().toString(),
                symbol,
                type,
                price,
                quantity,
                timestamp: new Date(),
                confidence,
                signal,
            };
            setTrades(prev => [newTrade, ...prev]);

            toast.success(`✅ Achat: ${quantity.toFixed(6)} ${symbol} à $${price.toFixed(2)}`);
        } else if (type === 'SELL') {
            const position = positions.find(p => p.symbol === symbol);
            if (!position) {
                toast.error(`Aucune position ${symbol} à vendre`);
                return;
            }

            const revenue = position.quantity * price;
            const cost = position.averagePrice * position.quantity;
            const pnl = revenue - cost;

            // Add to balance
            setBalance(prev => prev + revenue);

            // Remove position
            setPositions(prev => prev.filter(p => p.symbol !== symbol));

            // Add trade to history
            const newTrade: Trade = {
                id: Date.now().toString(),
                symbol,
                type,
                price,
                quantity: position.quantity,
                timestamp: new Date(),
                confidence,
                signal,
            };
            setTrades(prev => [newTrade, ...prev]);

            // Update stats - track wins and losses
            setStats(prev => ({
                ...prev,
                totalTrades: prev.totalTrades + 1,
                winningTrades: pnl > 0 ? prev.winningTrades + 1 : prev.winningTrades,
                losingTrades: pnl < 0 ? prev.losingTrades + 1 : prev.losingTrades,
            }));

            const pnlColor = pnl >= 0 ? '🟢' : '🔴';
            toast.success(`${pnlColor} Vente: ${position.quantity.toFixed(6)} ${symbol} - P&L: $${pnl.toFixed(2)}`);
        }
    };

    // Update positions with current prices periodically
    useEffect(() => {
        if (!isActive) return;

        const interval = setInterval(() => {
            setPositions(prev =>
                prev.map(position => {
                    // Simulate price movement (±0.5%)
                    const priceChange = (Math.random() - 0.5) * 0.01;
                    const newPrice = position.currentPrice * (1 + priceChange);
                    const pnl = (newPrice - position.averagePrice) * position.quantity;

                    // Update trailing stop if enabled
                    let newTrailingStop = position.trailingStopPrice;
                    if (currentStrategy.trailingStop && pnl > 0) {
                        const trailingStopPrice = newPrice * (1 - currentStrategy.stopLoss);
                        if (!newTrailingStop || trailingStopPrice > newTrailingStop) {
                            newTrailingStop = trailingStopPrice;
                        }
                    }

                    return {
                        ...position,
                        currentPrice: newPrice,
                        pnl,
                        trailingStopPrice: newTrailingStop,
                    };
                })
            );
        }, 5000); // Update every 5 seconds

        return () => clearInterval(interval);
    }, [isActive, currentStrategy]);

    // Check stop-loss and take-profit levels
    useEffect(() => {
        if (!isActive || positions.length === 0) return;

        const checkStopLossTakeProfit = () => {
            positions.forEach(position => {
                const effectiveStopLoss = position.trailingStopPrice || position.stopLoss;

                // Check stop-loss
                if (position.currentPrice <= effectiveStopLoss) {
                    executeTrade(
                        position.symbol,
                        'SELL',
                        position.currentPrice,
                        1.0,
                        'STOP_LOSS'
                    );
                    toast.error(`🛑 Stop-Loss déclenché pour ${position.symbol}`);
                }
                // Check take-profit
                else if (position.currentPrice >= position.takeProfit) {
                    executeTrade(
                        position.symbol,
                        'SELL',
                        position.currentPrice,
                        1.0,
                        'TAKE_PROFIT'
                    );
                    toast.success(`🎯 Take-Profit atteint pour ${position.symbol}`);
                }
            });
        };

        const interval = setInterval(checkStopLossTakeProfit, 5000); // Check every 5 seconds
        return () => clearInterval(interval);
    }, [isActive, positions]);

    // Fetch signals periodically when auto-trading is active
    useEffect(() => {
        if (!isActive || !autoTrade) return;

        // Fetch immediately
        fetchSignalsAndTrade();

        // Then fetch every 30 seconds
        const interval = setInterval(() => {
            fetchSignalsAndTrade();
        }, 30000);

        return () => clearInterval(interval);
    }, [isActive, autoTrade, fetchSignalsAndTrade]);

    // Calculate win rate whenever stats change
    useEffect(() => {
        if (stats.totalTrades > 0) {
            const winRate = (stats.winningTrades / stats.totalTrades) * 100;
            setStats(prev => ({ ...prev, winRate }));
        }
    }, [stats.totalTrades, stats.winningTrades]);

    // Track portfolio value over time
    useEffect(() => {
        if (!isActive) return;

        const interval = setInterval(() => {
            setPortfolioHistory(prev => [
                ...prev,
                { time: Math.floor(Date.now() / 1000), value: totalValue }
            ]);
        }, 10000); // Update every 10 seconds

        return () => clearInterval(interval);
    }, [isActive, totalValue]);

    const handleStartStop = () => {
        if (!isActive) {
            // Reset everything
            setBalance(initialBalance);
            setTrades([]);
            setPositions([]);
            setStats({
                totalTrades: 0,
                winningTrades: 0,
                losingTrades: 0,
                winRate: 0,
            });
            setPortfolioHistory([{ time: Math.floor(Date.now() / 1000), value: initialBalance }]);
        }
        setIsActive(!isActive);
    };

    return (
        <main className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-900 to-gray-800 text-white p-8">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <Link href="/" className="inline-flex items-center text-gray-400 hover:text-white mb-4 transition-colors">
                        <ArrowLeft className="w-4 h-4 mr-2" />
                        Retour au Dashboard
                    </Link>
                    <div className="flex justify-between items-center">
                        <div>
                            <h1 className="text-4xl font-bold mb-2">
                                <span className="bg-gradient-to-r from-cyan-400 to-purple-500 bg-clip-text text-transparent">
                                    Live Simulation
                                </span>
                            </h1>
                            <p className="text-gray-400">Testez vos stratégies en temps réel</p>
                        </div>
                        <div className="flex gap-3">
                            <Button
                                variant={autoTrade ? "success" : "secondary"}
                                size="md"
                                onClick={() => setAutoTrade(!autoTrade)}
                                disabled={!isActive}
                                leftIcon={autoTrade ? <Activity className="w-4 h-4 animate-pulse" /> : <Pause className="w-4 h-4" />}
                            >
                                {autoTrade ? 'Trading Actif' : 'Trading En Pause'}
                            </Button>
                            <Button
                                variant={isActive ? "danger" : "primary"}
                                size="md"
                                onClick={handleStartStop}
                                leftIcon={isActive ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                            >
                                {isActive ? 'Arrêter' : 'Démarrer'}
                            </Button>
                        </div>
                    </div>
                </div>

                {/* Content - Only show when active */}
                {!isActive ? (
                    <div className="space-y-6">
                        {/* Initial Balance Configuration */}
                        <Card variant="glass">
                            <CardContent className="p-6">
                                <div className="flex items-center gap-2 mb-4">
                                    <div className="p-2 bg-cyan-500/10 rounded-lg">
                                        <svg className="w-5 h-5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                        </svg>
                                    </div>
                                    <h3 className="text-lg font-bold">Capital Initial</h3>
                                </div>
                                <div className="flex items-center gap-4">
                                    <div className="flex-1">
                                        <label className="block text-sm text-gray-400 mb-2">
                                            Montant de départ (USD)
                                        </label>
                                        <input
                                            type="number"
                                            min="100"
                                            max="1000000"
                                            step="100"
                                            value={initialBalance}
                                            onChange={(e) => setInitialBalance(Number(e.target.value))}
                                            className="w-full px-4 py-3 bg-gray-800/50 border border-gray-700 rounded-lg text-white font-bold text-xl focus:outline-none focus:border-cyan-500 transition-colors"
                                        />
                                    </div>
                                    <div className="flex gap-2">
                                        <button
                                            onClick={() => setInitialBalance(5000)}
                                            className="px-3 py-2 bg-gray-700/50 hover:bg-gray-700 rounded-lg text-sm text-gray-300 transition-colors"
                                        >
                                            $5K
                                        </button>
                                        <button
                                            onClick={() => setInitialBalance(10000)}
                                            className="px-3 py-2 bg-gray-700/50 hover:bg-gray-700 rounded-lg text-sm text-gray-300 transition-colors"
                                        >
                                            $10K
                                        </button>
                                        <button
                                            onClick={() => setInitialBalance(50000)}
                                            className="px-3 py-2 bg-gray-700/50 hover:bg-gray-700 rounded-lg text-sm text-gray-300 transition-colors"
                                        >
                                            $50K
                                        </button>
                                    </div>
                                </div>
                                <div className="mt-4 p-3 bg-cyan-500/10 border border-cyan-500/20 rounded-lg">
                                    <p className="text-xs text-cyan-300">
                                        💡 Avec la stratégie <span className="font-bold">{currentStrategy.name}</span>,
                                        chaque trade risquera <span className="font-bold">${(initialBalance * currentStrategy.riskPerTrade).toFixed(2)}</span> ({(currentStrategy.riskPerTrade * 100).toFixed(0)}% du capital)
                                    </p>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Strategy Selection */}
                        <TradingStrategy
                            currentStrategy={currentStrategy}
                            onStrategyChange={setCurrentStrategy}
                        />
                        <div className="text-center py-12">
                            <p className="text-gray-400 text-lg mb-4">
                                Sélectionnez une stratégie et cliquez sur "Démarrer" pour lancer la simulation
                            </p>
                            <div className="flex items-center justify-center gap-4 text-sm text-gray-500">
                                <div className="flex items-center gap-2">
                                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                                    <span>Stop-Loss: {(currentStrategy.stopLoss * 100).toFixed(0)}%</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <div className="w-2 h-2 bg-cyan-500 rounded-full"></div>
                                    <span>Take-Profit: {(currentStrategy.takeProfit * 100).toFixed(0)}%</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                                    <span>Max Positions: {currentStrategy.maxPositions}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                ) : (
                    <motion.div
                        initial="initial"
                        animate="animate"
                        variants={staggerContainer}
                        className="space-y-6"
                    >
                        {/* Stats Cards */}
                        <motion.div variants={staggerItem} className="grid grid-cols-1 md:grid-cols-4 gap-4">
                            <Card variant="glass">
                                <CardContent className="p-6">
                                    <p className="text-sm text-gray-400 mb-2">Valeur Portfolio</p>
                                    <p className="text-2xl font-bold">${totalValue.toFixed(2)}</p>
                                    <p className={`text-sm ${totalPnL >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                        {totalPnL >= 0 ? '+' : ''}{totalPnLPercent.toFixed(2)}%
                                    </p>
                                </CardContent>
                            </Card>

                            <Card variant="glass">
                                <CardContent className="p-6">
                                    <p className="text-sm text-gray-400 mb-2">Liquidités</p>
                                    <p className="text-2xl font-bold">${balance.toFixed(2)}</p>
                                    <p className="text-sm text-gray-400">
                                        {((balance / totalValue) * 100).toFixed(1)}% cash
                                    </p>
                                </CardContent>
                            </Card>

                            <Card variant="glass">
                                <CardContent className="p-6">
                                    <p className="text-sm text-gray-400 mb-2">Win Rate</p>
                                    <p className="text-2xl font-bold">{stats.winRate.toFixed(1)}%</p>
                                    <p className="text-sm text-gray-400">
                                        {stats.winningTrades}W / {stats.losingTrades}L
                                    </p>
                                </CardContent>
                            </Card>

                            <Card variant="glass">
                                <CardContent className="p-6">
                                    <p className="text-sm text-gray-400 mb-2">Total Trades</p>
                                    <p className="text-2xl font-bold">{stats.totalTrades}</p>
                                    <p className="text-sm text-gray-400">
                                        {positions.length} positions ouvertes
                                    </p>
                                </CardContent>
                            </Card>
                        </motion.div>

                        {/* Portfolio Performance Chart */}
                        {portfolioHistory.length > 1 && (
                            <motion.div variants={staggerItem}>
                                <Card variant="gradient">
                                    <CardHeader>
                                        <CardTitle>Performance du Portfolio</CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                        <PortfolioChart
                                            data={portfolioHistory}
                                            initialBalance={initialBalance}
                                        />
                                    </CardContent>
                                </Card>
                            </motion.div>
                        )}

                        {/* Advanced Statistics */}
                        {stats.totalTrades > 0 && (
                            <motion.div variants={staggerItem}>
                                <Card variant="glass">
                                    <CardHeader>
                                        <CardTitle>Statistiques Avancées</CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                            {/* Sharpe Ratio */}
                                            <div className="bg-gray-800/30 p-4 rounded-lg">
                                                <div className="flex items-center gap-2 mb-2">
                                                    <BarChart3 className="w-4 h-4 text-blue-400" />
                                                    <p className="text-xs text-gray-400">Sharpe Ratio</p>
                                                </div>
                                                <p className="text-xl font-bold text-cyan-400">
                                                    {(() => {
                                                        if (portfolioHistory.length < 2) return '0.00';
                                                        const returns = [];
                                                        for (let i = 1; i < portfolioHistory.length; i++) {
                                                            const ret = (portfolioHistory[i].value - portfolioHistory[i - 1].value) / portfolioHistory[i - 1].value;
                                                            returns.push(ret);
                                                        }
                                                        const avgReturn = returns.reduce((sum, r) => sum + r, 0) / returns.length;
                                                        const variance = returns.reduce((sum, r) => sum + Math.pow(r - avgReturn, 2), 0) / returns.length;
                                                        const stdDev = Math.sqrt(variance);
                                                        const sharpe = stdDev === 0 ? 0 : (avgReturn / stdDev) * Math.sqrt(252);
                                                        return sharpe.toFixed(2);
                                                    })()}
                                                </p>
                                                <p className="text-xs text-gray-500 mt-1">Rendement/Risque</p>
                                            </div>

                                            {/* Max Drawdown */}
                                            <div className="bg-gray-800/30 p-4 rounded-lg">
                                                <div className="flex items-center gap-2 mb-2">
                                                    <TrendingDown className="w-4 h-4 text-red-400" />
                                                    <p className="text-xs text-gray-400">Max Drawdown</p>
                                                </div>
                                                <p className="text-xl font-bold text-red-400">
                                                    {(() => {
                                                        if (portfolioHistory.length < 2) return '0.0%';
                                                        let maxDD = 0;
                                                        let peak = portfolioHistory[0].value;
                                                        for (const point of portfolioHistory) {
                                                            if (point.value > peak) peak = point.value;
                                                            const dd = ((peak - point.value) / peak) * 100;
                                                            if (dd > maxDD) maxDD = dd;
                                                        }
                                                        return maxDD.toFixed(1) + '%';
                                                    })()}
                                                </p>
                                                <p className="text-xs text-gray-500 mt-1">Perte max</p>
                                            </div>

                                            {/* Profit Factor */}
                                            <div className="bg-gray-800/30 p-4 rounded-lg">
                                                <div className="flex items-center gap-2 mb-2">
                                                    <Target className="w-4 h-4 text-purple-400" />
                                                    <p className="text-xs text-gray-400">Profit Factor</p>
                                                </div>
                                                <p className="text-xl font-bold text-purple-400">
                                                    {(() => {
                                                        if (stats.losingTrades === 0) return stats.winningTrades > 0 ? '∞' : '0.00';
                                                        const avgWin = stats.winningTrades > 0 ? totalPnL / stats.winningTrades : 0;
                                                        const avgLoss = stats.losingTrades > 0 ? Math.abs(totalPnL) / stats.losingTrades : 1;
                                                        const pf = avgLoss === 0 ? 0 : (stats.winningTrades * Math.abs(avgWin)) / (stats.losingTrades * Math.abs(avgLoss));
                                                        return pf.toFixed(2);
                                                    })()}
                                                </p>
                                                <p className="text-xs text-gray-500 mt-1">Gains/Pertes</p>
                                            </div>

                                            {/* ROI */}
                                            <div className="bg-gray-800/30 p-4 rounded-lg">
                                                <div className="flex items-center gap-2 mb-2">
                                                    <TrendingUp className="w-4 h-4 text-green-400" />
                                                    <p className="text-xs text-gray-400">ROI</p>
                                                </div>
                                                <p className={`text-xl font-bold ${totalPnLPercent >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                                    {totalPnLPercent >= 0 ? '+' : ''}{totalPnLPercent.toFixed(1)}%
                                                </p>
                                                <p className="text-xs text-gray-500 mt-1">Return on Investment</p>
                                            </div>
                                        </div>
                                    </CardContent>
                                </Card>
                            </motion.div>
                        )}

                        {/* Positions and Trades */}
                        <motion.div variants={staggerItem}>
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                {/* Positions */}
                                <Card variant="glass">
                                    <CardHeader>
                                        <div className="flex justify-between items-center">
                                            <CardTitle>Positions Ouvertes</CardTitle>
                                            <Badge variant="info">{positions.length}</Badge>
                                        </div>
                                    </CardHeader>
                                    <CardContent>
                                        {positions.length === 0 ? (
                                            <div className="text-center text-gray-500 py-8">
                                                Aucune position ouverte
                                            </div>
                                        ) : (
                                            <div className="space-y-3">
                                                {positions.map((pos, idx) => (
                                                    <div key={idx} className="bg-gray-800/50 p-4 rounded-lg">
                                                        <div className="flex justify-between">
                                                            <div>
                                                                <p className="font-bold">{pos.symbol}</p>
                                                                <p className="text-sm text-gray-400">Qté: {pos.quantity.toFixed(6)}</p>
                                                            </div>
                                                            <div className="text-right">
                                                                <p className={pos.pnl >= 0 ? 'text-green-400' : 'text-red-400'}>
                                                                    {pos.pnl >= 0 ? '+' : ''}${pos.pnl.toFixed(2)}
                                                                </p>
                                                            </div>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </CardContent>
                                </Card>

                                {/* Trades */}
                                <Card variant="glass">
                                    <CardHeader>
                                        <div className="flex justify-between items-center">
                                            <CardTitle>Historique des Trades</CardTitle>
                                            <Badge variant="default">{trades.length}</Badge>
                                        </div>
                                    </CardHeader>
                                    <CardContent>
                                        {trades.length === 0 ? (
                                            <div className="text-center text-gray-500 py-8">
                                                Aucun trade effectué
                                            </div>
                                        ) : (
                                            <div className="space-y-2">
                                                {trades.slice(0, 10).map((trade) => (
                                                    <div key={trade.id} className="bg-gray-800/30 p-3 rounded-lg flex justify-between">
                                                        <div className="flex items-center gap-3">
                                                            <Badge variant={trade.type === 'BUY' ? 'success' : 'danger'}>
                                                                {trade.type}
                                                            </Badge>
                                                            <div>
                                                                <p className="font-bold">{trade.symbol}</p>
                                                                <p className="text-xs text-gray-500">
                                                                    {trade.timestamp.toLocaleTimeString()}
                                                                </p>
                                                            </div>
                                                        </div>
                                                        <div className="text-right">
                                                            <p className="font-mono">${trade.price.toFixed(2)}</p>
                                                            <p className="text-xs text-gray-500">
                                                                Conf: {(trade.confidence * 100).toFixed(0)}%
                                                            </p>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </CardContent>
                                </Card>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </div>
        </main>
    );
}
