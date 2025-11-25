"use client";

import { useEffect, useState } from "react";
import { ArrowUpRight, ArrowDownRight, Activity } from "lucide-react";
import Link from "next/link";

interface SignalData {
    symbol: string;
    timeframe: string;
    signal: string;
    confidence: number;
    price: number;
    indicators: {
        rsi: number;
        macd: number;
    };
}

export function GridDashboard() {
    const [signals, setSignals] = useState<SignalData[]>([]);
    const [loading, setLoading] = useState(true);
    const symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"];

    useEffect(() => {
        const fetchSignals = async () => {
            try {
                const response = await fetch("http://localhost:8000/signals/multi", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ symbols, timeframe: "1h" }),
                });
                const data = await response.json();
                setSignals(data.signals || []);
            } catch (error) {
                console.error("Error fetching grid signals:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchSignals();
        const interval = setInterval(fetchSignals, 30000); // Refresh every 30s
        return () => clearInterval(interval);
    }, []);

    if (loading) {
        return (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {[1, 2, 3, 4].map((i) => (
                    <div key={i} className="bg-gray-800 rounded-2xl p-6 border border-gray-700 h-48 animate-pulse" />
                ))}
            </div>
        );
    }

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {signals.map((signal) => (
                <div key={signal.symbol} className="bg-gray-800 rounded-2xl p-6 border border-gray-700 hover:border-blue-500/50 transition relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition">
                        <Activity className="w-24 h-24" />
                    </div>

                    <div className="relative z-10">
                        <div className="flex justify-between items-start mb-4">
                            <div>
                                <h3 className="text-2xl font-bold">{signal.symbol}</h3>
                                <p className="text-gray-400 text-sm">1H Timeframe</p>
                            </div>
                            <div className="text-right">
                                <p className="text-xl font-mono font-bold">${signal.price.toFixed(2)}</p>
                                <div className={`flex items-center justify-end gap-1 text-sm ${signal.signal.includes("BUY") ? "text-green-400" :
                                    signal.signal.includes("SELL") ? "text-red-400" : "text-gray-400"
                                    }`}>
                                    {signal.signal.includes("BUY") ? <ArrowUpRight className="w-4 h-4" /> :
                                        signal.signal.includes("SELL") ? <ArrowDownRight className="w-4 h-4" /> : null}
                                    {signal.signal}
                                </div>
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4 mt-6">
                            <div className="bg-gray-900/50 rounded-lg p-3">
                                <p className="text-gray-500 text-xs uppercase">Confiance</p>
                                <p className="text-lg font-bold text-blue-400">{(signal.confidence * 100).toFixed(0)}%</p>
                            </div>
                            <div className="bg-gray-900/50 rounded-lg p-3">
                                <p className="text-gray-500 text-xs uppercase">RSI</p>
                                <p className={`text-lg font-bold ${signal.indicators.rsi > 70 ? "text-red-400" :
                                    signal.indicators.rsi < 30 ? "text-green-400" : "text-white"
                                    }`}>
                                    {signal.indicators.rsi.toFixed(1)}
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            ))}
        </div>
    );
}
