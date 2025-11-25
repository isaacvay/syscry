"use client";

import { TrendingUp, TrendingDown, Minus } from "lucide-react";

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

export function Watchlist({ signals, onSelectCrypto }: WatchlistProps) {
    // Filter out signals without valid data
    const validSignals = signals.filter(s => s && s.signal && s.symbol);

    if (validSignals.length === 0) {
        return (
            <div className="bg-gray-800 rounded-2xl p-6 border border-gray-700">
                <h3 className="text-lg font-bold mb-4">Watchlist</h3>
                <p className="text-gray-400 text-sm">Chargement...</p>
            </div>
        );
    }

    return (
        <div className="bg-gray-800 rounded-2xl p-8 border border-gray-700">
            <h3 className="text-lg font-bold mb-4">Watchlist</h3>
            <div className="space-y-4">
                {validSignals.map((signal) => {
                    const isBuy = signal.signal?.includes("BUY") || false;
                    const isSell = signal.signal?.includes("SELL") || false;
                    const isNeutral = signal.signal === "NEUTRE";

                    return (
                        <button
                            key={signal.symbol}
                            onClick={() => onSelectCrypto(signal.symbol)}
                            className="w-full flex items-center justify-between p-5 bg-gray-900 hover:bg-gray-700 rounded-lg transition border border-gray-700"
                        >
                            <div className="flex items-center gap-3">
                                {isBuy && <TrendingUp className="w-5 h-5 text-green-400" />}
                                {isSell && <TrendingDown className="w-5 h-5 text-red-400" />}
                                {isNeutral && <Minus className="w-5 h-5 text-gray-400" />}
                                <div className="text-left">
                                    <div className="font-semibold">{signal.symbol}</div>
                                    <div className="text-xs text-gray-400">${signal.price?.toFixed(2) || 'N/A'}</div>
                                </div>
                            </div>
                            <div className="text-right">
                                <div
                                    className={`text-sm font-bold ${isBuy ? "text-green-400" : isSell ? "text-red-400" : "text-gray-400"
                                        }`}
                                >
                                    {signal.signal || 'N/A'}
                                </div>
                                <div className="text-xs text-gray-400">
                                    {((signal.confidence || 0) * 100).toFixed(0)}%
                                </div>
                            </div>
                        </button>
                    );
                })}
            </div>
        </div>
    );
}
