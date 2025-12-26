import { useQuery } from '@tanstack/react-query';
import { SignalData } from './useWebSocket'; // Assuming SignalData type is exported from here or needs to be moved

// API base URL
const API_URL = 'http://localhost:8000';

export interface SignalResponse {
    signal: string;
    confidence: number;
    price: number;
    symbol: string;
    timeframe: string;
    indicators: {
        rsi: number;
        macd: number;
        ema20: number;
        ema50: number;
    };
    chart_data?: any[];
}

async function fetchSignal(symbol: string, timeframe: string): Promise<SignalResponse> {
    const res = await fetch(`${API_URL}/get-signal`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            symbol,
            timeframe: timeframe === 'all' ? '1w' : timeframe
        }),
    });
    if (!res.ok) throw new Error('Network response was not ok');
    return res.json();
}

async function fetchWatchlist(symbols: string[], timeframe: string): Promise<SignalResponse[]> {
    const res = await fetch(`${API_URL}/signals/multi`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            symbols,
            timeframe: timeframe === 'all' ? '1w' : timeframe
        }),
    });
    if (!res.ok) throw new Error('Network response was not ok');
    const data = await res.json();
    return data.signals || [];
}

async function fetchCryptos(): Promise<{ cryptos: string[], timeframes: string[] }> {
    const res = await fetch(`${API_URL}/cryptos/list`);
    if (!res.ok) throw new Error('Network response was not ok');
    return res.json();
}

export function useSignal(symbol: string, timeframe: string, refreshInterval: number = 0) {
    return useQuery({
        queryKey: ['signal', symbol, timeframe],
        queryFn: () => fetchSignal(symbol, timeframe),
        refetchInterval: refreshInterval > 0 ? refreshInterval * 1000 : false,
        enabled: !!symbol && !!timeframe,
    });
}

export function useWatchlist(symbols: string[], timeframe: string, refreshInterval: number = 0) {
    return useQuery({
        queryKey: ['watchlist', symbols, timeframe],
        queryFn: () => fetchWatchlist(symbols, timeframe),
        refetchInterval: refreshInterval > 0 ? refreshInterval * 1000 : false,
        enabled: symbols.length > 0,
    });
}

export function useCryptoList() {
    return useQuery({
        queryKey: ['cryptos'],
        queryFn: fetchCryptos,
    });
}
