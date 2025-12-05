"use client";

import React, { HTMLAttributes } from 'react';

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
    variant?: 'default' | 'success' | 'danger' | 'warning' | 'info';
    size?: 'sm' | 'md' | 'lg';
    dot?: boolean;
}

export const Badge: React.FC<BadgeProps> = ({
    children,
    variant = 'default',
    size = 'md',
    dot = false,
    className = '',
    ...props
}) => {
    const baseStyles = `
    inline-flex items-center gap-1.5
    font-semibold rounded-full
    transition-all duration-200
  `;

    const variants = {
        default: 'bg-gray-700/50 text-gray-300 border border-gray-600/50',
        success: 'bg-green-500/10 text-green-400 border border-green-500/30',
        danger: 'bg-red-500/10 text-red-400 border border-red-500/30',
        warning: 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/30',
        info: 'bg-blue-500/10 text-blue-400 border border-blue-500/30',
    };

    const sizes = {
        sm: 'px-2 py-0.5 text-xs',
        md: 'px-2.5 py-1 text-sm',
        lg: 'px-3 py-1.5 text-base',
    };

    const dotColors = {
        default: 'bg-gray-400',
        success: 'bg-green-400',
        danger: 'bg-red-400',
        warning: 'bg-yellow-400',
        info: 'bg-blue-400',
    };

    return (
        <span
            className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
            {...props}
        >
            {dot && (
                <span className={`w-1.5 h-1.5 rounded-full ${dotColors[variant]} animate-pulse`} />
            )}
            {children}
        </span>
    );
};
