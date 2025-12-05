'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Shield, AlertTriangle, DollarSign, TrendingUp, PieChart } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/Card';
import { Badge } from './ui/Badge';
import { Tooltip } from './ui/Tooltip';
import { staggerItem } from '../animations';

interface Position {
    symbol: string;
    quantity: number;
    averagePrice: number;
    currentPrice: number;
    pnl: number;
    pnlPercent: number;
}

interface RiskManagerProps {
    currentBalance: number;
    totalPortfolioValue: number;
    positions: Position[];
    dailyPnL: number;
    maxDailyLoss: number;
    onMaxDailyLossChange: (value: number) => void;
}

export default function RiskManager({
    currentBalance,
    totalPortfolioValue,
    positions,
    dailyPnL,
    maxDailyLoss,
    onMaxDailyLossChange,
}: RiskManagerProps) {
    const [riskLevel, setRiskLevel] = useState<'low' | 'medium' | 'high'>('low');
    const [alerts, setAlerts] = useState<string[]>([]);

    // Calculate risk metrics
    const exposurePercent = ((totalPortfolioValue - currentBalance) / totalPortfolioValue) * 100;
    const dailyLossPercent = (dailyPnL / totalPortfolioValue) * 100;
    const remainingDailyLoss = maxDailyLoss + dailyLossPercent;

    // Calculate position concentration
    const positionValues = positions.map(p => p.quantity * p.currentPrice);
    const totalPositionValue = positionValues.reduce((sum, val) => sum + val, 0);
    const largestPosition = Math.max(...positionValues, 0);
    const concentrationPercent = totalPositionValue > 0 ? (largestPosition / totalPositionValue) * 100 : 0;

    // Risk assessment
    useEffect(() => {
        const newAlerts: string[] = [];
        let level: 'low' | 'medium' | 'high' = 'low';

        // Check daily loss limit
        if (dailyLossPercent < -maxDailyLoss * 0.8) {
            newAlerts.push('⚠️ Approche de la limite de perte journalière');
            level = 'high';
        } else if (dailyLossPercent < -maxDailyLoss * 0.5) {
            newAlerts.push('⚡ 50% de la limite de perte journalière atteinte');
            level = 'medium';
        }

        // Check exposure
        if (exposurePercent > 80) {
            newAlerts.push('🔴 Sur-exposition: Plus de 80% du capital investi');
            level = 'high';
        } else if (exposurePercent > 60) {
            newAlerts.push('🟡 Exposition élevée: Plus de 60% du capital investi');
            if (level === 'low') level = 'medium';
        }

        // Check concentration
        if (concentrationPercent > 50) {
            newAlerts.push('📊 Concentration élevée: Une position représente >50%');
            if (level === 'low') level = 'medium';
        }

        // Check individual position risk
        positions.forEach(pos => {
            if (pos.pnlPercent < -10) {
                newAlerts.push(`📉 ${pos.symbol}: Perte de ${pos.pnlPercent.toFixed(1)}%`);
                if (level === 'low') level = 'medium';
            }
        });

        setAlerts(newAlerts);
        setRiskLevel(level);
    }, [dailyLossPercent, maxDailyLoss, exposurePercent, concentrationPercent, positions]);

    const getRiskColor = () => {
        switch (riskLevel) {
            case 'high': return 'text-red-400';
            case 'medium': return 'text-yellow-400';
            default: return 'text-green-400';
        }
    };

    const getRiskBadge = () => {
        switch (riskLevel) {
            case 'high': return { variant: 'danger' as const, label: 'Risque Élevé' };
            case 'medium': return { variant: 'warning' as const, label: 'Risque Modéré' };
            default: return { variant: 'success' as const, label: 'Risque Faible' };
        }
    };

    return (
        <div className="space-y-6">
            {/* Risk Overview */}
            <motion.div variants={staggerItem}>
                <Card variant="glass" glow>
                    <CardHeader>
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                <Shield className="w-5 h-5 text-cyan-400" />
                                <CardTitle>Gestion des Risques</CardTitle>
                            </div>
                            <Badge {...getRiskBadge()}>
                                {getRiskBadge().label}
                            </Badge>
                        </div>
                    </CardHeader>
                    <CardContent>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            {/* Exposure */}
                            <div className="bg-gray-800/30 p-4 rounded-xl border border-gray-700/30">
                                <div className="flex items-center gap-3 mb-3">
                                    <div className="p-2 bg-cyan-500/10 rounded-lg">
                                        <DollarSign className="w-4 h-4 text-cyan-400" />
                                    </div>
                                    <Tooltip content="Pourcentage du capital actuellement investi">
                                        <p className="text-sm text-gray-400">Exposition</p>
                                    </Tooltip>
                                </div>
                                <p className={`text-2xl font-bold ${exposurePercent > 70 ? 'text-red-400' : 'text-cyan-400'}`}>
                                    {exposurePercent.toFixed(1)}%
                                </p>
                                <div className="mt-2 h-2 bg-gray-700 rounded-full overflow-hidden">
                                    <div
                                        className={`h-full transition-all ${exposurePercent > 70 ? 'bg-red-500' : 'bg-cyan-500'}`}
                                        style={{ width: `${Math.min(exposurePercent, 100)}%` }}
                                    />
                                </div>
                            </div>

                            {/* Daily Loss */}
                            <div className="bg-gray-800/30 p-4 rounded-xl border border-gray-700/30">
                                <div className="flex items-center gap-3 mb-3">
                                    <div className="p-2 bg-purple-500/10 rounded-lg">
                                        <TrendingUp className="w-4 h-4 text-purple-400" />
                                    </div>
                                    <Tooltip content="Perte/Gain du jour par rapport au capital total">
                                        <p className="text-sm text-gray-400">P&L Journalier</p>
                                    </Tooltip>
                                </div>
                                <p className={`text-2xl font-bold ${dailyPnL >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                    {dailyPnL >= 0 ? '+' : ''}{dailyLossPercent.toFixed(2)}%
                                </p>
                                <p className="text-xs text-gray-500 mt-2">
                                    Limite: -{maxDailyLoss}% ({remainingDailyLoss.toFixed(1)}% restant)
                                </p>
                            </div>

                            {/* Concentration */}
                            <div className="bg-gray-800/30 p-4 rounded-xl border border-gray-700/30">
                                <div className="flex items-center gap-3 mb-3">
                                    <div className="p-2 bg-green-500/10 rounded-lg">
                                        <PieChart className="w-4 h-4 text-green-400" />
                                    </div>
                                    <Tooltip content="Pourcentage de la plus grande position">
                                        <p className="text-sm text-gray-400">Concentration</p>
                                    </Tooltip>
                                </div>
                                <p className={`text-2xl font-bold ${concentrationPercent > 50 ? 'text-yellow-400' : 'text-green-400'}`}>
                                    {concentrationPercent.toFixed(1)}%
                                </p>
                                <p className="text-xs text-gray-500 mt-2">
                                    {positions.length} position{positions.length > 1 ? 's' : ''} ouverte{positions.length > 1 ? 's' : ''}
                                </p>
                            </div>
                        </div>

                        {/* Daily Loss Limit Control */}
                        <div className="mt-6 p-4 bg-gray-800/50 rounded-xl border border-gray-700/50">
                            <label className="block text-sm font-medium text-gray-400 mb-3">
                                Limite de Perte Journalière (%)
                            </label>
                            <div className="flex items-center gap-4">
                                <input
                                    type="range"
                                    min="1"
                                    max="10"
                                    step="0.5"
                                    value={maxDailyLoss}
                                    onChange={(e) => onMaxDailyLossChange(Number(e.target.value))}
                                    className="flex-1 h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-cyan-500"
                                />
                                <span className="text-lg font-bold text-cyan-400 min-w-[60px] text-right">
                                    {maxDailyLoss.toFixed(1)}%
                                </span>
                            </div>
                            <p className="text-xs text-gray-500 mt-2">
                                Le trading s'arrêtera automatiquement si cette limite est atteinte
                            </p>
                        </div>
                    </CardContent>
                </Card>
            </motion.div>

            {/* Risk Alerts */}
            {alerts.length > 0 && (
                <motion.div variants={staggerItem}>
                    <Card variant="glass">
                        <CardHeader>
                            <div className="flex items-center gap-2">
                                <AlertTriangle className="w-5 h-5 text-yellow-400" />
                                <CardTitle>Alertes de Risque</CardTitle>
                                <Badge variant="warning">{alerts.length}</Badge>
                            </div>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-2">
                                {alerts.map((alert, index) => (
                                    <motion.div
                                        key={index}
                                        initial={{ opacity: 0, x: -20 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        transition={{ delay: index * 0.1 }}
                                        className="p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg text-sm text-yellow-200"
                                    >
                                        {alert}
                                    </motion.div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                </motion.div>
            )}

            {/* Position Diversification */}
            {positions.length > 0 && (
                <motion.div variants={staggerItem}>
                    <Card variant="glass">
                        <CardHeader>
                            <CardTitle>Diversification du Portfolio</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-3">
                                {positions.map((position) => {
                                    const positionValue = position.quantity * position.currentPrice;
                                    const positionPercent = totalPositionValue > 0 ? (positionValue / totalPositionValue) * 100 : 0;

                                    return (
                                        <div key={position.symbol} className="space-y-2">
                                            <div className="flex items-center justify-between text-sm">
                                                <span className="font-medium text-white">{position.symbol}</span>
                                                <span className="text-gray-400">{positionPercent.toFixed(1)}%</span>
                                            </div>
                                            <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                                                <div
                                                    className="h-full bg-gradient-to-r from-cyan-500 to-purple-500 transition-all"
                                                    style={{ width: `${positionPercent}%` }}
                                                />
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </CardContent>
                    </Card>
                </motion.div>
            )}
        </div>
    );
}
