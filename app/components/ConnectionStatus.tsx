"use client";

import { motion } from "framer-motion";
import { Activity } from "lucide-react";
import { Badge } from "./ui/Badge";
import { Tooltip } from "./ui/Tooltip";

interface ConnectionStatusProps {
    isConnected: boolean;
    status: string;
}

export const ConnectionStatus: React.FC<ConnectionStatusProps> = ({
    isConnected,
    status,
}) => {
    return (
        <Tooltip content={status}>
            <motion.div
                className="flex items-center gap-2 px-3 py-1.5 bg-gray-800/50 rounded-lg border border-gray-700/50"
                animate={{
                    borderColor: isConnected
                        ? 'rgba(34, 197, 94, 0.5)'
                        : 'rgba(107, 114, 128, 0.5)',
                }}
            >
                <motion.div
                    className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-gray-500'
                        }`}
                    animate={{
                        scale: isConnected ? [1, 1.2, 1] : 1,
                        opacity: isConnected ? [1, 0.7, 1] : 0.5,
                    }}
                    transition={{
                        duration: 2,
                        repeat: isConnected ? Infinity : 0,
                        ease: 'easeInOut',
                    }}
                />
                <span className="text-xs font-medium text-gray-300">{status}</span>
            </motion.div>
        </Tooltip>
    );
};
