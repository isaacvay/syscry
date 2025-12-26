import { motion } from "framer-motion";
import { DollarSign, TrendingUp, TrendingDown, Zap } from "lucide-react";
import { Card, CardContent } from "../ui/Card";
import { staggerItem } from "../../animations";

interface MarketStatsProps {
    stats: {
        totalValue: number;
        buySignals: number;
        sellSignals: number;
        avgConfidence: number;
    };
}

export function MarketStats({ stats }: MarketStatsProps) {
    return (
        <motion.div variants={staggerItem} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card variant="glass" hover glow>
                <CardContent className="flex items-center gap-4">
                    <div className="p-3 bg-cyan-500/10 rounded-xl">
                        <DollarSign className="w-6 h-6 text-cyan-400" />
                    </div>
                    <div>
                        <p className="text-sm text-gray-400">Total Market Value</p>
                        <p className="text-2xl font-bold font-mono">${stats.totalValue.toFixed(0)}</p>
                    </div>
                </CardContent>
            </Card>

            <Card variant="glass" hover glow>
                <CardContent className="flex items-center gap-4">
                    <div className="p-3 bg-green-500/10 rounded-xl">
                        <TrendingUp className="w-6 h-6 text-green-400" />
                    </div>
                    <div>
                        <p className="text-sm text-gray-400">Buy Signals</p>
                        <p className="text-2xl font-bold text-green-400">{stats.buySignals}</p>
                    </div>
                </CardContent>
            </Card>

            <Card variant="glass" hover glow>
                <CardContent className="flex items-center gap-4">
                    <div className="p-3 bg-red-500/10 rounded-xl">
                        <TrendingDown className="w-6 h-6 text-red-400" />
                    </div>
                    <div>
                        <p className="text-sm text-gray-400">Sell Signals</p>
                        <p className="text-2xl font-bold text-red-400">{stats.sellSignals}</p>
                    </div>
                </CardContent>
            </Card>

            <Card variant="glass" hover glow>
                <CardContent className="flex items-center gap-4">
                    <div className="p-3 bg-purple-500/10 rounded-xl">
                        <Zap className="w-6 h-6 text-purple-400" />
                    </div>
                    <div>
                        <p className="text-sm text-gray-400">Avg Confidence</p>
                        <p className="text-2xl font-bold text-purple-400">{stats.avgConfidence.toFixed(0)}%</p>
                    </div>
                </CardContent>
            </Card>
        </motion.div>
    );
}
