'use client';

import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';
import { Badge } from './ui/Badge';
import { Button } from './ui/Button';
import {
    Plus, Play, Pause, Trash2, RefreshCw, Settings,
    TrendingUp, TrendingDown, Activity, Clock
} from 'lucide-react';
import toast from 'react-hot-toast';

interface Strategy {
    name: string;
    riskPerTrade: number;
    stopLoss: number;
    takeProfit: number;
    maxPositions: number;
    trailingStop: boolean;
}

interface SessionStats {
    totalTrades: number;
    winningTrades: number;
    losingTrades: number;
    winRate: number;
}

interface TradingSession {
    id: string;
    name: string;
    strategy: Strategy;
    symbols: string[];
    initialBalance: number;
    currentBalance: number;
    isActive: boolean;
    autoTrade: boolean;
    stats: SessionStats;
    totalValue?: number;
    position_count?: number;
    createdAt: string;
    updatedAt: string;
}

interface SessionManagerProps {
    selectedSessionId: string | null;
    onSelectSession: (sessionId: string) => void;
    onSessionsChange?: () => void;
}

const API_URL = 'http://localhost:8000';

export default function SessionManager({
    selectedSessionId,
    onSelectSession,
    onSessionsChange
}: SessionManagerProps) {
    const [sessions, setSessions] = useState<TradingSession[]>([]);
    const [loading, setLoading] = useState(true);
    const [creating, setCreating] = useState(false);
    const [showCreateForm, setShowCreateForm] = useState(false);
    const [newSessionName, setNewSessionName] = useState('');
    const [newSessionBalance, setNewSessionBalance] = useState(10000);
    const [newSessionStrategy, setNewSessionStrategy] = useState('Balanced');

    // Fetch all sessions
    const fetchSessions = useCallback(async () => {
        try {
            const response = await fetch(`${API_URL}/trading/sessions`);
            if (response.ok) {
                const data = await response.json();
                setSessions(data.sessions || []);
            }
        } catch (error) {
            console.error('Error fetching sessions:', error);
        } finally {
            setLoading(false);
        }
    }, []);

    // Initial load and periodic refresh
    useEffect(() => {
        fetchSessions();
        const interval = setInterval(fetchSessions, 5000); // Refresh every 5s
        return () => clearInterval(interval);
    }, [fetchSessions]);

    // Create new session
    const createSession = async () => {
        if (!newSessionName.trim()) {
            toast.error('Please enter a session name');
            return;
        }

        setCreating(true);
        try {
            const response = await fetch(`${API_URL}/trading/sessions`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: newSessionName,
                    strategyName: newSessionStrategy,
                    initialBalance: newSessionBalance,
                    symbols: ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
                })
            });

            if (response.ok) {
                const data = await response.json();
                toast.success(`Session "${newSessionName}" created!`);
                setShowCreateForm(false);
                setNewSessionName('');
                fetchSessions();
                onSelectSession(data.session.id);
                onSessionsChange?.();
            } else {
                throw new Error('Failed to create session');
            }
        } catch (error) {
            console.error('Error creating session:', error);
            toast.error('Failed to create session');
        } finally {
            setCreating(false);
        }
    };

    // Start/Stop session
    const toggleSession = async (session: TradingSession, e: React.MouseEvent) => {
        e.stopPropagation();

        const endpoint = session.isActive ? 'stop' : 'start';
        try {
            const response = await fetch(
                `${API_URL}/trading/sessions/${session.id}/${endpoint}`,
                { method: 'POST' }
            );

            if (response.ok) {
                toast.success(session.isActive ? 'Session stopped' : 'Session started!');
                fetchSessions();
                onSessionsChange?.();
            }
        } catch (error) {
            console.error('Error toggling session:', error);
            toast.error('Failed to update session');
        }
    };

    // Delete session
    const deleteSession = async (sessionId: string, e: React.MouseEvent) => {
        e.stopPropagation();

        if (!confirm('Are you sure you want to delete this session?')) {
            return;
        }

        try {
            const response = await fetch(
                `${API_URL}/trading/sessions/${sessionId}`,
                { method: 'DELETE' }
            );

            if (response.ok) {
                toast.success('Session deleted');
                if (selectedSessionId === sessionId) {
                    onSelectSession('');
                }
                fetchSessions();
                onSessionsChange?.();
            }
        } catch (error) {
            console.error('Error deleting session:', error);
            toast.error('Failed to delete session');
        }
    };

    const getPnL = (session: TradingSession) => {
        const totalValue = session.totalValue || session.currentBalance;
        return totalValue - session.initialBalance;
    };

    const getPnLPercent = (session: TradingSession) => {
        const pnl = getPnL(session);
        return (pnl / session.initialBalance) * 100;
    };

    return (
        <Card variant="glass">
            <CardHeader>
                <div className="flex justify-between items-center">
                    <CardTitle className="flex items-center gap-2">
                        <Activity className="w-5 h-5 text-cyan-400" />
                        Trading Sessions
                    </CardTitle>
                    <div className="flex gap-2">
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => fetchSessions()}
                            leftIcon={<RefreshCw className="w-4 h-4" />}
                        >
                            Refresh
                        </Button>
                        <Button
                            variant="primary"
                            size="sm"
                            onClick={() => setShowCreateForm(!showCreateForm)}
                            leftIcon={<Plus className="w-4 h-4" />}
                        >
                            New Session
                        </Button>
                    </div>
                </div>
            </CardHeader>
            <CardContent>
                {/* Create Form */}
                {showCreateForm && (
                    <div className="mb-4 p-4 bg-gray-800/50 rounded-lg border border-gray-700">
                        <h4 className="text-sm font-semibold mb-3">Create New Session</h4>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                            <input
                                type="text"
                                placeholder="Session name"
                                value={newSessionName}
                                onChange={(e) => setNewSessionName(e.target.value)}
                                className="px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white text-sm focus:border-cyan-500 focus:outline-none"
                            />
                            <select
                                value={newSessionStrategy}
                                onChange={(e) => setNewSessionStrategy(e.target.value)}
                                className="px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white text-sm focus:border-cyan-500 focus:outline-none"
                            >
                                <option value="Conservative">Conservative</option>
                                <option value="Balanced">Balanced</option>
                                <option value="Aggressive">Aggressive</option>
                            </select>
                            <input
                                type="number"
                                placeholder="Initial Balance"
                                value={newSessionBalance}
                                onChange={(e) => setNewSessionBalance(Number(e.target.value))}
                                className="px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white text-sm focus:border-cyan-500 focus:outline-none"
                            />
                        </div>
                        <div className="flex gap-2 mt-3">
                            <Button
                                variant="primary"
                                size="sm"
                                onClick={createSession}
                                isLoading={creating}
                            >
                                Create
                            </Button>
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setShowCreateForm(false)}
                            >
                                Cancel
                            </Button>
                        </div>
                    </div>
                )}

                {/* Sessions List */}
                {loading ? (
                    <div className="text-center py-8 text-gray-400">
                        Loading sessions...
                    </div>
                ) : sessions.length === 0 ? (
                    <div className="text-center py-8 text-gray-400">
                        <p>No trading sessions yet.</p>
                        <p className="text-sm mt-1">Create a session to start trading 24/7!</p>
                    </div>
                ) : (
                    <div className="space-y-2">
                        {sessions.map((session) => {
                            const pnl = getPnL(session);
                            const pnlPercent = getPnLPercent(session);
                            const isSelected = selectedSessionId === session.id;

                            return (
                                <div
                                    key={session.id}
                                    onClick={() => onSelectSession(session.id)}
                                    className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${isSelected
                                        ? 'border-cyan-500 bg-cyan-500/10'
                                        : 'border-gray-700 bg-gray-800/30 hover:border-gray-600'
                                        }`}
                                >
                                    <div className="flex justify-between items-start">
                                        <div className="flex-1">
                                            <div className="flex items-center gap-2 mb-1">
                                                <span className="font-bold">{session.name}</span>
                                                {session.isActive && session.autoTrade && (
                                                    <Badge variant="success" size="sm">
                                                        <span className="flex items-center gap-1">
                                                            <span className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse"></span>
                                                            Trading
                                                        </span>
                                                    </Badge>
                                                )}
                                                {session.isActive && !session.autoTrade && (
                                                    <Badge variant="warning" size="sm">Paused</Badge>
                                                )}
                                                {!session.isActive && (
                                                    <Badge variant="default" size="sm">Stopped</Badge>
                                                )}
                                            </div>
                                            <div className="flex items-center gap-4 text-sm text-gray-400">
                                                <span>{session.strategy.name}</span>
                                                <span>${session.totalValue?.toFixed(2) || session.currentBalance.toFixed(2)}</span>
                                                <span className={pnl >= 0 ? 'text-green-400' : 'text-red-400'}>
                                                    {pnl >= 0 ? '+' : ''}{pnlPercent.toFixed(2)}%
                                                </span>
                                                <span className="flex items-center gap-1">
                                                    <Clock className="w-3 h-3" />
                                                    {session.stats.totalTrades} trades
                                                </span>
                                            </div>
                                        </div>
                                        <div className="flex gap-2">
                                            <button
                                                onClick={(e) => toggleSession(session, e)}
                                                className={`p-2 rounded-lg transition-colors ${session.isActive
                                                    ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30'
                                                    : 'bg-green-500/20 text-green-400 hover:bg-green-500/30'
                                                    }`}
                                            >
                                                {session.isActive ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                                            </button>
                                            <button
                                                onClick={(e) => deleteSession(session.id, e)}
                                                className="p-2 rounded-lg bg-gray-700/50 text-gray-400 hover:bg-red-500/20 hover:text-red-400 transition-colors"
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}

                {/* Info Box */}
                <div className="mt-4 p-3 bg-cyan-500/10 border border-cyan-500/20 rounded-lg">
                    <p className="text-xs text-cyan-300">
                        💡 <strong>24/7 Trading:</strong> Sessions continue trading even when you close your browser.
                        The server processes signals every 30 seconds for all active sessions.
                    </p>
                </div>
            </CardContent>
        </Card>
    );
}
