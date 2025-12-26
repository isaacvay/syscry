"use client";

import React, { HTMLAttributes, forwardRef } from 'react';
import { motion, HTMLMotionProps } from 'framer-motion';

export interface CardProps extends HTMLMotionProps<"div"> {
    children?: React.ReactNode;
    variant?: 'default' | 'glass' | 'gradient';
    hover?: boolean;
    glow?: boolean;
}

export const Card = forwardRef<HTMLDivElement, CardProps>(
    (
        {
            children,
            variant = 'default',
            hover = true,
            glow = false,
            className = '',
            ...props
        },
        ref
    ) => {
        const baseStyles = `
      rounded-2xl p-6
      transition-all duration-300
    `;

        const variants = {
            default: `
        bg-gray-800/90 border border-gray-700/50
        ${hover ? 'hover:border-gray-600/70 hover:bg-gray-800' : ''}
        ${glow ? 'shadow-xl shadow-cyan-500/10 hover:shadow-cyan-500/20' : 'shadow-lg'}
      `,
            glass: `
        glass
        ${hover ? 'hover:bg-gray-800/80' : ''}
      `,
            gradient: `
        bg-gradient-to-br from-gray-800/90 via-gray-800/80 to-gray-900/90
        border border-gray-700/30
        ${hover ? 'hover:border-gray-600/50' : ''}
        ${glow ? 'shadow-xl shadow-purple-500/10 hover:shadow-purple-500/20' : 'shadow-lg'}
      `,
        };

        const CardComponent = hover ? motion.div : ('div' as any);
        const motionProps = hover
            ? {
                whileHover: { y: -2, scale: 1.005 },
                transition: { duration: 0.2 },
            }
            : {};

        return (
            <CardComponent
                ref={ref}
                className={`${baseStyles} ${variants[variant]} ${className}`}
                {...motionProps}
                {...props}
            >
                {children}
            </CardComponent>
        );
    }
);

Card.displayName = 'Card';

export const CardHeader = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
    ({ className = '', ...props }, ref) => (
        <div ref={ref} className={`mb-4 ${className}`} {...props} />
    )
);

CardHeader.displayName = 'CardHeader';

export const CardTitle = forwardRef<HTMLHeadingElement, HTMLAttributes<HTMLHeadingElement>>(
    ({ className = '', ...props }, ref) => (
        <h3 ref={ref} className={`text-xl font-bold text-white ${className}`} {...props} />
    )
);

CardTitle.displayName = 'CardTitle';

export const CardDescription = forwardRef<HTMLParagraphElement, HTMLAttributes<HTMLParagraphElement>>(
    ({ className = '', ...props }, ref) => (
        <p ref={ref} className={`text-sm text-gray-400 mt-1 ${className}`} {...props} />
    )
);

CardDescription.displayName = 'CardDescription';

export const CardContent = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
    ({ className = '', ...props }, ref) => (
        <div ref={ref} className={className} {...props} />
    )
);

CardContent.displayName = 'CardContent';

export const CardFooter = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
    ({ className = '', ...props }, ref) => (
        <div ref={ref} className={`mt-4 pt-4 border-t border-gray-700/50 ${className}`} {...props} />
    )
);

CardFooter.displayName = 'CardFooter';
