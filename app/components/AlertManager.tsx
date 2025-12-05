"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Plus, Trash2, Bell, BellOff } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "./ui/Card";
import { Button } from "./ui/Button";
import { Input } from "./ui/Input";
import { Badge } from "./ui/Badge";
import { Modal, ModalBody, ModalFooter } from "./ui/Modal";
import { useAppStore } from "../store/useAppStore";
import { slideUp } from "../animations";

export function AlertManager() {
    const { alerts, addAlert, removeAlert, toggleAlert } = useAppStore();
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [newAlert, setNewAlert] = useState({
        symbol: 'BTCUSDT',
        type: 'price' as 'price' | 'signal' | 'indicator',
        condition: 'above' as 'above' | 'below' | 'equals',
        value: '',
    });

    const handleAddAlert = () => {
        if (!newAlert.value) return;

        addAlert({
            symbol: newAlert.symbol,
            type: newAlert.type,
            condition: newAlert.condition,
            value: newAlert.type === 'price' ? parseFloat(newAlert.value) : newAlert.value,
            enabled: true,
        });

        setNewAlert({ symbol: 'BTCUSDT', type: 'price', condition: 'above', value: '' });
        setIsModalOpen(false);
    };

    return (
        <>
            <Card variant="gradient" glow>
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <CardTitle className="flex items-center gap-2">
                            <Bell className="w-5 h-5 text-yellow-400" />
                            Alertes
                            <Badge variant="info" size="sm">{alerts.length}</Badge>
                        </CardTitle>
                        <Button
                            variant="primary"
                            size="sm"
                            onClick={() => setIsModalOpen(true)}
                            leftIcon={<Plus className="w-4 h-4" />}
                        >
                            Nouvelle
                        </Button>
                    </div>
                </CardHeader>
                <CardContent>
                    {alerts.length === 0 ? (
                        <div className="text-center py-8 text-gray-400">
                            <Bell className="w-12 h-12 mx-auto mb-3 opacity-50" />
                            <p>Aucune alerte configurée</p>
                        </div>
                    ) : (
                        <div className="space-y-3">
                            <AnimatePresence>
                                {alerts.map((alert) => (
                                    <motion.div
                                        key={alert.id}
                                        {...slideUp}
                                        className={`p-4 rounded-xl border transition-all ${alert.enabled
                                                ? 'bg-gray-800/50 border-gray-700'
                                                : 'bg-gray-900/30 border-gray-800 opacity-50'
                                            }`}
                                    >
                                        <div className="flex items-start justify-between">
                                            <div className="flex-1">
                                                <div className="flex items-center gap-2 mb-1">
                                                    <span className="font-bold text-white">{alert.symbol}</span>
                                                    <Badge variant="default" size="sm">{alert.type}</Badge>
                                                </div>
                                                <p className="text-sm text-gray-400">
                                                    {alert.condition} {alert.value}
                                                </p>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <button
                                                    onClick={() => toggleAlert(alert.id)}
                                                    className="p-2 hover:bg-gray-700 rounded-lg transition"
                                                >
                                                    {alert.enabled ? (
                                                        <Bell className="w-4 h-4 text-yellow-400" />
                                                    ) : (
                                                        <BellOff className="w-4 h-4 text-gray-500" />
                                                    )}
                                                </button>
                                                <button
                                                    onClick={() => removeAlert(alert.id)}
                                                    className="p-2 hover:bg-red-900/30 rounded-lg transition"
                                                >
                                                    <Trash2 className="w-4 h-4 text-red-400" />
                                                </button>
                                            </div>
                                        </div>
                                    </motion.div>
                                ))}
                            </AnimatePresence>
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Add Alert Modal */}
            <Modal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                title="Nouvelle Alerte"
                size="md"
            >
                <ModalBody>
                    <div className="space-y-4">
                        <Input
                            label="Symbole"
                            value={newAlert.symbol}
                            onChange={(e) => setNewAlert({ ...newAlert, symbol: e.target.value })}
                            placeholder="BTCUSDT"
                        />

                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">
                                Type d'alerte
                            </label>
                            <select
                                value={newAlert.type}
                                onChange={(e) => setNewAlert({ ...newAlert, type: e.target.value as any })}
                                className="w-full px-4 py-3 bg-gray-900/50 border border-gray-700/50 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
                            >
                                <option value="price">Prix</option>
                                <option value="signal">Signal</option>
                                <option value="indicator">Indicateur</option>
                            </select>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">
                                Condition
                            </label>
                            <select
                                value={newAlert.condition}
                                onChange={(e) => setNewAlert({ ...newAlert, condition: e.target.value as any })}
                                className="w-full px-4 py-3 bg-gray-900/50 border border-gray-700/50 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
                            >
                                <option value="above">Au-dessus de</option>
                                <option value="below">En-dessous de</option>
                                <option value="equals">Égal à</option>
                            </select>
                        </div>

                        <Input
                            label="Valeur"
                            type={newAlert.type === 'price' ? 'number' : 'text'}
                            value={newAlert.value}
                            onChange={(e) => setNewAlert({ ...newAlert, value: e.target.value })}
                            placeholder={newAlert.type === 'price' ? '50000' : 'BUY'}
                        />
                    </div>
                </ModalBody>
                <ModalFooter>
                    <Button variant="ghost" onClick={() => setIsModalOpen(false)}>
                        Annuler
                    </Button>
                    <Button variant="primary" onClick={handleAddAlert}>
                        Créer l'alerte
                    </Button>
                </ModalFooter>
            </Modal>
        </>
    );
}
