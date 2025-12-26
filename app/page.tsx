"use client";

import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Toaster } from 'react-hot-toast';

import { useStore } from "./store/useStore";
import { useSignal, useWatchlist, useCryptoList } from "./hooks/useSignals";

import { Header } from "./components/dashboard/Header";
import { SignalCard } from "./components/dashboard/SignalCard";
import { Watchlist } from "./components/Watchlist";
import { SignalHistory } from "./components/SignalHistory";
import { GridDashboard } from "./components/GridDashboard"; // Assuming this is compatible or will be updated
import { SignalCardSkeleton, WatchlistSkeleton } from "./components/Skeleton";
import { fadeIn } from "./animations";

export default function Home() {
    // Global State
    const {
        selectedCrypto,
        selectedTimeframe,
        viewMode,
        setSelectedCrypto,
        setSelectedTimeframe,
        setViewMode
    } = useStore();

    // Local State for specific UI controls
    const [autoRefresh, setAutoRefresh] = useState(false);

    // Data Fetching
    const { data: cryptoList } = useCryptoList();
    const availableCryptos = cryptoList?.cryptos || ["BTCUSDT"];
    const availableTimeframes = cryptoList?.timeframes || ["1h"];

    const {
        data: signalData,
        isLoading: isSignalLoading,
        refetch: refetchSignal
    } = useSignal(selectedCrypto, selectedTimeframe, autoRefresh ? 30 : 0);

    const {
        data: watchlistData = [],
        isLoading: isWatchlistLoading,
        refetch: refetchWatchlist
    } = useWatchlist(availableCryptos, selectedTimeframe, autoRefresh ? 30 : 0);

    const isLoading = isSignalLoading || isWatchlistLoading;

    // Derived Market Stats
    const marketStats = {
        totalValue: watchlistData.reduce((acc, s) => acc + (s.price || 0), 0),
        buySignals: watchlistData.filter(s => s.signal?.includes("BUY")).length,
        sellSignals: watchlistData.filter(s => s.signal?.includes("SELL")).length,
        avgConfidence: watchlistData.length > 0
            ? (watchlistData.reduce((acc, s) => acc + (s.confidence || 0), 0) / watchlistData.length) * 100
            : 0,
    };

    const handleRefresh = () => {
        refetchSignal();
        refetchWatchlist();
    };

    return (
        <main className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-900 to-gray-800 text-white">
            <Toaster position="top-right" />

            {/* Background Effects */}
            <div className="fixed inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-0 right-0 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl" />
                <div className="absolute bottom-0 left-0 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl" />
            </div>

            <div className="relative z-10 max-w-[1600px] mx-auto px-6 py-8">
                <Header
                    marketStats={marketStats}
                    availableCryptos={availableCryptos}
                    availableTimeframes={availableTimeframes}
                    selectedCrypto={selectedCrypto}
                    selectedTimeframe={selectedTimeframe}
                    viewMode={viewMode}
                    autoRefresh={autoRefresh}
                    onCryptoChange={setSelectedCrypto}
                    onTimeframeChange={setSelectedTimeframe}
                    onAutoRefreshToggle={() => setAutoRefresh(!autoRefresh)}
                    onViewModeToggle={() => setViewMode(viewMode === 'single' ? 'grid' : 'single')}
                    onRefresh={handleRefresh}
                />

                {/* Main Content */}
                {viewMode === 'grid' ? (
                    <GridDashboard />
                ) : (
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                        {/* Main Signal Display */}
                        <div className="lg:col-span-2 space-y-8">
                            <AnimatePresence mode="wait">
                                {isSignalLoading && !signalData ? (
                                    <motion.div key="loading" {...fadeIn}>
                                        <SignalCardSkeleton />
                                    </motion.div>
                                ) : signalData ? (
                                    <SignalCard
                                        key="content"
                                        data={signalData}
                                        timeframe={selectedTimeframe}
                                        onTimeframeChange={setSelectedTimeframe}
                                        onRefresh={handleRefresh}
                                    />
                                ) : null}
                            </AnimatePresence>

                            {/* We keep SignalHistory as is for now, passing symbol */}
                            <SignalHistory symbol={selectedCrypto} limit={15} />
                        </div>

                        {/* Watchlist Sidebar */}
                        <div className="lg:col-span-1">
                            {isWatchlistLoading && watchlistData.length === 0 ? (
                                <WatchlistSkeleton />
                            ) : (
                                <Watchlist
                                    signals={watchlistData}
                                    onSelectCrypto={setSelectedCrypto}
                                />
                            )}
                        </div>
                    </div>
                )}
            </div>
        </main>
    );
}
