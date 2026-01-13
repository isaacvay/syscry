"use client";

import { useEffect, useState } from "react";
import { Clock, Download } from "lucide-react";
import { API_CONFIG } from "../utils/config";



interface HistoricalSignal {
    id: number;
    symbol: string;
    timeframe: string;
    signal: string;
    confidence: number;
    price: number;
    timestamp: string;
}

interface SignalHistoryProps {
    symbol?: string;
    limit?: number;
}

export function SignalHistory({ symbol, limit = 20 }: SignalHistoryProps) {
    const [history, setHistory] = useState<HistoricalSignal[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchHistory = async () => {
            try {
                const params = new URLSearchParams();
                if (symbol) params.append("symbol", symbol);
                params.append("limit", limit.toString());

                const response = await fetch(`${API_CONFIG.BASE_URL}/signals/history?${params}`);
                const data = await response.json();
                setHistory(data.signals || []);
            } catch (error) {
                console.error("Error fetching history:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchHistory();
    }, [symbol, limit]);

    const exportToCSV = () => {
        if (history.length === 0) return;

        const headers = ['Symbol', 'Signal', 'Confidence', 'Price', 'Date'];
        const csvData = history.map(h => [
            h.symbol,
            h.signal,
            `${(h.confidence * 100).toFixed(0)}%`,
            `$${h.price.toFixed(2)}`,
            new Date(h.timestamp).toLocaleString('fr-FR')
        ]);

        const csvContent = [
            headers.join(','),
            ...csvData.map(row => row.join(','))
        ].join('\n');

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `signals_history_${symbol || 'all'}_${new Date().toISOString().split('T')[0]}.csv`;
        link.click();
        URL.revokeObjectURL(url);
    };

    if (loading) {
        return (
            <div className="bg-gray-800 rounded-2xl p-6 border border-gray-700">
                <h3 className="text-lg font-bold mb-4">Historique des Signaux</h3>
                <p className="text-gray-400 text-sm">Chargement...</p>
            </div>
        );
    }

    return (
        <div className="bg-gray-800 rounded-2xl p-8 border border-gray-700">
            <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-bold flex items-center gap-2">
                    <Clock className="w-5 h-5" />
                    Historique des Signaux
                </h3>
                {history.length > 0 && (
                    <button
                        onClick={exportToCSV}
                        className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition text-sm"
                    >
                        <Download className="w-4 h-4" />
                        Export CSV
                    </button>
                )}
            </div>
            <div className="overflow-x-auto">
                <table className="w-full text-sm">
                    <thead>
                        <tr className="border-b border-gray-700">
                            <th className="text-left py-2 px-2 text-gray-400 font-medium">Crypto</th>
                            <th className="text-left py-2 px-2 text-gray-400 font-medium">Signal</th>
                            <th className="text-left py-2 px-2 text-gray-400 font-medium">Confiance</th>
                            <th className="text-left py-2 px-2 text-gray-400 font-medium">Prix</th>
                            <th className="text-left py-2 px-2 text-gray-400 font-medium">Date</th>
                        </tr>
                    </thead>
                    <tbody>
                        {history.map((item) => (
                            <tr key={item.id} className="border-b border-gray-700/50 hover:bg-gray-700/30">
                                <td className="py-4 px-2 font-mono">{item.symbol}</td>
                                <td className="py-4 px-2">
                                    <span
                                        className={`px-2 py-1 rounded text-xs font-bold ${item.signal.includes("BUY")
                                            ? "bg-green-900/30 text-green-400"
                                            : item.signal.includes("SELL")
                                                ? "bg-red-900/30 text-red-400"
                                                : "bg-gray-700 text-gray-300"
                                            }`}
                                    >
                                        {item.signal}
                                    </span>
                                </td>
                                <td className="py-4 px-2">{(item.confidence * 100).toFixed(0)}%</td>
                                <td className="py-4 px-2 font-mono">${item.price.toFixed(2)}</td>
                                <td className="py-4 px-2 text-gray-400">
                                    {new Date(item.timestamp).toLocaleString("fr-FR", {
                                        day: "2-digit",
                                        month: "2-digit",
                                        hour: "2-digit",
                                        minute: "2-digit",
                                    })}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
                {history.length === 0 && (
                    <p className="text-center text-gray-400 py-4">Aucun signal enregistré</p>
                )}
            </div>
        </div>
    );
}
