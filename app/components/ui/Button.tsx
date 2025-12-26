"use client";

import React, { forwardRef } from 'react';
import { motion, HTMLMotionProps } from 'framer-motion';

export interface ButtonProps extends HTMLMotionProps<"button"> {
    children?: React.ReactNode;
    variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'success';
    size?: 'sm' | 'md' | 'lg';
    isLoading?: boolean;
    leftIcon?: React.ReactNode;
    rightIcon?: React.ReactNode;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
    (
        {
            children,
            variant = 'primary',
            size = 'md',
            isLoading = false,
            leftIcon,
            rightIcon,
            className = '',
            disabled,
            ...props
        },
        ref
    ) => {
        const baseStyles = `
      inline-flex items-center justify-center gap-2
      font-semibold rounded-xl
      transition-all duration-200
      focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-900
      disabled:opacity-50 disabled:cursor-not-allowed
      relative overflow-hidden
    `;

        const variants = {
            primary: `
        bg-gradient-to-r from-cyan-500 to-blue-600
        hover:from-cyan-400 hover:to-blue-500
        text-white shadow-lg shadow-cyan-500/30
        hover:shadow-xl hover:shadow-cyan-500/40
        focus:ring-cyan-500
      `,
            secondary: `
        bg-gray-800 hover:bg-gray-700
        text-white border border-gray-700
        hover:border-gray-600
        focus:ring-gray-600
      `,
            ghost: `
        bg-transparent hover:bg-gray-800/50
        text-gray-300 hover:text-white
        focus:ring-gray-700
      `,
            danger: `
        bg-gradient-to-r from-red-500 to-rose-600
        hover:from-red-400 hover:to-rose-500
        text-white shadow-lg shadow-red-500/30
        hover:shadow-xl hover:shadow-red-500/40
        focus:ring-red-500
      `,
            success: `
        bg-gradient-to-r from-green-500 to-emerald-600
        hover:from-green-400 hover:to-emerald-500
        text-white shadow-lg shadow-green-500/30
        hover:shadow-xl hover:shadow-green-500/40
        focus:ring-green-500
      `,
        };

        const sizes = {
            sm: 'px-3 py-1.5 text-sm',
            md: 'px-4 py-2.5 text-base',
            lg: 'px-6 py-3.5 text-lg',
        };

        return (
            <motion.button
                ref={ref}
                className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
                disabled={disabled || isLoading}
                whileHover={{ scale: disabled || isLoading ? 1 : 1.02 }}
                whileTap={{ scale: disabled || isLoading ? 1 : 0.98 }}
                {...props}
            >
                {/* Ripple effect background */}
                <span className="absolute inset-0 overflow-hidden rounded-xl">
                    <span className="absolute inset-0 bg-white/0 hover:bg-white/10 transition-colors duration-300" />
                </span>

                {/* Content */}
                <span className="relative flex items-center gap-2">
                    {isLoading ? (
                        <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                        </svg>
                    ) : leftIcon}
                    {children}
                    {rightIcon}
                </span>
            </motion.button>
        );
    }
);

Button.displayName = 'Button';
