"use client";

import React, { useEffect, useRef } from 'react';
import { createChart, ColorType, IChartApi, ISeriesApi, UTCTimestamp } from 'lightweight-charts';

interface ChartProps {
  data: { time: number; open: number; high: number; low: number; close: number }[];
  onRefresh?: () => void;
  timeframe: string;
  onTimeframeChange: (tf: string) => void;
}

export const CryptoChart: React.FC<ChartProps> = ({ data, onRefresh, timeframe, onTimeframeChange }) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candlestickSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);

  // Initial Chart Setup
  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: '#9CA3AF',
      },
      grid: {
        vertLines: { color: 'rgba(55, 65, 81, 0.2)' },
        horzLines: { color: 'rgba(55, 65, 81, 0.2)' },
      },
      width: chartContainerRef.current.clientWidth,
      height: 500,
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
        borderColor: '#374151',
      },
      rightPriceScale: {
        borderColor: '#374151',
      },
    });

    // Candlestick Series
    const candlestickSeries = (chart as any).addCandlestickSeries({
      upColor: '#10B981',
      downColor: '#EF4444',
      borderVisible: false,
      wickUpColor: '#10B981',
      wickDownColor: '#EF4444',
    });

    chartRef.current = chart;
    candlestickSeriesRef.current = candlestickSeries;

    // Resize Handler
    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, []);

  // Data Update
  useEffect(() => {
    if (!candlestickSeriesRef.current || !data) return;

    // Convert timestamps to UTCTimestamp/BusinessDay format if needed
    // lightweight-charts expects sorted data
    const sortedData = [...data]
      .sort((a, b) => a.time - b.time)
      .map(item => ({
        time: item.time as UTCTimestamp,
        open: item.open,
        high: item.high,
        low: item.low,
        close: item.close,
      }));

    candlestickSeriesRef.current.setData(sortedData);

    // Fit content if it's the first load or drastic change
    chartRef.current?.timeScale().fitContent();

  }, [data]);

  // Simple Timeframe Selector (Overlay)
  const timeframes = ['15m', '1h', '4h', '1d', '1w'];

  return (
    <div className="relative w-full h-full">
      {/* Header / Controls */}
      <div className="absolute top-4 right-4 z-10 flex gap-2">
        {timeframes.map((tf) => (
          <button
            key={tf}
            onClick={() => onTimeframeChange(tf)}
            className={`px-3 py-1 text-xs rounded-lg transition-colors backdrop-blur-md border ${timeframe === tf
              ? 'bg-cyan-500/20 border-cyan-500 text-cyan-400'
              : 'bg-gray-800/50 border-gray-700 text-gray-400 hover:text-white'
              }`}
          >
            {tf.toUpperCase()}
          </button>
        ))}
      </div>

      <div ref={chartContainerRef} className="w-full h-[500px]" />
    </div>
  );
};
