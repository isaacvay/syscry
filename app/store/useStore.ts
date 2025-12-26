import { create } from 'zustand';

interface AppState {
    selectedCrypto: string;
    selectedTimeframe: string;
    viewMode: 'single' | 'grid';
    setSelectedCrypto: (crypto: string) => void;
    setSelectedTimeframe: (timeframe: string) => void;
    setViewMode: (mode: 'single' | 'grid') => void;
}

export const useStore = create<AppState>((set) => ({
    selectedCrypto: 'BTCUSDT',
    selectedTimeframe: '1h',
    viewMode: 'single',
    setSelectedCrypto: (crypto) => set({ selectedCrypto: crypto }),
    setSelectedTimeframe: (timeframe) => set({ selectedTimeframe: timeframe }),
    setViewMode: (mode) => set({ viewMode: mode }),
}));
