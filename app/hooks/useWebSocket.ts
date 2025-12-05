"use client";

import { useEffect, useRef, useCallback, useState } from 'react';
import useWebSocket, { ReadyState } from 'react-use-websocket';
import toast from 'react-hot-toast';

export interface SignalData {
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
    chart_data?: { time: number; open: number; high: number; low: number; close: number }[];
}

interface WebSocketMessage {
    type: string;
    data: SignalData[];
    timestamp: number;
}

interface UseWebSocketSignalsOptions {
    enabled?: boolean;
    onSignalUpdate?: (signals: SignalData[]) => void;
    onNewSignal?: (signal: SignalData) => void;
}

export function useWebSocketSignals(options: UseWebSocketSignalsOptions = {}) {
    const { enabled = true, onSignalUpdate, onNewSignal } = options;
    const [signals, setSignals] = useState<SignalData[]>([]);
    const [isConnected, setIsConnected] = useState(false);
    const previousSignalsRef = useRef<Map<string, string>>(new Map());
    const reconnectAttemptsRef = useRef(0);

    const WS_URL = 'ws://localhost:8000/ws/signals';

    // Exponential backoff for reconnection
    const getReconnectInterval = useCallback(() => {
        const attempt = reconnectAttemptsRef.current;
        // Start at 1s, double each time, max 30s
        const interval = Math.min(1000 * Math.pow(2, attempt), 30000);
        return interval;
    }, []);

    const { sendMessage, lastMessage, readyState } = useWebSocket(
        WS_URL,
        {
            shouldReconnect: () => enabled,
            reconnectAttempts: 10,
            reconnectInterval: () => getReconnectInterval(),
            onOpen: () => {
                console.log('WebSocket connected');
                setIsConnected(true);
                reconnectAttemptsRef.current = 0; // Reset on successful connection
                toast.success('Connexion temps réel établie', {
                    icon: '🔴',
                    duration: 2000,
                });
            },
            onClose: () => {
                console.log('WebSocket disconnected');
                setIsConnected(false);
                reconnectAttemptsRef.current += 1;
                toast.error('Connexion temps réel perdue', {
                    icon: '⚫',
                    duration: 2000,
                });
            },
            onError: (error) => {
                console.error('WebSocket error:', error);
                reconnectAttemptsRef.current += 1;
            },
        },
        enabled
    );

    // Process incoming messages
    useEffect(() => {
        if (lastMessage !== null) {
            try {
                const message: WebSocketMessage = JSON.parse(lastMessage.data);

                if (message.type === 'signals_update' && message.data) {
                    setSignals(message.data);
                    onSignalUpdate?.(message.data);

                    // Check for new signals
                    message.data.forEach((signal) => {
                        const key = `${signal.symbol}-${signal.timeframe}`;
                        const previousSignal = previousSignalsRef.current.get(key);

                        if (previousSignal && previousSignal !== signal.signal) {
                            // Signal changed
                            onNewSignal?.(signal);
                            toast.success(
                                `Nouveau signal ${signal.signal} pour ${signal.symbol}`,
                                {
                                    icon: signal.signal.includes('BUY') ? '🟢' : signal.signal.includes('SELL') ? '🔴' : '🟡',
                                    duration: 4000,
                                }
                            );
                        }

                        previousSignalsRef.current.set(key, signal.signal);
                    });
                }
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        }
    }, [lastMessage, onSignalUpdate, onNewSignal]);

    const connectionStatus = {
        [ReadyState.CONNECTING]: 'Connexion...',
        [ReadyState.OPEN]: 'Connecté',
        [ReadyState.CLOSING]: 'Déconnexion...',
        [ReadyState.CLOSED]: 'Déconnecté',
        [ReadyState.UNINSTANTIATED]: 'Non initialisé',
    }[readyState];

    return {
        signals,
        isConnected,
        connectionStatus,
        readyState,
        sendMessage,
    };
}
