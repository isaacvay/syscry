import { motion } from "framer-motion";
import { Card, CardHeader, CardTitle, CardContent } from "../ui/Card";
import { SignalData } from "../../hooks/useWebSocket";
import { slideUp } from "../../animations";
import { CryptoChart } from "../CryptoChart";

// Helper Interface (should ideally be shared)
interface ExtendedSignalData extends SignalData {
    chart_data?: any[];
}

interface SignalCardProps {
    data: ExtendedSignalData;
    timeframe: string;
    onTimeframeChange: (tf: string) => void;
    onRefresh: () => void;
}

export function SignalCard({ data, timeframe, onTimeframeChange, onRefresh }: SignalCardProps) {
    if (!data) return null;

    return (
        <motion.div {...slideUp}>
            <Card variant="gradient" glow>
                <CardHeader>
                    <div className="flex justify-between items-start">
                        <div>
                            <CardTitle className="text-3xl">{data.symbol}</CardTitle>
                            <p className="text-gray-400 text-sm mt-1">Timeframe: {data.timeframe}</p>
                        </div>
                        <div className="text-right">
                            <div className="text-3xl font-mono font-bold text-white">
                                ${data.price?.toFixed(2) || 'N/A'}
                            </div>
                        </div>
                    </div>
                </CardHeader>

                <CardContent>
                    <div className="grid grid-cols-2 gap-6 mb-6">
                        <div
                            className={`p-6 rounded-xl border-2 text-center transition-all ${data.signal?.includes("BUY")
                                ? "border-green-500 bg-green-900/20 shadow-lg shadow-green-500/20"
                                : data.signal?.includes("SELL")
                                    ? "border-red-500 bg-red-900/20 shadow-lg shadow-red-500/20"
                                    : "border-gray-500 bg-gray-700/30"
                                }`}
                        >
                            <p className="text-gray-400 text-xs uppercase tracking-wider mb-2">Signal AI</p>
                            <p
                                className={`text-4xl font-black ${data.signal?.includes("BUY")
                                    ? "text-green-400"
                                    : data.signal?.includes("SELL")
                                        ? "text-red-400"
                                        : "text-gray-300"
                                    }`}
                            >
                                {data.signal || 'N/A'}
                            </p>
                        </div>

                        <div className="p-6 rounded-xl border border-gray-700 bg-gray-800/30 text-center">
                            <p className="text-gray-400 text-xs uppercase tracking-wider mb-2">Confidence</p>
                            <div className="flex items-center justify-center gap-2">
                                <span className="text-4xl font-bold text-cyan-400">
                                    {((data.confidence || 0) * 100).toFixed(0)}%
                                </span>
                            </div>
                        </div>
                    </div>

                    <div className="space-y-4">
                        <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider border-b border-gray-700 pb-2">
                            Technical Indicators
                        </h3>
                        <div className="grid grid-cols-2 gap-y-4 gap-x-8 text-sm">
                            <div className="flex justify-between">
                                <span className="text-gray-400">RSI (14)</span>
                                <span
                                    className={`font-mono font-semibold ${(data.indicators?.rsi || 0) < 30
                                        ? "text-green-400"
                                        : (data.indicators?.rsi || 0) > 70
                                            ? "text-red-400"
                                            : "text-white"
                                        }`}
                                >
                                    {data.indicators?.rsi?.toFixed(2) || 'N/A'}
                                </span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-400">MACD</span>
                                <span className={`font-mono font-semibold ${(data.indicators?.macd || 0) > 0 ? "text-green-400" : "text-red-400"}`}>
                                    {data.indicators?.macd?.toFixed(2) || 'N/A'}
                                </span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-400">EMA (20)</span>
                                <span className="font-mono font-semibold text-white">{data.indicators?.ema20?.toFixed(2) || 'N/A'}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-400">EMA (50)</span>
                                <span className="font-mono font-semibold text-white">{data.indicators?.ema50?.toFixed(2) || 'N/A'}</span>
                            </div>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Chart Section */}
            {data.chart_data && data.chart_data.length > 0 && (
                <Card variant="gradient" className="mt-8">
                    <CryptoChart
                        data={data.chart_data}
                        timeframe={timeframe}
                        onTimeframeChange={onTimeframeChange}
                        onRefresh={onRefresh}
                    />
                </Card>
            )}
        </motion.div>
    );
}
