'use client';

import { useEffect, useRef } from 'react';
import { createChart, IChartApi, LineSeries } from 'lightweight-charts';

interface PortfolioChartProps {
    data: { time: number; value: number }[];
    initialBalance: number;
}

export default function PortfolioChart({ data, initialBalance }: PortfolioChartProps) {
    const chartContainerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);

    useEffect(() => {
        if (!chartContainerRef.current) return;

        const chart = createChart(chartContainerRef.current, {
            width: chartContainerRef.current.clientWidth,
            height: 300,
            layout: {
                background: { color: 'transparent' },
                textColor: '#9ca3af',
            },
            grid: {
                vertLines: { color: 'rgba(255, 255, 255, 0.05)' },
                horzLines: { color: 'rgba(255, 255, 255, 0.05)' },
            },
            crosshair: {
                mode: 1,
            },
            rightPriceScale: {
                borderColor: 'rgba(255, 255, 255, 0.1)',
            },
            timeScale: {
                borderColor: 'rgba(255, 255, 255, 0.1)',
                timeVisible: true,
                secondsVisible: false,
            },
        });

        const lineSeries = chart.addSeries(LineSeries, {
            color: '#8b5cf6',
            lineWidth: 2,
            priceFormat: {
                type: 'price',
                precision: 2,
                minMove: 0.01,
            },
        });

        lineSeries.createPriceLine({
            price: initialBalance,
            color: '#64748b',
            lineWidth: 1,
            lineStyle: 2,
            axisLabelVisible: true,
            title: 'Initial',
        });

        if (data.length > 0) {
            const chartData = data.map((d) => ({
                time: d.time as any, // Cast to any to avoid type issues with Time type
                value: d.value,
            }));
            lineSeries.setData(chartData);
        }

        chartRef.current = chart;

        const handleResize = () => {
            if (chartContainerRef.current && chartRef.current) {
                chartRef.current.applyOptions({
                    width: chartContainerRef.current.clientWidth,
                });
            }
        };

        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('resize', handleResize);
            chart.remove();
        };
    }, [data, initialBalance]);

    return (
        <div className="w-full">
            <div ref={chartContainerRef} className="w-full" />
        </div>
    );
}
