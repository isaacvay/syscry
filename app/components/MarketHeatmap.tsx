"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { TrendingUp, TrendingDown } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "./ui/Card";
import { Tooltip } from "./ui/Tooltip";
import { staggerContainer, staggerItem } from "../animations";

interface CryptoData {
    symbol: string;
    price: number;
    change24h: number;
    volume: number;
    marketCap: number;
}

export function MarketHeatmap() {
    const [cryptos, setCryptos] = useState<CryptoData[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Simulated data - replace with real API call
        const mockData: CryptoData[] = [
            { symbol: "BTC", price: 43250, change24h: 2.5, volume: 28000000000, marketCap: 850000000000 },
            { symbol: "ETH", price: 2280, change24h: 3.8, volume: 15000000000, marketCap: 275000000000 },
            { symbol: "BNB", price: 315, change24h: -1.2, volume: 1200000000, marketCap: 48000000000 },
            { symbol: "SOL", price: 98, change24h: 5.6, volume: 2500000000, marketCap: 42000000000 },
            { symbol: "ADA", price: 0.52, change24h: -2.1, volume: 450000000, marketCap: 18000000000 },
            { symbol: "XRP", price: 0.61, change24h: 1.8, volume: 1800000000, marketCap: 33000000000 },
            { symbol: "DOT", price: 7.2, change24h: -0.5, volume: 280000000, marketCap: 9500000000 },
            { symbol: "AVAX", price: 38, change24h: 4.2, volume: 650000000, marketCap: 14000000000 },
            { symbol: "MATIC", price: 0.88, change24h: 2.9, volume: 520000000, marketCap: 8200000000 },
            { symbol: "LINK", price: 15.5, change24h: -1.8, volume: 680000000, marketCap: 8800000000 },
            { symbol: "UNI", price: 6.8, change24h: 3.1, volume: 180000000, marketCap: 5100000000 },
            { symbol: "ATOM", price: 10.2, change24h: 1.5, volume: 320000000, marketCap: 3000000000 },
        ];

        setTimeout(() => {
            setCryptos(mockData);
            setLoading(false);
        }, 500);
    }, []);

    const getColor = (change: number) => {
        if (change > 3) return 'bg-green-500';
        if (change > 0) return 'bg-green-600';
        if (change > -3) return 'bg-red-600';
        return 'bg-red-500';
    };

    const getOpacity = (change: number) => {
        const absChange = Math.abs(change);
        if (absChange > 5) return '100';
        if (absChange > 3) return '80';
        if (absChange > 1) return '60';
        return '40';
    };

    if (loading) {
        return (
            <Card variant="gradient">
                <CardHeader>
                    <CardTitle>Market Heatmap</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="h-64 flex items-center justify-center">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-500" />
                    </div>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card variant="gradient" glow>
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-cyan-400" />
                    Market Heatmap
                </CardTitle>
            </CardHeader>
            <CardContent>
                <motion.div
                    className="grid grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2"
                    variants={staggerContainer}
                    initial="initial"
                    animate="animate"
                >
                    {cryptos.map((crypto) => (
                        <motion.div key={crypto.symbol} variants={staggerItem}>
                            <Tooltip
                                content={
                                    <div className="text-left">
                                        <div className="font-bold">{crypto.symbol}</div>
                                        <div className="text-xs text-gray-300">
                                            ${crypto.price.toLocaleString()}
                                        </div>
                                        <div className={`text-xs font-semibold ${crypto.change24h >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                            {crypto.change24h >= 0 ? '+' : ''}{crypto.change24h.toFixed(2)}%
                                        </div>
                                        <div className="text-xs text-gray-400 mt-1">
                                            Vol: ${(crypto.volume / 1000000000).toFixed(2)}B
                                        </div>
                                    </div>
                                }
                            >
                                <motion.div
                                    className={`${getColor(crypto.change24h)}/${getOpacity(crypto.change24h)} rounded-lg p-3 cursor-pointer transition-all hover:scale-105`}
                                    whileHover={{ scale: 1.05 }}
                                >
                                    <div className="text-white font-bold text-sm mb-1">
                                        {crypto.symbol}
                                    </div>
                                    <div className="flex items-center gap-1">
                                        {crypto.change24h >= 0 ? (
                                            <TrendingUp className="w-3 h-3 text-white" />
                                        ) : (
                                            <TrendingDown className="w-3 h-3 text-white" />
                                        )}
                                        <span className="text-white text-xs font-semibold">
                                            {Math.abs(crypto.change24h).toFixed(1)}%
                                        </span>
                                    </div>
                                </motion.div>
                            </Tooltip>
                        </motion.div>
                    ))}
                </motion.div>
            </CardContent>
        </Card>
    );
}
