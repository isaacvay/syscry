'use client';

import { useMemo } from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Activity, Target, Clock, Award } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/Card';
import { Badge } from './ui/Badge';
import { Tooltip } from './ui/Tooltip';
import { staggerItem } from '../animations';

interface Trade {
    id: string;
    symbol: string;
    type: 'BUY' | 'SELL';
    price: number;
    quantity: number;
    timestamp: Date;
    signal: string;
    confidence: number;
    pnl?: number;
}

interface TradingStatsProps {
    trades: Trade[];
    totalPnL: number;
    initialBalance: number;
    currentBalance: number;
}

export default function TradingStats({ trades, totalPnL, initialBalance, currentBalance }: TradingStatsProps) {
    const stats = useMemo(() => {
        const completedTrades = trades.filter(t => t.pnl !== undefined);
        const winningTrades = completedTrades.filter(t => t.pnl! > 0);
        const losingTrades = completedTrades.filter(t => t.pnl! < 0);

        const totalWins = winningTrades.reduce((sum, t) => sum + t.pnl!, 0);
        const totalLosses = Math.abs(losingTrades.reduce((sum, t) => sum + t.pnl!, 0));

        const averageWin = winningTrades.length > 0 ? totalWins / winningTrades.length : 0;
        const averageLoss = losingTrades.length > 0 ? totalLosses / losingTrades.length : 0;

        const profitFactor = totalLosses > 0 ? totalWins / totalLosses : totalWins > 0 ? Infinity : 0;
        const winLossRatio = averageLoss > 0 ? averageWin / averageLoss : averageWin > 0 ? Infinity : 0;

        // Calculate Sharpe Ratio (simplified)
        const returns = completedTrades.map(t => (t.pnl! / initialBalance) * 100);
        const avgReturn = returns.length > 0 ? returns.reduce((a, b) => a + b, 0) / returns.length : 0;
        const stdDev = returns.length > 1
            ? Math.sqrt(returns.reduce((sum, r) => sum + Math.pow(r - avgReturn, 2), 0) / (returns.length - 1))
            : 0;
        const sharpeRatio = stdDev > 0 ? (avgReturn / stdDev) * Math.sqrt(252) : 0; // Annualized

        // Calculate Maximum Drawdown
        let peak = initialBalance;
        let maxDrawdown = 0;
        let runningBalance = initialBalance;

        completedTrades.forEach(trade => {
            runningBalance += trade.pnl!;
            if (runningBalance > peak) {
                peak = runningBalance;
            }
            const drawdown = ((peak - runningBalance) / peak) * 100;
            if (drawdown > maxDrawdown) {
                maxDrawdown = drawdown;
            }
        });

        // Average holding time (in minutes)
        const buyTrades = trades.filter(t => t.type === 'BUY');
        const sellTrades = trades.filter(t => t.type === 'SELL');
        let totalHoldingTime = 0;
        let holdingCount = 0;

        sellTrades.forEach(sell => {
            const correspondingBuy = buyTrades.find(buy =>
                buy.symbol === sell.symbol &&
                buy.timestamp < sell.timestamp
            );
            if (correspondingBuy) {
                totalHoldingTime += (sell.timestamp.getTime() - correspondingBuy.timestamp.getTime()) / 1000 / 60;
                holdingCount++;
            }
        });

        const avgHoldingTime = holdingCount > 0 ? totalHoldingTime / holdingCount : 0;

        return {
            sharpeRatio,
            maxDrawdown,
            profitFactor,
            averageWin,
            averageLoss,
            winLossRatio,
            avgHoldingTime,
            totalWins,
            totalLosses,
        };
    }, [trades, initialBalance]);

    const getSharpeColor = (sharpe: number) => {
        if (sharpe > 2) return 'text-green-400';
        if (sharpe > 1) return 'text-cyan-400';
        if (sharpe > 0) return 'text-yellow-400';
        return 'text-red-400';
    };

    const getSharpeBadge = (sharpe: number) => {
        if (sharpe > 2) return { variant: 'success' as const, label: 'Excellent' };
        if (sharpe > 1) return { variant: 'info' as const, label: 'Bon' };
        if (sharpe > 0) return { variant: 'warning' as const, label: 'Moyen' };
        return { variant: 'danger' as const, label: 'Faible' };
    };

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* Sharpe Ratio */}
            <motion.div variants={staggerItem}>
                <Card variant="glass" hover glow>
                    <CardContent className="p-6">
                        <div className="flex items-start justify-between mb-4">
                            <div className="p-3 bg-cyan-500/10 rounded-xl">
                                <Award className="w-6 h-6 text-cyan-400" />
                            </div>
                            <Tooltip content="Mesure du rendement ajusté au risque. >2 = Excellent, >1 = Bon, >0 = Moyen">
                                <Badge {...getSharpeBadge(stats.sharpeRatio)}>
                                    {getSharpeBadge(stats.sharpeRatio).label}
                                </Badge>
                            </Tooltip>
                        </div>
                        <div>
                            <p className="text-sm text-gray-400 mb-1">Sharpe Ratio</p>
                            <p className={`text-3xl font-bold ${getSharpeColor(stats.sharpeRatio)}`}>
                                {stats.sharpeRatio.toFixed(2)}
                            </p>
                            <p className="text-xs text-gray-500 mt-2">
                                Rendement ajusté au risque
                            </p>
                        </div>
                    </CardContent>
                </Card>
            </motion.div>

            {/* Maximum Drawdown */}
            <motion.div variants={staggerItem}>
                <Card variant="glass" hover glow>
                    <CardContent className="p-6">
                        <div className="flex items-start justify-between mb-4">
                            <div className="p-3 bg-red-500/10 rounded-xl">
                                <TrendingDown className="w-6 h-6 text-red-400" />
                            </div>
                            <Tooltip content="Perte maximale depuis le pic. Plus c'est bas, mieux c'est.">
                                <Badge variant={stats.maxDrawdown < 10 ? 'success' : stats.maxDrawdown < 20 ? 'warning' : 'danger'}>
                                    {stats.maxDrawdown < 10 ? 'Faible' : stats.maxDrawdown < 20 ? 'Modéré' : 'Élevé'}
                                </Badge>
                            </Tooltip>
                        </div>
                        <div>
                            <p className="text-sm text-gray-400 mb-1">Max Drawdown</p>
                            <p className="text-3xl font-bold text-red-400">
                                {stats.maxDrawdown.toFixed(2)}%
                            </p>
                            <p className="text-xs text-gray-500 mt-2">
                                Perte maximale depuis le pic
                            </p>
                        </div>
                    </CardContent>
                </Card>
            </motion.div>

            {/* Profit Factor */}
            <motion.div variants={staggerItem}>
                <Card variant="glass" hover glow>
                    <CardContent className="p-6">
                        <div className="flex items-start justify-between mb-4">
                            <div className="p-3 bg-green-500/10 rounded-xl">
                                <Target className="w-6 h-6 text-green-400" />
                            </div>
                            <Tooltip content="Ratio gains/pertes. >2 = Excellent, >1.5 = Bon, >1 = Profitable">
                                <Badge variant={stats.profitFactor > 2 ? 'success' : stats.profitFactor > 1 ? 'info' : 'danger'}>
                                    {stats.profitFactor > 2 ? 'Excellent' : stats.profitFactor > 1 ? 'Profitable' : 'Perte'}
                                </Badge>
                            </Tooltip>
                        </div>
                        <div>
                            <p className="text-sm text-gray-400 mb-1">Profit Factor</p>
                            <p className={`text-3xl font-bold ${stats.profitFactor > 1 ? 'text-green-400' : 'text-red-400'}`}>
                                {stats.profitFactor === Infinity ? '∞' : stats.profitFactor.toFixed(2)}
                            </p>
                            <p className="text-xs text-gray-500 mt-2">
                                ${stats.totalWins.toFixed(0)} / ${stats.totalLosses.toFixed(0)}
                            </p>
                        </div>
                    </CardContent>
                </Card>
            </motion.div>

            {/* Average Win */}
            <motion.div variants={staggerItem}>
                <Card variant="glass" hover>
                    <CardContent className="p-6">
                        <div className="flex items-center gap-4">
                            <div className="p-3 bg-green-500/10 rounded-xl">
                                <TrendingUp className="w-5 h-5 text-green-400" />
                            </div>
                            <div>
                                <p className="text-sm text-gray-400">Gain Moyen</p>
                                <p className="text-xl font-bold text-green-400">
                                    ${stats.averageWin.toFixed(2)}
                                </p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </motion.div>

            {/* Average Loss */}
            <motion.div variants={staggerItem}>
                <Card variant="glass" hover>
                    <CardContent className="p-6">
                        <div className="flex items-center gap-4">
                            <div className="p-3 bg-red-500/10 rounded-xl">
                                <TrendingDown className="w-5 h-5 text-red-400" />
                            </div>
                            <div>
                                <p className="text-sm text-gray-400">Perte Moyenne</p>
                                <p className="text-xl font-bold text-red-400">
                                    ${stats.averageLoss.toFixed(2)}
                                </p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </motion.div>

            {/* Average Holding Time */}
            <motion.div variants={staggerItem}>
                <Card variant="glass" hover>
                    <CardContent className="p-6">
                        <div className="flex items-center gap-4">
                            <div className="p-3 bg-purple-500/10 rounded-xl">
                                <Clock className="w-5 h-5 text-purple-400" />
                            </div>
                            <div>
                                <p className="text-sm text-gray-400">Temps Moyen</p>
                                <p className="text-xl font-bold text-purple-400">
                                    {stats.avgHoldingTime.toFixed(0)}m
                                </p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </motion.div>
        </div>
    );
}
