"use client";

import React from "react";
import { motion } from "framer-motion";
import { TrendingUp, TrendingDown, Minus, Star } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "./ui/Card";
import { Badge } from "./ui/Badge";
import { staggerContainer, staggerItem } from "../animations";

interface SignalData {
    symbol: string;
    timeframe: string;
    signal: string;
    confidence: number;
    price: number;
}

interface WatchlistProps {
    signals: SignalData[];
    onSelectCrypto: (crypto: string) => void;
}

export const Watchlist = React.memo(function Watchlist({ signals, onSelectCrypto }: WatchlistProps) {
    const validSignals = signals.filter(s => s && s.signal && s.symbol);

    if (validSignals.length === 0) {
        return (
            <Card variant="glass">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Star className="w-5 h-5 text-yellow-400" />
                        Watchlist
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <p className="text-gray-400 text-sm">Chargement...</p>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card variant="glass" hover={false}>
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <Star className="w-5 h-5 text-yellow-400" />
                    Watchlist
                    <Badge variant="info" size="sm">{validSignals.length}</Badge>
                </CardTitle>
            </CardHeader>
            <CardContent>
                <motion.div
                    className="space-y-3"
                    variants={staggerContainer}
                    initial="initial"
                    animate="animate"
                >
                    {validSignals.map((signal) => {
                        const isBuy = signal.signal?.includes("BUY") || false;
                        const isSell = signal.signal?.includes("SELL") || false;
                        const isNeutral = signal.signal === "NEUTRE";

                        return (
                            <motion.button
                                key={signal.symbol}
                                variants={staggerItem}
                                onClick={() => onSelectCrypto(signal.symbol)}
                                className="w-full group"
                                whileHover={{ scale: 1.02 }}
                                whileTap={{ scale: 0.98 }}
                            >
                                <div className="flex items-center justify-between p-4 bg-gray-900/50 hover:bg-gray-800/80 rounded-xl transition-all border border-gray-700/50 hover:border-gray-600/70 shadow-lg hover:shadow-xl">
                                    <div className="flex items-center gap-3">
                                        <div className={`p-2 rounded-lg ${isBuy ? 'bg-green-500/10' :
                                            isSell ? 'bg-red-500/10' :
                                                'bg-gray-500/10'
                                            }`}>
                                            {isBuy && <TrendingUp className="w-5 h-5 text-green-400" />}
                                            {isSell && <TrendingDown className="w-5 h-5 text-red-400" />}
                                            {isNeutral && <Minus className="w-5 h-5 text-gray-400" />}
                                        </div>
                                        <div className="text-left">
                                            <div className="font-bold text-white group-hover:text-cyan-400 transition-colors">
                                                {signal.symbol}
                                            </div>
                                            <div className="text-xs text-gray-400 font-mono">
                                                ${signal.price?.toFixed(2) || 'N/A'}
                                            </div>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <Badge
                                            variant={isBuy ? 'success' : isSell ? 'danger' : 'default'}
                                            size="sm"
                                        >
                                            {signal.signal || 'N/A'}
                                        </Badge>
                                        <div className="text-xs text-gray-400 mt-1">
                                            {((signal.confidence || 0) * 100).toFixed(0)}%
                                        </div>
                                    </div>
                                </div>
                            </motion.button>
                        );
                    })}
                </motion.div>
            </CardContent>
        </Card>
    );
}, (prevProps, nextProps) => {
    // Custom comparison: only re-render if signals actually changed
    return JSON.stringify(prevProps.signals) === JSON.stringify(nextProps.signals) &&
        prevProps.onSelectCrypto === nextProps.onSelectCrypto;
});
