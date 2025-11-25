"use client";

import { useEffect, useState } from "react";
import { CryptoChart } from "./components/CryptoChart";
import { CryptoSelector } from "./components/CryptoSelector";
import { Watchlist } from "./components/Watchlist";
import { SignalHistory } from "./components/SignalHistory";
import { SignalCardSkeleton, ChartSkeleton, WatchlistSkeleton, HistorySkeleton } from "./components/Skeleton";
import Link from "next/link";
import { Settings, RefreshCw, Play, Pause, LayoutGrid, Maximize, TrendingUp } from "lucide-react";
import toast, { Toaster } from 'react-hot-toast';
import { motion, AnimatePresence } from 'framer-motion';
import { GridDashboard } from "./components/GridDashboard";

interface SignalData {
  symbol: string;
  timeframe: string;
  signal: string;
  confidence: number;
  price: number;
  indicators: {
    rsi: number;
    ema20: number;
    ema50: number;
    macd: number;
  };
  chart_data: { time: number; open: number; high: number; low: number; close: number }[];
}

export default function Home() {
  const [viewMode, setViewMode] = useState<'single' | 'grid'>('single');
  const [data, setData] = useState<SignalData | null>(null);
  const [watchlistData, setWatchlistData] = useState<SignalData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [availableCryptos, setAvailableCryptos] = useState<string[]>(["BTCUSDT"]);
  const [availableTimeframes, setAvailableTimeframes] = useState<string[]>(["1h"]);
  const [selectedCrypto, setSelectedCrypto] = useState("BTCUSDT");
  const [selectedTimeframe, setSelectedTimeframe] = useState("1h");

  // Auto-refresh state
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState(30); // seconds

  // Fetch available cryptos and timeframes
  useEffect(() => {
    fetch("http://localhost:8000/cryptos/list")
      .then((res) => res.json())
      .then((data) => {
        setAvailableCryptos(data.cryptos || ["BTCUSDT"]);
        setAvailableTimeframes(data.timeframes || ["1h"]);
      })
      .catch((err) => {
        console.error("Error fetching crypto list:", err);
        toast.error("Erreur de connexion au backend");
      });
  }, []);

  // Fetch watchlist data (all cryptos)
  const fetchWatchlist = () => {
    fetch("http://localhost:8000/signals/multi", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        symbols: availableCryptos,
        timeframe: selectedTimeframe === 'all' ? '1w' : selectedTimeframe
      }),
    })
      .then((res) => res.json())
      .then((data) => setWatchlistData(data.signals || []))
      .catch((err) => {
        console.error("Error fetching watchlist:", err);
        toast.error("Erreur lors de la récupération de la watchlist");
      });
  };

  // Fetch single crypto signal
  const fetchSignal = () => {
    setLoading(true);
    setError("");
    fetch("http://localhost:8000/get-signal", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        symbol: selectedCrypto,
        timeframe: selectedTimeframe === 'all' ? '1w' : selectedTimeframe
      }),
    })
      .then((res) => {
        if (!res.ok) throw new Error("Erreur connexion backend");
        return res.json();
      })
      .then((signalData) => {
        setData(signalData);
        toast.success(`Signal ${selectedCrypto} mis à jour !`);
      })
      .catch((err) => {
        console.error(err);
        setError("Impossible de joindre le backend (http://localhost:8000). Assurez-vous qu'il est lancé.");
        toast.error("Erreur de connexion au backend");
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchSignal();
    fetchWatchlist();
  }, [selectedCrypto, selectedTimeframe]);

  // Auto-refresh effect
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchSignal();
      fetchWatchlist();
    }, refreshInterval * 1000);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, selectedCrypto, selectedTimeframe]);

  return (
    <main className="min-h-screen bg-gray-900 text-white p-8 md:p-12 font-sans">
      <Toaster position="top-right" />
      <div className="max-w-7xl mx-auto">
        <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-12">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
            Crypto AI System
          </h1>
          <div className="flex gap-4 items-center flex-wrap">
            <CryptoSelector
              cryptos={availableCryptos}
              timeframes={availableTimeframes}
              selectedCrypto={selectedCrypto}
              selectedTimeframe={selectedTimeframe}
              onCryptoChange={setSelectedCrypto}
              onTimeframeChange={setSelectedTimeframe}
            />
            <button
              onClick={() => {
                fetchSignal();
                fetchWatchlist();
              }}
              className="p-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition"
              title="Rafraîchir"
            >
              <RefreshCw className="w-5 h-5" />
            </button>
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`p-2 rounded-lg transition ${autoRefresh ? 'bg-green-600 hover:bg-green-700' : 'bg-gray-700 hover:bg-gray-600'
                }`}
              title={autoRefresh ? 'Désactiver auto-refresh' : 'Activer auto-refresh'}
            >
              {autoRefresh ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
            </button>
            <button
              onClick={() => setViewMode(viewMode === 'single' ? 'grid' : 'single')}
              className="p-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition"
              title={viewMode === 'single' ? "Vue Grille" : "Vue Unique"}
            >
              {viewMode === 'single' ? <LayoutGrid className="w-5 h-5 text-gray-400" /> : <Maximize className="w-5 h-5 text-gray-400" />}
            </button>
            <Link href="/backtest" className="p-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition" title="Backtest">
              <TrendingUp className="w-5 h-5 text-gray-400" />
            </Link>
            <Link href="/settings" className="p-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition" title="Paramètres">
              <Settings className="w-5 h-5 text-gray-400" />
            </Link>
          </div>
        </header>

        {viewMode === 'grid' ? (
          <GridDashboard />
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
            {/* Main Signal Display */}
            <div className="lg:col-span-2 space-y-10">
              <AnimatePresence mode="wait">
                {loading ? (
                  <motion.div
                    key="loading"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                  >
                    <SignalCardSkeleton />
                  </motion.div>
                ) : data && data.signal ? (
                  <motion.div
                    key="content"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    transition={{ duration: 0.3 }}
                  >
                    <div className="bg-gray-800 rounded-2xl p-10 shadow-2xl border border-gray-700">
                      <div className="flex justify-between items-start mb-8">
                        <div>
                          <h2 className="text-4xl font-bold text-white">{data.symbol}</h2>
                          <p className="text-gray-400 text-sm mt-1">Timeframe: {data.timeframe}</p>
                        </div>
                        <div className="text-right">
                          <div className="text-2xl font-mono font-bold text-gray-200">${data.price?.toFixed(2) || 'N/A'}</div>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-8 mb-8">
                        <div
                          className={`p-6 rounded-xl border-2 text-center ${data.signal?.includes("BUY")
                            ? "border-green-500 bg-green-900/20"
                            : data.signal?.includes("SELL")
                              ? "border-red-500 bg-red-900/20"
                              : "border-gray-500 bg-gray-700/30"
                            }`}
                        >
                          <p className="text-gray-400 text-xs uppercase tracking-wider mb-2">Signal AI</p>
                          <p
                            className={`text-3xl font-black ${data.signal?.includes("BUY")
                              ? "text-green-400"
                              : data.signal?.includes("SELL")
                                ? "text-red-400"
                                : "text-gray-300"
                              }`}
                          >
                            {data.signal || 'N/A'}
                          </p>
                        </div>

                        <div className="p-6 rounded-xl border border-gray-700 bg-gray-700/30 text-center">
                          <p className="text-gray-400 text-xs uppercase tracking-wider mb-2">Confiance Modèle</p>
                          <div className="flex items-center justify-center gap-2">
                            <span className="text-3xl font-bold text-blue-400">
                              {((data.confidence || 0) * 100).toFixed(0)}%
                            </span>
                          </div>
                        </div>
                      </div>

                      <div className="space-y-4">
                        <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider border-b border-gray-700 pb-2">
                          Indicateurs Techniques
                        </h3>
                        <div className="grid grid-cols-2 gap-y-6 gap-x-12 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-400">RSI (14)</span>
                            <span
                              className={`font-mono ${(data.indicators?.rsi || 0) < 30
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
                            <span className={(data.indicators?.macd || 0) > 0 ? "text-green-400" : "text-red-400"}>
                              {data.indicators?.macd?.toFixed(2) || 'N/A'}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-400">EMA (20)</span>
                            <span className="font-mono text-white">{data.indicators?.ema20?.toFixed(2) || 'N/A'}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-400">EMA (50)</span>
                            <span className="font-mono text-white">{data.indicators?.ema50?.toFixed(2) || 'N/A'}</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {data.chart_data && data.chart_data.length > 0 && (
                      <div className="bg-gray-800 rounded-2xl p-8 shadow-2xl border border-gray-700 my-8">
                        <CryptoChart
                          data={data.chart_data}
                          timeframe={selectedTimeframe}
                          onTimeframeChange={setSelectedTimeframe}
                          onRefresh={() => {
                            fetchSignal();
                            fetchWatchlist();
                          }}
                        />
                      </div>
                    )}

                    <SignalHistory symbol={selectedCrypto} limit={15} />
                  </motion.div>
                ) : null}
              </AnimatePresence>
            </div>

            {/* Watchlist Sidebar */}
            <div className="lg:col-span-1">
              {loading ? (
                <WatchlistSkeleton />
              ) : (
                <Watchlist signals={watchlistData} onSelectCrypto={setSelectedCrypto} />
              )}
            </div>
          </div>

        )}
      </div>
    </main >
  );
}
