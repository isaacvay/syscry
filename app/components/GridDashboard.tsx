"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { ArrowUpRight, ArrowDownRight, Activity, TrendingUp } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "./ui/Card";
import { Badge } from "./ui/Badge";
import { staggerContainer, staggerItem } from "../animations";

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
        const interval = setInterval(fetchSignals, 30000);
        return () => clearInterval(interval);
    }, []);

    if (loading) {
        return (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {[1, 2, 3, 4].map((i) => (
                    <Card key={i} variant="glass">
                        <div className="h-48 animate-pulse bg-gray-700/30 rounded-xl" />
                    </Card>
                ))}
            </div>
        );
    }

    return (
        <motion.div
            className="grid grid-cols-1 md:grid-cols-2 gap-6"
            variants={staggerContainer}
            initial="initial"
            animate="animate"
        >
            {signals.map((signal) => (
                <motion.div key={signal.symbol} variants={staggerItem}>
                    <Card variant="gradient" hover glow>
                        {/* Background Icon */}
                        <div className="absolute top-0 right-0 p-6 opacity-5">
                            <TrendingUp className="w-32 h-32" />
                        </div>

                        <CardContent className="relative z-10">
                            <div className="flex justify-between items-start mb-6">
                                <div>
                                    <h3 className="text-3xl font-black text-white">{signal.symbol}</h3>
                                    <p className="text-gray-400 text-sm mt-1">1H Timeframe</p>
                                </div>
                                <div className="text-right">
                                    <p className="text-2xl font-mono font-bold text-white">
                                        ${signal.price.toFixed(2)}
                                    </p>
                                    <Badge
                                        variant={
                                            signal.signal.includes("BUY")
                                                ? "success"
                                                : signal.signal.includes("SELL")
                                                    ? "danger"
                                                    : "default"
                                        }
                                        size="sm"
                                        className="mt-2"
                                    >
                                        {signal.signal.includes("BUY") && <ArrowUpRight className="w-3 h-3" />}
                                        {signal.signal.includes("SELL") && <ArrowDownRight className="w-3 h-3" />}
                                        {signal.signal}
                                    </Badge>
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div className="bg-gray-900/50 rounded-xl p-4 border border-gray-700/50">
                                    <p className="text-gray-400 text-xs uppercase tracking-wider mb-1">
                                        Confiance
                                    </p>
                                    <p className="text-xl font-bold text-cyan-400">
                                        {(signal.confidence * 100).toFixed(0)}%
                                    </p>
                                </div>
                                <div className="bg-gray-900/50 rounded-xl p-4 border border-gray-700/50">
                                    <p className="text-gray-400 text-xs uppercase tracking-wider mb-1">RSI</p>
                                    <p
                                        className={`text-xl font-bold ${signal.indicators.rsi > 70
                                                ? "text-red-400"
                                                : signal.indicators.rsi < 30
                                                    ? "text-green-400"
                                                    : "text-white"
                                            }`}
                                    >
                                        {signal.indicators.rsi.toFixed(1)}
                                    </p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </motion.div>
            ))}
        </motion.div>
    );
}
