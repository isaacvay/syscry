"use client";

import { useState } from "react";
import { ChevronDown } from "lucide-react";

interface CryptoSelectorProps {
    cryptos: string[];
    timeframes: string[];
    selectedCrypto: string;
    selectedTimeframe: string;
    onCryptoChange: (crypto: string) => void;
    onTimeframeChange: (timeframe: string) => void;
}

export function CryptoSelector({
    cryptos,
    timeframes,
    selectedCrypto,
    selectedTimeframe,
    onCryptoChange,
    onTimeframeChange,
}: CryptoSelectorProps) {
    const [cryptoOpen, setCryptoOpen] = useState(false);
    const [timeframeOpen, setTimeframeOpen] = useState(false);

    return (
        <div className="flex gap-4">
            {/* Crypto Selector */}
            <div className="relative">
                <button
                    onClick={() => setCryptoOpen(!cryptoOpen)}
                    className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition border border-gray-700"
                >
                    <span className="font-semibold">{selectedCrypto}</span>
                    <ChevronDown className="w-4 h-4" />
                </button>
                {cryptoOpen && (
                    <div className="absolute top-full mt-2 bg-gray-800 border border-gray-700 rounded-lg shadow-xl z-50 min-w-[150px]">
                        {cryptos.map((crypto) => (
                            <button
                                key={crypto}
                                onClick={() => {
                                    onCryptoChange(crypto);
                                    setCryptoOpen(false);
                                }}
                                className={`block w-full text-left px-4 py-2 hover:bg-gray-700 transition ${crypto === selectedCrypto ? "bg-gray-700 text-blue-400" : ""
                                    }`}
                            >
                                {crypto}
                            </button>
                        ))}
                    </div>
                )}
            </div>

            {/* Timeframe Selector */}
            <div className="relative">
                <button
                    onClick={() => setTimeframeOpen(!timeframeOpen)}
                    className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition border border-gray-700"
                >
                    <span>{selectedTimeframe}</span>
                    <ChevronDown className="w-4 h-4" />
                </button>
                {timeframeOpen && (
                    <div className="absolute top-full mt-2 bg-gray-800 border border-gray-700 rounded-lg shadow-xl z-50 min-w-[100px]">
                        {timeframes.map((tf) => (
                            <button
                                key={tf}
                                onClick={() => {
                                    onTimeframeChange(tf);
                                    setTimeframeOpen(false);
                                }}
                                className={`block w-full text-left px-4 py-2 hover:bg-gray-700 transition ${tf === selectedTimeframe ? "bg-gray-700 text-blue-400" : ""
                                    }`}
                            >
                                {tf}
                            </button>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
