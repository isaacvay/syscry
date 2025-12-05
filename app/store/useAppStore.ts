"use client";

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface Alert {
    id: string;
    symbol: string;
    type: 'price' | 'signal' | 'indicator';
    condition: 'above' | 'below' | 'equals';
    value: number | string;
    enabled: boolean;
    createdAt: number;
}

interface AppState {
    // Alerts
    alerts: Alert[];
    addAlert: (alert: Omit<Alert, 'id' | 'createdAt'>) => void;
    removeAlert: (id: string) => void;
    toggleAlert: (id: string) => void;

    // Watchlist groups
    watchlistGroups: Record<string, string[]>;
    addToWatchlist: (group: string, symbol: string) => void;
    removeFromWatchlist: (group: string, symbol: string) => void;
    createWatchlistGroup: (name: string) => void;
    deleteWatchlistGroup: (name: string) => void;

    // Dashboard layout
    dashboardLayout: any[];
    updateDashboardLayout: (layout: any[]) => void;

    // Preferences
    preferences: {
        autoRefresh: boolean;
        refreshInterval: number;
        soundEnabled: boolean;
        notificationsEnabled: boolean;
    };
    updatePreferences: (prefs: Partial<AppState['preferences']>) => void;
}

export const useAppStore = create<AppState>()(
    persist(
        (set) => ({
            // Alerts
            alerts: [],
            addAlert: (alert) =>
                set((state) => ({
                    alerts: [
                        ...state.alerts,
                        {
                            ...alert,
                            id: Math.random().toString(36).substr(2, 9),
                            createdAt: Date.now(),
                        },
                    ],
                })),
            removeAlert: (id) =>
                set((state) => ({
                    alerts: state.alerts.filter((a) => a.id !== id),
                })),
            toggleAlert: (id) =>
                set((state) => ({
                    alerts: state.alerts.map((a) =>
                        a.id === id ? { ...a, enabled: !a.enabled } : a
                    ),
                })),

            // Watchlist groups
            watchlistGroups: {
                favorites: [],
                defi: [],
                'layer-1': [],
            },
            addToWatchlist: (group, symbol) =>
                set((state) => ({
                    watchlistGroups: {
                        ...state.watchlistGroups,
                        [group]: [...(state.watchlistGroups[group] || []), symbol],
                    },
                })),
            removeFromWatchlist: (group, symbol) =>
                set((state) => ({
                    watchlistGroups: {
                        ...state.watchlistGroups,
                        [group]: (state.watchlistGroups[group] || []).filter((s) => s !== symbol),
                    },
                })),
            createWatchlistGroup: (name) =>
                set((state) => ({
                    watchlistGroups: {
                        ...state.watchlistGroups,
                        [name]: [],
                    },
                })),
            deleteWatchlistGroup: (name) =>
                set((state) => {
                    const { [name]: _, ...rest } = state.watchlistGroups;
                    return { watchlistGroups: rest };
                }),

            // Dashboard layout
            dashboardLayout: [],
            updateDashboardLayout: (layout) => set({ dashboardLayout: layout }),

            // Preferences
            preferences: {
                autoRefresh: false,
                refreshInterval: 30,
                soundEnabled: true,
                notificationsEnabled: true,
            },
            updatePreferences: (prefs) =>
                set((state) => ({
                    preferences: { ...state.preferences, ...prefs },
                })),
        }),
        {
            name: 'crypto-ai-storage',
        }
    )
);
