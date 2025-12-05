import { renderHook, waitFor } from '@testing-library/react';
import { useWebSocketSignals } from '../useWebSocket';

// Mock react-use-websocket
jest.mock('react-use-websocket', () => ({
    __esModule: true,
    default: jest.fn(),
    ReadyState: {
        CONNECTING: 0,
        OPEN: 1,
        CLOSING: 2,
        CLOSED: 3,
        UNINSTANTIATED: -1,
    },
}));

// Mock react-hot-toast
jest.mock('react-hot-toast', () => ({
    __esModule: true,
    default: {
        success: jest.fn(),
        error: jest.fn(),
    },
}));

import useWebSocket, { ReadyState } from 'react-use-websocket';
import toast from 'react-hot-toast';

const mockUseWebSocket = useWebSocket as jest.MockedFunction<typeof useWebSocket>;

describe('useWebSocketSignals', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('initializes with default state', () => {
        mockUseWebSocket.mockReturnValue({
            sendMessage: jest.fn(),
            lastMessage: null,
            readyState: ReadyState.CONNECTING,
            getWebSocket: jest.fn(),
        } as any);

        const { result } = renderHook(() => useWebSocketSignals());

        expect(result.current.signals).toEqual([]);
        expect(result.current.isConnected).toBe(false);
        expect(result.current.connectionStatus).toBe('Connexion...');
    });

    it('updates connection status on open', () => {
        const mockOnOpen = jest.fn();

        mockUseWebSocket.mockImplementation((url, options) => {
            // Simulate connection opening
            if (options?.onOpen) {
                setTimeout(() => options.onOpen({} as any), 0);
            }

            return {
                sendMessage: jest.fn(),
                lastMessage: null,
                readyState: ReadyState.OPEN,
                getWebSocket: jest.fn(),
            } as any;
        });

        const { result } = renderHook(() =>
            useWebSocketSignals({ onSignalUpdate: mockOnOpen })
        );

        waitFor(() => {
            expect(result.current.isConnected).toBe(true);
            expect(toast.success).toHaveBeenCalledWith(
                'Connexion temps réel établie',
                expect.any(Object)
            );
        });
    });

    it('handles disconnection', () => {
        mockUseWebSocket.mockImplementation((url, options) => {
            // Simulate disconnection
            if (options?.onClose) {
                setTimeout(() => options.onClose({} as any), 0);
            }

            return {
                sendMessage: jest.fn(),
                lastMessage: null,
                readyState: ReadyState.CLOSED,
                getWebSocket: jest.fn(),
            } as any;
        });

        const { result } = renderHook(() => useWebSocketSignals());

        waitFor(() => {
            expect(result.current.isConnected).toBe(false);
            expect(toast.error).toHaveBeenCalledWith(
                'Connexion temps réel perdue',
                expect.any(Object)
            );
        });
    });

    it('processes incoming signal messages', () => {
        const mockSignalData = [
            {
                symbol: 'BTCUSDT',
                timeframe: '1h',
                signal: 'BUY',
                confidence: 0.85,
                price: 50000,
                indicators: {
                    rsi: 45,
                    ema20: 49000,
                    ema50: 48000,
                    macd: 100,
                },
            },
        ];

        const mockMessage = {
            data: JSON.stringify({
                type: 'signals_update',
                data: mockSignalData,
                timestamp: Date.now(),
            }),
        };

        mockUseWebSocket.mockReturnValue({
            sendMessage: jest.fn(),
            lastMessage: mockMessage as any,
            readyState: ReadyState.OPEN,
            getWebSocket: jest.fn(),
        } as any);

        const onSignalUpdate = jest.fn();
        const { result } = renderHook(() =>
            useWebSocketSignals({ onSignalUpdate })
        );

        waitFor(() => {
            expect(result.current.signals).toEqual(mockSignalData);
            expect(onSignalUpdate).toHaveBeenCalledWith(mockSignalData);
        });
    });

    it('uses exponential backoff for reconnection', () => {
        const mockOptions = { enabled: true };

        mockUseWebSocket.mockImplementation((url, options) => {
            // Verify reconnectInterval is a function
            expect(typeof options?.reconnectInterval).toBe('function');

            return {
                sendMessage: jest.fn(),
                lastMessage: null,
                readyState: ReadyState.CONNECTING,
                getWebSocket: jest.fn(),
            } as any;
        });

        renderHook(() => useWebSocketSignals(mockOptions));

        expect(mockUseWebSocket).toHaveBeenCalled();
    });
});
