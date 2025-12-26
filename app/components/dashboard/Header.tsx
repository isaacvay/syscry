import { motion } from "framer-motion";
import Link from "next/link";
import {
    RefreshCw,
    Play,
    Pause,
    LayoutGrid,
    Maximize,
    Activity,
    TrendingUp,
    Settings
} from "lucide-react";
import { CryptoSelector } from "../CryptoSelector";
import { Button } from "../ui/Button";
import { Badge } from "../ui/Badge";
import { staggerContainer, staggerItem } from "../../animations";
import { MarketStats } from "./MarketStats";

interface HeaderProps {
    marketStats: any;
    availableCryptos: string[];
    availableTimeframes: string[];
    selectedCrypto: string;
    selectedTimeframe: string;
    viewMode: 'single' | 'grid';
    autoRefresh: boolean;
    onCryptoChange: (crypto: string) => void;
    onTimeframeChange: (tf: string) => void;
    onAutoRefreshToggle: () => void;
    onViewModeToggle: () => void;
    onRefresh: () => void;
}

export function Header({
    marketStats,
    availableCryptos,
    availableTimeframes,
    selectedCrypto,
    selectedTimeframe,
    viewMode,
    autoRefresh,
    onCryptoChange,
    onTimeframeChange,
    onAutoRefreshToggle,
    onViewModeToggle,
    onRefresh
}: HeaderProps) {
    return (
        <motion.header
            className="mb-10"
            initial="initial"
            animate="animate"
            variants={staggerContainer}
        >
            <motion.div variants={staggerItem} className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6 mb-8">
                <div>
                    <h1 className="text-4xl lg:text-5xl font-black mb-2">
                        <span className="gradient-text">Crypto AI System</span>
                    </h1>
                    <p className="text-gray-400 flex items-center gap-2">
                        <Badge variant="success" dot>Live</Badge>
                        <span>Trading Signals & Analysis</span>
                    </p>
                </div>

                <div className="flex gap-3 items-center flex-wrap">
                    <CryptoSelector
                        cryptos={availableCryptos}
                        timeframes={availableTimeframes}
                        selectedCrypto={selectedCrypto}
                        selectedTimeframe={selectedTimeframe}
                        onCryptoChange={onCryptoChange}
                        onTimeframeChange={onTimeframeChange}
                    />

                    <Button
                        variant="secondary"
                        size="md"
                        onClick={onRefresh}
                        leftIcon={<RefreshCw className="w-4 h-4" />}
                    >
                        Refresh
                    </Button>

                    <Button
                        variant={autoRefresh ? "success" : "ghost"}
                        size="md"
                        onClick={onAutoRefreshToggle}
                        leftIcon={autoRefresh ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                    >
                        {autoRefresh ? 'Auto' : 'Manual'}
                    </Button>

                    <Button
                        variant="ghost"
                        size="md"
                        onClick={onViewModeToggle}
                        leftIcon={viewMode === 'single' ? <LayoutGrid className="w-4 h-4" /> : <Maximize className="w-4 h-4" />}
                    />

                    <Link href="/trading">
                        <Button variant="ghost" size="md" leftIcon={<Activity className="w-4 h-4" />}>
                            Simulation
                        </Button>
                    </Link>

                    <Link href="/backtest">
                        <Button variant="ghost" size="md" leftIcon={<TrendingUp className="w-4 h-4" />}>
                            Backtest
                        </Button>
                    </Link>

                    <Link href="/settings">
                        <Button variant="ghost" size="md" leftIcon={<Settings className="w-4 h-4" />}>
                            Settings
                        </Button>
                    </Link>
                </div>
            </motion.div>

            <MarketStats stats={marketStats} />
        </motion.header>
    );
}
