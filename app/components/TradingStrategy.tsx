'use client';

import { Card, CardContent } from './ui/Card';
import { Badge } from './ui/Badge';
import { TrendingUp, Shield, Zap, Target, Activity, Settings, Rocket, DollarSign } from 'lucide-react';

interface Strategy {
    name: string;
    description: string;
    riskPerTrade: number;
    stopLoss: number;
    takeProfit: number;
    maxPositions: number;
    trailingStop: boolean;
    signalMode?: 'normal' | 'aggressive'; // Backend signal filtering mode
}

const STRATEGIES: Strategy[] = [
    {
        name: 'Normal',
        description: 'Stratégie équilibrée avec signaux confirmés - Moins de trades, plus de sécurité',
        riskPerTrade: 0.02, // 2%
        stopLoss: 0.03, // 3%
        takeProfit: 0.06, // 6%
        maxPositions: 4,
        trailingStop: true,
        signalMode: 'normal',
    },
    {
        name: 'High Gain',
        description: '🚀 Plus de trades, gains potentiels élevés - Accepte plus de risque',
        riskPerTrade: 0.04, // 4%
        stopLoss: 0.05, // 5%
        takeProfit: 0.15, // 15%
        maxPositions: 8,
        trailingStop: false,
        signalMode: 'aggressive',
    },
    {
        name: 'Conservative',
        description: 'Faible risque, gains modérés et stables',
        riskPerTrade: 0.01, // 1%
        stopLoss: 0.02, // 2%
        takeProfit: 0.04, // 4%
        maxPositions: 3,
        trailingStop: true,
        signalMode: 'normal',
    },
    {
        name: 'Custom',
        description: 'Personnalisez tous les paramètres',
        riskPerTrade: 0.02, // 2%
        stopLoss: 0.03, // 3%
        takeProfit: 0.06, // 6%
        maxPositions: 5,
        trailingStop: true,
        signalMode: 'normal',
    },
];

const strategyIcons = {
    Normal: Activity,
    'High Gain': Rocket,
    Conservative: Shield,
    Custom: Settings,
};

const strategyColors = {
    Normal: 'from-cyan-500/20 to-blue-500/20 border-cyan-500/30',
    'High Gain': 'from-yellow-500/20 to-orange-500/20 border-yellow-500/30',
    Conservative: 'from-green-500/20 to-emerald-500/20 border-green-500/30',
    Custom: 'from-purple-500/20 to-pink-500/20 border-purple-500/30',
};

interface TradingStrategyProps {
    currentStrategy: Strategy;
    onStrategyChange: (strategy: Strategy) => void;
}

export default function TradingStrategy({ currentStrategy, onStrategyChange }: TradingStrategyProps) {
    return (
        <Card variant="glass">
            <CardContent className="p-6">
                <div className="flex items-center gap-2 mb-6">
                    <Target className="w-5 h-5 text-cyan-400" />
                    <h3 className="text-lg font-bold">Stratégie de Trading</h3>
                    <Badge variant="info" size="sm" className="ml-auto">
                        {STRATEGIES.length} stratégies
                    </Badge>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    {STRATEGIES.map((strategy) => {
                        const Icon = strategyIcons[strategy.name as keyof typeof strategyIcons];
                        const isActive = currentStrategy.name === strategy.name;
                        const colorClass = strategyColors[strategy.name as keyof typeof strategyColors];

                        return (
                            <button
                                key={strategy.name}
                                onClick={() => onStrategyChange(strategy)}
                                className={`relative p-5 rounded-xl border-2 transition-all duration-300 ${isActive
                                    ? `bg-gradient-to-br ${colorClass} scale-105 shadow-lg`
                                    : 'border-gray-700 bg-gray-800/30 hover:border-gray-600 hover:bg-gray-800/50'
                                    }`}
                            >

                                {/* Header */}
                                <div className="relative flex items-start justify-between mb-4">
                                    <div className="flex items-center gap-3">
                                        <div className={`p-3 rounded-xl transition-all duration-300 ${isActive
                                            ? 'bg-white/15 shadow-lg backdrop-blur-sm'
                                            : 'bg-gray-700/50 group-hover:bg-gray-700'
                                            }`}>
                                            <Icon className={`w-6 h-6 transition-all duration-300 ${isActive ? 'text-white drop-shadow-lg' : 'text-gray-400 group-hover:text-gray-300'
                                                }`} />
                                        </div>
                                        <div className="text-left">
                                            <h4 className="font-bold text-white text-base mb-0.5">{strategy.name}</h4>
                                            {isActive && (
                                                <div className="flex items-center gap-1 text-xs text-green-400">
                                                    <span className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse"></span>
                                                    <span>Active</span>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                    {isActive && (
                                        <div className="absolute -top-2 -right-2">
                                            <div className="relative">
                                                <div className="absolute inset-0 bg-green-400 rounded-full blur-md opacity-50 animate-pulse"></div>
                                                <Badge variant="success" size="sm" className="relative">
                                                    <span className="flex items-center gap-1.5">
                                                        <span className="w-2 h-2 bg-green-400 rounded-full animate-ping absolute"></span>
                                                        <span className="w-2 h-2 bg-green-400 rounded-full"></span>
                                                        Actif
                                                    </span>
                                                </Badge>
                                            </div>
                                        </div>
                                    )}
                                </div>

                                {/* Description */}
                                <p className="text-xs text-gray-400 mb-5 min-h-[2.5rem] leading-relaxed">{strategy.description}</p>

                                {/* Stats Grid */}
                                <div className="space-y-2.5">
                                    <div className="flex justify-between items-center text-xs group/item">
                                        <span className="text-gray-500 flex items-center gap-1.5 group-hover/item:text-gray-400 transition-colors">
                                            <TrendingUp className="w-3.5 h-3.5" />
                                            Risque/Trade
                                        </span>
                                        <span className="font-bold text-white bg-gray-700/30 px-2 py-0.5 rounded">
                                            {(strategy.riskPerTrade * 100).toFixed(1)}%
                                        </span>
                                    </div>
                                    <div className="flex justify-between items-center text-xs group/item">
                                        <span className="text-gray-500 group-hover/item:text-gray-400 transition-colors">Stop-Loss</span>
                                        <span className="font-bold text-red-400 bg-red-500/10 px-2 py-0.5 rounded">
                                            -{(strategy.stopLoss * 100).toFixed(1)}%
                                        </span>
                                    </div>
                                    <div className="flex justify-between items-center text-xs group/item">
                                        <span className="text-gray-500 group-hover/item:text-gray-400 transition-colors">Take-Profit</span>
                                        <span className="font-bold text-green-400 bg-green-500/10 px-2 py-0.5 rounded">
                                            +{(strategy.takeProfit * 100).toFixed(1)}%
                                        </span>
                                    </div>
                                    <div className="flex justify-between items-center text-xs group/item">
                                        <span className="text-gray-500 group-hover/item:text-gray-400 transition-colors">Max Positions</span>
                                        <span className="font-bold text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded">
                                            {strategy.maxPositions}
                                        </span>
                                    </div>
                                    <div className="flex justify-between items-center text-xs group/item">
                                        <span className="text-gray-500 group-hover/item:text-gray-400 transition-colors">Trailing Stop</span>
                                        <span className={`font-semibold px-2 py-0.5 rounded ${strategy.trailingStop
                                            ? 'text-cyan-400 bg-cyan-500/10'
                                            : 'text-gray-500 bg-gray-700/30'
                                            }`}>
                                            {strategy.trailingStop ? '✓ Oui' : '✗ Non'}
                                        </span>
                                    </div>
                                </div>

                                {/* Risk/Reward Ratio */}
                                <div className={`mt-5 pt-4 border-t transition-all duration-300 ${isActive ? 'border-white/20' : 'border-gray-700/50 group-hover:border-gray-700'
                                    }`}>
                                    <div className="flex items-center justify-between">
                                        <span className="text-xs text-gray-400 font-medium">Ratio R/R</span>
                                        <div className={`px-3 py-1 rounded-lg font-bold text-sm ${isActive
                                            ? 'bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-300 shadow-lg'
                                            : 'bg-gray-700/30 text-cyan-400 group-hover:bg-gray-700/50'
                                            }`}>
                                            1:{(strategy.takeProfit / strategy.stopLoss).toFixed(1)}
                                        </div>
                                    </div>
                                </div>
                            </button>
                        );
                    })}
                </div>

                {/* Custom Strategy Configuration */}
                {currentStrategy.name === 'Custom' && (
                    <div className="mt-6 p-6 bg-gradient-to-br from-purple-500/10 to-pink-500/10 border-2 border-purple-500/30 rounded-xl">
                        <div className="flex items-center gap-2 mb-4">
                            <Settings className="w-5 h-5 text-purple-400" />
                            <h4 className="font-bold text-white">Configuration Personnalisée</h4>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {/* Risk Per Trade */}
                            <div>
                                <label className="block text-sm text-gray-300 mb-2">
                                    Risque par Trade: <span className="font-bold text-white">{(currentStrategy.riskPerTrade * 100).toFixed(1)}%</span>
                                </label>
                                <input
                                    type="range"
                                    min="0.5"
                                    max="5"
                                    step="0.1"
                                    value={currentStrategy.riskPerTrade * 100}
                                    onChange={(e) => onStrategyChange({
                                        ...currentStrategy,
                                        riskPerTrade: Number(e.target.value) / 100
                                    })}
                                    className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-purple-500"
                                />
                                <div className="flex justify-between text-xs text-gray-500 mt-1">
                                    <span>0.5%</span>
                                    <span>5%</span>
                                </div>
                            </div>

                            {/* Stop Loss */}
                            <div>
                                <label className="block text-sm text-gray-300 mb-2">
                                    Stop-Loss: <span className="font-bold text-red-400">{(currentStrategy.stopLoss * 100).toFixed(1)}%</span>
                                </label>
                                <input
                                    type="range"
                                    min="1"
                                    max="10"
                                    step="0.5"
                                    value={currentStrategy.stopLoss * 100}
                                    onChange={(e) => onStrategyChange({
                                        ...currentStrategy,
                                        stopLoss: Number(e.target.value) / 100
                                    })}
                                    className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-red-500"
                                />
                                <div className="flex justify-between text-xs text-gray-500 mt-1">
                                    <span>1%</span>
                                    <span>10%</span>
                                </div>
                            </div>

                            {/* Take Profit */}
                            <div>
                                <label className="block text-sm text-gray-300 mb-2">
                                    Take-Profit: <span className="font-bold text-green-400">{(currentStrategy.takeProfit * 100).toFixed(1)}%</span>
                                </label>
                                <input
                                    type="range"
                                    min="2"
                                    max="20"
                                    step="0.5"
                                    value={currentStrategy.takeProfit * 100}
                                    onChange={(e) => onStrategyChange({
                                        ...currentStrategy,
                                        takeProfit: Number(e.target.value) / 100
                                    })}
                                    className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-green-500"
                                />
                                <div className="flex justify-between text-xs text-gray-500 mt-1">
                                    <span>2%</span>
                                    <span>20%</span>
                                </div>
                            </div>

                            {/* Max Positions */}
                            <div>
                                <label className="block text-sm text-gray-300 mb-2">
                                    Max Positions: <span className="font-bold text-white">{currentStrategy.maxPositions}</span>
                                </label>
                                <input
                                    type="range"
                                    min="1"
                                    max="10"
                                    step="1"
                                    value={currentStrategy.maxPositions}
                                    onChange={(e) => onStrategyChange({
                                        ...currentStrategy,
                                        maxPositions: Number(e.target.value)
                                    })}
                                    className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-cyan-500"
                                />
                                <div className="flex justify-between text-xs text-gray-500 mt-1">
                                    <span>1</span>
                                    <span>10</span>
                                </div>
                            </div>
                        </div>

                        {/* Trailing Stop Toggle */}
                        <div className="mt-6 flex items-center justify-between p-4 bg-gray-800/50 rounded-lg">
                            <div>
                                <p className="text-sm font-semibold text-white">Trailing Stop</p>
                                <p className="text-xs text-gray-400">Ajuste automatiquement le stop-loss à la hausse</p>
                            </div>
                            <button
                                onClick={() => onStrategyChange({
                                    ...currentStrategy,
                                    trailingStop: !currentStrategy.trailingStop
                                })}
                                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${currentStrategy.trailingStop ? 'bg-cyan-500' : 'bg-gray-600'
                                    }`}
                            >
                                <span
                                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${currentStrategy.trailingStop ? 'translate-x-6' : 'translate-x-1'
                                        }`}
                                />
                            </button>
                        </div>

                        {/* Risk/Reward Info */}
                        <div className="mt-4 p-3 bg-purple-500/10 border border-purple-500/20 rounded-lg">
                            <div className="flex items-center justify-between text-sm">
                                <span className="text-gray-300">Ratio Risk/Reward:</span>
                                <span className="font-bold text-purple-400">
                                    1:{(currentStrategy.takeProfit / currentStrategy.stopLoss).toFixed(2)}
                                </span>
                            </div>
                        </div>
                    </div>
                )}
            </CardContent>
        </Card>
    );
}

export { STRATEGIES };
export type { Strategy };
