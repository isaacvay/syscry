"use client";

import React, { useState, useEffect, useRef } from 'react';
import { TrendingUp, TrendingDown, Activity, BarChart3, CandlestickChart, LineChart as LineChartIcon, AreaChart as AreaChartIcon, ZoomIn, ZoomOut } from 'lucide-react';

interface ChartProps {
  data: { time: number; open: number; high: number; low: number; close: number }[];
  onRefresh?: () => void;
  timeframe: string;
  onTimeframeChange: (tf: string) => void;
}

type ChartType = 'candlestick' | 'line' | 'area';

export const CryptoChart: React.FC<ChartProps> = ({ data, onRefresh, timeframe, onTimeframeChange }) => {
  const [chartType, setChartType] = useState<ChartType>('candlestick');
  // timeframe state removed, using prop instead
  const [showMA, setShowMA] = useState(true);
  const [showRSI, setShowRSI] = useState(false);
  const [showVolume, setShowVolume] = useState(true);
  const [showBB, setShowBB] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(new Date());
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  const [mousePos, setMousePos] = useState<{ x: number; y: number } | null>(null);
  const [tooltipPosition, setTooltipPosition] = useState<{ x: number; y: number } | null>(null);
  const [zoomLevel, setZoomLevel] = useState(2.0);
  const [panOffset, setPanOffset] = useState(0);
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (onRefresh) {
      const interval = setInterval(() => {
        onRefresh();
        setLastUpdate(new Date());
      }, 30000);
      return () => clearInterval(interval);
    }
  }, [onRefresh]);

  if (!data || data.length === 0) {
    return (
      <div className="w-full h-[600px] flex items-center justify-center bg-gradient-to-br from-gray-900 to-gray-800 rounded-xl border border-gray-700">
        <p className="text-gray-400">Aucune donnée de graphique disponible</p>
      </div>
    );
  }

  // Timeframe configuration - defines labels
  const getTimeframeConfig = () => {
    switch (timeframe) {
      case 'all': return { label: 'All Data' };
      case '15m': return { label: '15m' };
      case '1h': return { label: '1h' };
      case '4h': return { label: '4h' };
      case '1d': return { label: '1d' };
      case '1w': return { label: '1w' };
      default: return { label: timeframe };
    }
  };

  const timeframeConfig = getTimeframeConfig();
  const filteredData = data; // Use all available data, don't slice history

  // 1. Calculate Indicators (depend on filteredData)
  // Volume
  const volumeData = filteredData.map((candle, idx) => {
    const baseVolume = 500000 + Math.random() * 1000000;
    const volatility = Math.abs(candle.close - candle.open) / candle.open;
    return baseVolume * (1 + volatility * 5);
  });
  const maxVolume = Math.max(...volumeData);

  // RSI
  const calculateRSI = (period = 14) => {
    const rsi: (number | null)[] = [];
    for (let i = 0; i < filteredData.length; i++) {
      if (i < period) {
        rsi.push(null);
        continue;
      }
      let gains = 0;
      let losses = 0;
      for (let j = i - period + 1; j <= i; j++) {
        const change = filteredData[j].close - filteredData[j - 1].close;
        if (change > 0) gains += change;
        else losses += Math.abs(change);
      }
      const avgGain = gains / period;
      const avgLoss = losses / period;
      const rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
      const rsiValue = 100 - (100 / (1 + rs));
      rsi.push(rsiValue);
    }
    return rsi;
  };
  const rsiData = showRSI ? calculateRSI() : [];

  // MA
  const calculateMA = (period: number) => {
    return filteredData.map((_, idx) => {
      if (idx < period - 1) return null;
      const sum = filteredData.slice(idx - period + 1, idx + 1).reduce((acc, d) => acc + d.close, 0);
      return sum / period;
    });
  };
  const ma7 = showMA ? calculateMA(7) : [];
  const ma20 = showMA ? calculateMA(20) : [];
  const ma50 = showMA ? calculateMA(50) : [];

  // BB
  const calculateBB = (period = 20, stdDev = 2) => {
    const bb: { upper: number | null; middle: number | null; lower: number | null }[] = [];
    for (let i = 0; i < filteredData.length; i++) {
      if (i < period - 1) {
        bb.push({ upper: null, middle: null, lower: null });
        continue;
      }
      const slice = filteredData.slice(i - period + 1, i + 1);
      const mean = slice.reduce((sum, d) => sum + d.close, 0) / period;
      const variance = slice.reduce((sum, d) => sum + Math.pow(d.close - mean, 2), 0) / period;
      const std = Math.sqrt(variance);
      bb.push({
        upper: mean + stdDev * std,
        middle: mean,
        lower: mean - stdDev * std,
      });
    }
    return bb;
  };
  const bbData = showBB ? calculateBB() : [];

  // 2. Zoom & Visible Data Calculation
  const BASE_CANDLE_WIDTH = 16;
  const CANDLE_SPACING = 4;

  // Reset zoom when timeframe changes
  useEffect(() => {
    setZoomLevel(1.0); // Default to 100% (approx 70 candles visible)
    setPanOffset(0);
  }, [timeframe]);

  const candleWidth = BASE_CANDLE_WIDTH * zoomLevel;
  const CANDLE_TOTAL_WIDTH = candleWidth + CANDLE_SPACING;

  // Chart dimensions configuration
  const margin = { top: 20, right: 100, bottom: 50, left: 100 };
  const volumeHeight = showVolume ? 100 : 0;
  const mainHeight = showRSI ? 600 : 700;
  const rsiHeight = 120;

  // Calculate max visible candles based on minimum width assumption (will adjust later)
  const maxVisibleCandles = Math.floor(1400 / CANDLE_TOTAL_WIDTH);
  const candlesVisible = Math.min(filteredData.length, maxVisibleCandles);

  const startIndex = Math.max(0, Math.min(filteredData.length - candlesVisible, panOffset));
  const visibleData = filteredData.slice(startIndex, startIndex + candlesVisible);

  // 3. Stats & Scaling (based on VISIBLE data)
  const visiblePrices = visibleData.flatMap(d => [d.high, d.low]);

  // Include BB in min/max if visible
  if (showBB && bbData.length > 0) {
    for (let i = 0; i < visibleData.length; i++) {
      const idx = startIndex + i;
      if (bbData[idx] && bbData[idx].upper !== null && bbData[idx].lower !== null) {
        visiblePrices.push(bbData[idx].upper!);
        visiblePrices.push(bbData[idx].lower!);
      }
    }
  }

  const minPrice = visiblePrices.length > 0 ? Math.min(...visiblePrices) : 0;
  const maxPrice = visiblePrices.length > 0 ? Math.max(...visiblePrices) : 100;
  const priceRange = maxPrice - minPrice;
  const padding = priceRange * 0.1;

  const currentPrice = filteredData[filteredData.length - 1]?.close || 0;
  const firstPrice = filteredData[0]?.open || 0;
  const priceChange = currentPrice - firstPrice;
  const priceChangePercent = ((priceChange / firstPrice) * 100).toFixed(2);

  // 4. Final Chart Dimensions
  const calculatedWidth = candlesVisible * CANDLE_TOTAL_WIDTH + margin.left + margin.right;
  const width = Math.max(1400, calculatedWidth);
  const totalHeight = mainHeight + volumeHeight + (showRSI ? rsiHeight + 40 : 40);
  const chartWidth = candlesVisible * CANDLE_TOTAL_WIDTH;
  const chartHeight = mainHeight - margin.top - margin.bottom;

  // 5. Scales
  const xScale = (index: number) => {
    const relativeIndex = index - startIndex;
    return relativeIndex * CANDLE_TOTAL_WIDTH + candleWidth / 2;
  };

  const yScale = (price: number) => {
    return chartHeight - ((price - (minPrice - padding)) / (maxPrice - minPrice + 2 * padding)) * chartHeight;
  };
  const rsiYScale = (value: number) => (100 - value) / 100 * (rsiHeight - 20);

  // Mouse move handler - improved detection
  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!svgRef.current) return;
    const rect = svgRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left - margin.left;
    const y = e.clientY - rect.top - margin.top;

    if (x >= 0 && x <= chartWidth && y >= 0 && y <= chartHeight) {
      setMousePos({ x, y });

      // Store absolute position for tooltip
      setTooltipPosition({
        x: e.clientX,
        y: e.clientY
      });

      // Find the nearest candle based on x position
      let nearestIndex = 0;
      let minDistance = Infinity;

      for (let i = 0; i < visibleData.length; i++) {
        const actualIndex = startIndex + i;
        const candleX = xScale(actualIndex);
        const distance = Math.abs(x - candleX);

        if (distance < minDistance) {
          minDistance = distance;
          nearestIndex = actualIndex;
        }
      }

      // Only set hovered index if we're close enough to a candle
      if (minDistance < CANDLE_TOTAL_WIDTH / 2) {
        setHoveredIndex(nearestIndex);
      } else {
        setHoveredIndex(null);
      }
    } else {
      setMousePos(null);
      setTooltipPosition(null);
      setHoveredIndex(null);
    }
  };

  // Zoom handlers - adjust candle width
  const handleZoomIn = () => {
    setZoomLevel(prev => Math.min(prev * 1.2, 5)); // Make candles bigger
  };

  const handleZoomOut = () => {
    setZoomLevel(prev => Math.max(prev / 1.2, 0.5)); // Make candles smaller
  };

  const handleResetZoom = () => {
    setZoomLevel(1.0); // Reset to 100%
    setPanOffset(0);
  };

  // Wheel zoom
  const handleWheel = (e: React.WheelEvent<SVGSVGElement>) => {
    e.preventDefault();
    if (e.deltaY < 0) { // Scroll up = zoom in = bigger candles
      handleZoomIn();
    } else { // Scroll down = zoom out = smaller candles
      handleZoomOut();
    }
  };

  // Render candlestick with zoom-based width
  const renderCandle = (candle: any, index: number) => {
    const actualIndex = startIndex + index;
    const x = xScale(actualIndex);

    const highY = yScale(candle.high);
    const lowY = yScale(candle.low);
    const openY = yScale(candle.open);
    const closeY = yScale(candle.close);

    const isGreen = candle.close >= candle.open;
    const color = isGreen ? '#10B981' : '#EF4444';
    const glowColor = isGreen ? 'rgba(16, 185, 129, 0.4)' : 'rgba(239, 68, 68, 0.4)';

    const bodyTop = Math.min(openY, closeY);
    const bodyBottom = Math.max(openY, closeY);
    const bodyHeight = Math.max(Math.abs(bodyBottom - bodyTop), 1);

    const isHovered = hoveredIndex === actualIndex;

    return (
      <g key={`candle-${actualIndex}`}>
        {/* Glow effect for hovered candle */}
        {isHovered && (
          <>
            <line
              x1={x} y1={highY} x2={x} y2={lowY}
              stroke={glowColor}
              strokeWidth={Math.max(6, zoomLevel * 2)}
              opacity={0.6}
              filter="url(#glow)"
            />
            <rect
              x={x - candleWidth / 2}
              y={bodyTop}
              width={candleWidth}
              height={bodyHeight}
              fill={glowColor}
              stroke="none"
              rx={2}
              opacity={0.5}
              filter="url(#glow)"
            />
          </>
        )}

        {/* Main candle wick */}
        <line
          x1={x} y1={highY} x2={x} y2={lowY}
          stroke={color}
          strokeWidth={Math.max(2, zoomLevel)}
          opacity={isHovered ? 1 : 0.9}
          strokeLinecap="round"
        />

        {/* Candle body */}
        <rect
          x={x - candleWidth / 2}
          y={bodyTop}
          width={candleWidth}
          height={bodyHeight}
          fill={color}
          stroke={color}
          strokeWidth={1}
          rx={2}
          opacity={isHovered ? 1 : 0.95}
          style={{
            filter: isHovered ? `drop-shadow(0 0 8px ${glowColor})` : 'none',
            transition: 'all 0.2s ease'
          }}
        />
      </g>
    );
  };

  // Render line
  const renderLine = () => {
    const points = filteredData.map((d, i) => `${xScale(i)},${yScale(d.close)}`).join(' ');
    return <polyline points={points} fill="none" stroke="#3B82F6" strokeWidth={2.5} />;
  };

  // Render area
  const renderArea = () => {
    const points = filteredData.map((d, i) => `${xScale(i)},${yScale(d.close)}`).join(' ');
    const areaPoints = `0,${chartHeight} ${points} ${chartWidth},${chartHeight}`;
    return (
      <>
        <polygon points={areaPoints} fill="url(#areaGradient)" opacity={0.4} />
        <polyline points={points} fill="none" stroke="#3B82F6" strokeWidth={2.5} />
      </>
    );
  };

  // Render Bollinger Bands
  const renderBB = () => {
    if (!showBB || bbData.length === 0) return null;

    const upperPoints = bbData.map((bb, i) => bb.upper !== null ? `${xScale(i)},${yScale(bb.upper)}` : null).filter(p => p !== null).join(' ');
    const middlePoints = bbData.map((bb, i) => bb.middle !== null ? `${xScale(i)},${yScale(bb.middle)}` : null).filter(p => p !== null).join(' ');
    const lowerPoints = bbData.map((bb, i) => bb.lower !== null ? `${xScale(i)},${yScale(bb.lower)}` : null).filter(p => p !== null).join(' ');

    // Create filled area between bands
    const upperPointsArray = bbData.map((bb, i) => bb.upper !== null ? { x: xScale(i), y: yScale(bb.upper) } : null).filter(p => p !== null);
    const lowerPointsArray = bbData.map((bb, i) => bb.lower !== null ? { x: xScale(i), y: yScale(bb.lower) } : null).filter(p => p !== null);
    const areaPoints = [...upperPointsArray.map(p => `${p!.x},${p!.y}`), ...lowerPointsArray.reverse().map(p => `${p!.x},${p!.y}`)].join(' ');

    return (
      <>
        <polygon points={areaPoints} fill="#3B82F6" opacity={0.1} />
        <polyline points={upperPoints} fill="none" stroke="#3B82F6" strokeWidth={1} opacity={0.6} strokeDasharray="4 2" />
        <polyline points={middlePoints} fill="none" stroke="#3B82F6" strokeWidth={1.5} opacity={0.7} />
        <polyline points={lowerPoints} fill="none" stroke="#3B82F6" strokeWidth={1} opacity={0.6} strokeDasharray="4 2" />
      </>
    );
  };

  // Render MA
  const renderMA = (maData: (number | null)[], color: string, width: number, strokeDasharray?: string) => {
    const points = maData
      .map((value, i) => value !== null ? `${xScale(i)},${yScale(value)}` : null)
      .filter(p => p !== null)
      .join(' ');
    return (
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth={width}
        opacity={0.85}
        strokeDasharray={strokeDasharray}
        strokeLinecap="round"
        strokeLinejoin="round"
        filter="url(#glow)"
      />
    );
  };

  // Render RSI
  const renderRSI = () => {
    if (!showRSI || rsiData.length === 0) return null;

    const rsiY = mainHeight + volumeHeight + 20;
    const points = rsiData
      .map((value, i) => value !== null ? `${xScale(i)},${rsiYScale(value)}` : null)
      .filter(p => p !== null)
      .join(' ');

    return (
      <g transform={`translate(0, ${rsiY})`}>
        {/* RSI background */}
        <rect x={0} y={0} width={chartWidth} height={rsiHeight - 20} fill="#1F2937" opacity={0.3} rx={4} />

        {/* Overbought/Oversold lines */}
        <line x1={0} y1={rsiYScale(70)} x2={chartWidth} y2={rsiYScale(70)} stroke="#EF4444" strokeWidth={1} strokeDasharray="4 4" opacity={0.5} />
        <line x1={0} y1={rsiYScale(30)} x2={chartWidth} y2={rsiYScale(30)} stroke="#10B981" strokeWidth={1} strokeDasharray="4 4" opacity={0.5} />
        <line x1={0} y1={rsiYScale(50)} x2={chartWidth} y2={rsiYScale(50)} stroke="#6B7280" strokeWidth={0.5} opacity={0.3} />

        {/* RSI line */}
        <polyline points={points} fill="none" stroke="#A855F7" strokeWidth={2} />

        {/* Labels */}
        <text x={chartWidth + 10} y={rsiYScale(70)} fill="#EF4444" fontSize="9" dominantBaseline="middle">70</text>
        <text x={chartWidth + 10} y={rsiYScale(50)} fill="#6B7280" fontSize="9" dominantBaseline="middle">50</text>
        <text x={chartWidth + 10} y={rsiYScale(30)} fill="#10B981" fontSize="9" dominantBaseline="middle">30</text>
        <text x={-60} y={rsiYScale(50)} fill="#A855F7" fontSize="11" fontWeight="bold" dominantBaseline="middle">RSI</text>
      </g>
    );
  };

  // Render volume bars
  const renderVolume = () => {
    if (!showVolume) return null;

    const volumeY = mainHeight + 10;
    const volumeBarHeight = volumeHeight - 20;

    return (
      <g transform={`translate(0, ${volumeY})`}>
        <rect x={0} y={0} width={chartWidth} height={volumeBarHeight} fill="#1F2937" opacity={0.2} rx={4} />
        {volumeData.map((vol, i) => {
          const x = xScale(i);
          const barWidth = Math.max((chartWidth / filteredData.length) * 0.6, 1);
          const barHeight = (vol / maxVolume) * volumeBarHeight;
          const isGreen = filteredData[i].close >= filteredData[i].open;
          const color = isGreen ? '#10B981' : '#EF4444';

          return (
            <rect
              key={`vol-${i}`}
              x={x - barWidth / 2}
              y={volumeBarHeight - barHeight}
              width={barWidth}
              height={barHeight}
              fill={color}
              opacity={hoveredIndex === i ? 0.8 : 0.4}
            />
          );
        })}
        <text x={-60} y={volumeBarHeight / 2} fill="#8B5CF6" fontSize="11" fontWeight="bold" dominantBaseline="middle">VOL</text>
      </g>
    );
  };

  // Y-axis ticks
  const yTicks = 6;
  const yTickValues = Array.from({ length: yTicks }, (_, i) => {
    return minPrice - padding + ((maxPrice - minPrice + 2 * padding) / (yTicks - 1)) * i;
  });

  const hoveredCandle = hoveredIndex !== null ? filteredData[hoveredIndex] : null;
  const hoveredRSI = hoveredIndex !== null && rsiData[hoveredIndex] !== null && rsiData[hoveredIndex] !== undefined ? rsiData[hoveredIndex] : null;

  return (
    <>
      {/* Floating Tooltip - follows cursor (outside main container) */}
      {hoveredCandle && tooltipPosition && (
        <div
          className="fixed pointer-events-none transition-all duration-100 ease-out"
          style={{
            left: `${tooltipPosition.x + 20}px`,
            top: `${tooltipPosition.y - 80}px`,
            transform: tooltipPosition.x > window.innerWidth - 400 ? 'translateX(-100%) translateX(-40px)' : 'none',
            zIndex: 9999
          }}
        >
          <div className="bg-gradient-to-br from-gray-900/98 via-gray-800/98 to-gray-900/98 border-2 border-gray-700/80 rounded-2xl backdrop-blur-xl shadow-2xl p-4 min-w-[320px]">
            {/* Header with symbol and time */}
            <div className="flex justify-between items-center mb-3 pb-2 border-b border-gray-700/50">
              <div className="flex items-center gap-2">
                <div className={`w-3 h-3 rounded-full ${hoveredCandle.close >= hoveredCandle.open ? 'bg-green-500 shadow-lg shadow-green-500/50' : 'bg-red-500 shadow-lg shadow-red-500/50'}`}></div>
                <span className="text-white font-bold text-sm">
                  {new Date(hoveredCandle.time * 1000).toLocaleString('fr-FR', {
                    day: '2-digit',
                    month: 'short',
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </span>
              </div>
            </div>

            {/* OHLC Data */}
            <div className="grid grid-cols-2 gap-3 mb-3">
              <div className="flex justify-between items-center px-2 py-1.5 bg-gray-800/40 rounded-lg">
                <span className="text-gray-400 text-xs font-medium">Open</span>
                <span className="text-white font-mono font-bold text-sm">${hoveredCandle.open.toFixed(2)}</span>
              </div>
              <div className="flex justify-between items-center px-2 py-1.5 bg-green-500/10 border border-green-500/20 rounded-lg">
                <span className="text-gray-400 text-xs font-medium">High</span>
                <span className="text-green-400 font-mono font-bold text-sm drop-shadow-[0_0_8px_rgba(34,197,94,0.4)]">${hoveredCandle.high.toFixed(2)}</span>
              </div>
              <div className="flex justify-between items-center px-2 py-1.5 bg-red-500/10 border border-red-500/20 rounded-lg">
                <span className="text-gray-400 text-xs font-medium">Low</span>
                <span className="text-red-400 font-mono font-bold text-sm drop-shadow-[0_0_8px_rgba(248,113,113,0.4)]">${hoveredCandle.low.toFixed(2)}</span>
              </div>
              <div className="flex justify-between items-center px-2 py-1.5 bg-gray-800/40 rounded-lg">
                <span className="text-gray-400 text-xs font-medium">Close</span>
                <span className="text-white font-mono font-black text-sm">${hoveredCandle.close.toFixed(2)}</span>
              </div>
            </div>

            {/* Change percentage */}
            <div className={`flex justify-between items-center px-3 py-2 rounded-lg border-2 ${hoveredCandle.close >= hoveredCandle.open
              ? 'bg-green-500/10 border-green-500/30'
              : 'bg-red-500/10 border-red-500/30'
              }`}>
              <span className="text-gray-300 text-xs font-semibold">Change</span>
              <span className={`font-mono font-black text-base ${hoveredCandle.close >= hoveredCandle.open
                ? 'text-green-400 drop-shadow-[0_0_10px_rgba(34,197,94,0.5)]'
                : 'text-red-400 drop-shadow-[0_0_10px_rgba(248,113,113,0.5)]'
                }`}>
                {hoveredCandle.close >= hoveredCandle.open ? '+' : ''}
                {((hoveredCandle.close - hoveredCandle.open) / hoveredCandle.open * 100).toFixed(2)}%
              </span>
            </div>

            {/* RSI if available */}
            {hoveredRSI !== null && typeof hoveredRSI === 'number' && (
              <div className="mt-3 flex justify-between items-center px-3 py-2 bg-purple-500/10 border border-purple-500/20 rounded-lg">
                <span className="text-gray-300 text-xs font-semibold">RSI (14)</span>
                <span className="text-purple-400 font-mono font-bold text-sm drop-shadow-[0_0_8px_rgba(168,85,247,0.4)]">
                  {hoveredRSI.toFixed(1)}
                </span>
              </div>
            )}

            {/* Tooltip arrow */}
            <div
              className={`absolute w-3 h-3 bg-gray-900 border-l-2 border-b-2 border-gray-700/80 transform rotate-45 ${tooltipPosition.x > window.innerWidth - 400 ? 'right-5' : '-left-1.5'
                }`}
              style={{ top: '50%', marginTop: '-6px' }}
            ></div>
          </div>
        </div>
      )}

      <div className="w-full relative overflow-hidden bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 rounded-2xl border border-gray-700/50 p-6 shadow-2xl backdrop-blur-sm">
        {/* Animated Background Glow */}
        <div className="absolute inset-0 opacity-30 pointer-events-none">
          <div className="absolute top-0 right-0 w-64 h-64 bg-cyan-500/20 rounded-full blur-3xl animate-pulse"></div>
          <div className="absolute bottom-0 left-0 w-64 h-64 bg-purple-500/20 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }}></div>
        </div>

        {/* Header */}
        <div className="relative z-10 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-gradient-to-br from-blue-500/20 to-cyan-500/20 rounded-xl border border-blue-500/30 backdrop-blur-sm">
                <BarChart3 className="w-6 h-6 text-blue-400 drop-shadow-[0_0_8px_rgba(59,130,246,0.5)]" />
              </div>
              <h3 className="text-xl font-bold bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">Analyse Technique</h3>
              <div className="flex items-center gap-2 px-3 py-1.5 bg-gradient-to-r from-green-900/40 to-emerald-900/40 rounded-lg border border-green-500/30 backdrop-blur-sm shadow-lg shadow-green-500/10">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse shadow-lg shadow-green-500/50"></div>
                <span className="text-xs font-semibold text-green-400">Live</span>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-4xl font-black bg-gradient-to-r from-white via-gray-100 to-gray-300 bg-clip-text text-transparent drop-shadow-lg">${currentPrice.toFixed(2)}</span>
              <div className={`flex items-center gap-1.5 px-4 py-2 rounded-xl backdrop-blur-sm border shadow-lg transition-all duration-300 ${priceChange >= 0
                ? 'bg-gradient-to-r from-green-900/40 to-emerald-900/40 border-green-500/30 text-green-400 shadow-green-500/20'
                : 'bg-gradient-to-r from-red-900/40 to-rose-900/40 border-red-500/30 text-red-400 shadow-red-500/20'}`}>
                {priceChange >= 0 ? <TrendingUp className="w-5 h-5 drop-shadow-lg" /> : <TrendingDown className="w-5 h-5 drop-shadow-lg" />}
                <span className="font-bold text-lg">{priceChange >= 0 ? '+' : ''}{priceChangePercent}%</span>
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-2 font-medium">
              Dernière mise à jour: {lastUpdate.toLocaleTimeString('fr-FR')}
            </p>
          </div>

          {/* Controls */}
          <div className="relative z-10 flex flex-wrap gap-2">
            {/* Chart Type */}
            <div className="flex gap-1 bg-gray-800/60 backdrop-blur-md p-1.5 rounded-xl border border-gray-700/50 shadow-lg">
              <button onClick={() => setChartType('candlestick')} className={`p-2.5 rounded-lg transition-all duration-300 ${chartType === 'candlestick' ? 'bg-gradient-to-br from-blue-600 to-cyan-600 text-white shadow-lg shadow-blue-500/30' : 'text-gray-400 hover:text-white hover:bg-gray-700/50'}`} title="Bougies">
                <CandlestickChart className="w-4 h-4" />
              </button>
              <button onClick={() => setChartType('line')} className={`p-2.5 rounded-lg transition-all duration-300 ${chartType === 'line' ? 'bg-gradient-to-br from-blue-600 to-cyan-600 text-white shadow-lg shadow-blue-500/30' : 'text-gray-400 hover:text-white hover:bg-gray-700/50'}`} title="Ligne">
                <LineChartIcon className="w-4 h-4" />
              </button>
              <button onClick={() => setChartType('area')} className={`p-2.5 rounded-lg transition-all duration-300 ${chartType === 'area' ? 'bg-gradient-to-br from-blue-600 to-cyan-600 text-white shadow-lg shadow-blue-500/30' : 'text-gray-400 hover:text-white hover:bg-gray-700/50'}`} title="Zone">
                <AreaChartIcon className="w-4 h-4" />
              </button>
            </div>

            {/* Timeframe */}
            <div className="flex gap-1 bg-gray-800/60 backdrop-blur-md p-1.5 rounded-xl border border-gray-700/50 shadow-lg">
              {(['15m', '1h', '4h', '1d', '1w'] as const).map((tf) => (
                <button key={tf} onClick={() => onTimeframeChange(tf)} className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all duration-300 ${timeframe === tf ? 'bg-gradient-to-br from-green-600 to-emerald-600 text-white shadow-lg shadow-green-500/30' : 'text-gray-400 hover:text-white hover:bg-gray-700/50'}`}>
                  {tf.toUpperCase()}
                </button>
              ))}
            </div>

            {/* Indicators */}
            <button onClick={() => setShowMA(!showMA)} className={`px-4 py-1.5 rounded-xl text-xs font-bold transition-all duration-300 backdrop-blur-md border shadow-lg ${showMA ? 'bg-gradient-to-br from-blue-600 to-cyan-600 text-white border-blue-500/30 shadow-blue-500/30' : 'bg-gray-800/60 text-gray-400 hover:text-white border-gray-700/50 hover:border-gray-600'}`}>MA</button>
            <button onClick={() => setShowBB(!showBB)} className={`px-4 py-1.5 rounded-xl text-xs font-bold transition-all duration-300 backdrop-blur-md border shadow-lg ${showBB ? 'bg-gradient-to-br from-blue-600 to-cyan-600 text-white border-blue-500/30 shadow-blue-500/30' : 'bg-gray-800/60 text-gray-400 hover:text-white border-gray-700/50 hover:border-gray-600'}`}>BB</button>
            <button onClick={() => setShowVolume(!showVolume)} className={`px-4 py-1.5 rounded-xl text-xs font-bold transition-all duration-300 backdrop-blur-md border shadow-lg ${showVolume ? 'bg-gradient-to-br from-purple-600 to-pink-600 text-white border-purple-500/30 shadow-purple-500/30' : 'bg-gray-800/60 text-gray-400 hover:text-white border-gray-700/50 hover:border-gray-600'}`}>VOL</button>
            <button onClick={() => setShowRSI(!showRSI)} className={`px-4 py-1.5 rounded-xl text-xs font-bold transition-all duration-300 backdrop-blur-md border shadow-lg ${showRSI ? 'bg-gradient-to-br from-purple-600 to-pink-600 text-white border-purple-500/30 shadow-purple-500/30' : 'bg-gray-800/60 text-gray-400 hover:text-white border-gray-700/50 hover:border-gray-600'}`}>RSI</button>

            {/* Zoom Controls */}
            <div className="flex gap-1 bg-gray-800/60 backdrop-blur-md p-1.5 rounded-xl border border-gray-700/50 shadow-lg">
              <button onClick={handleZoomOut} className="p-2 text-gray-400 hover:text-white hover:bg-gray-700/50 transition-all duration-300 rounded-lg" title="Zoom Out">
                <ZoomOut className="w-4 h-4" />
              </button>
              <button onClick={handleResetZoom} className="px-3 text-xs font-bold text-gray-400 hover:text-white hover:bg-gray-700/50 transition-all duration-300 rounded-lg" title="Reset Zoom">
                {(zoomLevel * 100).toFixed(0)}%
              </button>
              <button onClick={handleZoomIn} className="p-2 text-gray-400 hover:text-white hover:bg-gray-700/50 transition-all duration-300 rounded-lg" title="Zoom In">
                <ZoomIn className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Legend */}
        <div className="relative z-10 flex flex-wrap gap-4 mb-4 text-xs">
          {showMA && (
            <>
              <div className="flex items-center gap-2 px-3 py-1.5 bg-yellow-500/10 border border-yellow-500/20 rounded-lg backdrop-blur-sm">
                <div className="w-5 h-0.5 bg-gradient-to-r from-yellow-400 to-yellow-500 shadow-lg shadow-yellow-500/30"></div>
                <span className="text-yellow-400 font-semibold">MA7</span>
              </div>
              <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-500/10 border border-blue-500/20 rounded-lg backdrop-blur-sm">
                <div className="w-5 h-0.5 bg-gradient-to-r from-blue-400 to-blue-500 shadow-lg shadow-blue-500/30"></div>
                <span className="text-blue-400 font-semibold">MA20</span>
              </div>
              <div className="flex items-center gap-2 px-3 py-1.5 bg-purple-500/10 border border-purple-500/20 rounded-lg backdrop-blur-sm">
                <div className="w-5 h-0.5 bg-gradient-to-r from-purple-400 to-purple-500 shadow-lg shadow-purple-500/30"></div>
                <span className="text-purple-400 font-semibold">MA50</span>
              </div>
            </>
          )}
          {showBB && <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-500/10 border border-blue-500/20 rounded-lg backdrop-blur-sm"><div className="w-4 h-3 bg-blue-400/20 border border-blue-400/40 rounded"></div><span className="text-blue-400 font-semibold">BB(20,2)</span></div>}
          {showVolume && <div className="flex items-center gap-2 px-3 py-1.5 bg-purple-500/10 border border-purple-500/20 rounded-lg backdrop-blur-sm"><div className="w-3 h-3 bg-gradient-to-br from-purple-500 to-pink-500 opacity-50 rounded"></div><span className="text-purple-400 font-semibold">Volume</span></div>}
          {showRSI && <div className="flex items-center gap-2 px-3 py-1.5 bg-purple-500/10 border border-purple-500/20 rounded-lg backdrop-blur-sm"><div className="w-5 h-0.5 bg-gradient-to-r from-purple-400 to-pink-400 shadow-lg shadow-purple-500/30"></div><span className="text-purple-400 font-semibold">RSI(14)</span></div>}
          <div className="flex items-center gap-3 ml-auto px-4 py-1.5 bg-gray-800/60 border border-gray-700/50 rounded-lg backdrop-blur-sm">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-green-500 shadow-lg shadow-green-500/50 animate-pulse"></div>
              <span className="text-gray-300 font-bold">{timeframeConfig.label}</span>
            </div>
            <span className="text-gray-600">•</span>
            <span className="text-gray-400 font-medium">{filteredData.length} bougies</span>
          </div>
        </div>

        {/* Chart */}
        <div className="relative z-10 w-full overflow-x-auto bg-gray-900/50 rounded-xl p-3 border border-gray-800/50 backdrop-blur-sm">
          <svg ref={svgRef} viewBox={`0 0 ${width} ${totalHeight}`} className="w-full h-auto" onMouseMove={handleMouseMove} onMouseLeave={() => { setMousePos(null); setHoveredIndex(null); }} onWheel={handleWheel}>
            <defs>
              {/* Area gradient */}
              <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#3B82F6" stopOpacity="0.8" />
                <stop offset="50%" stopColor="#8B5CF6" stopOpacity="0.4" />
                <stop offset="100%" stopColor="#3B82F6" stopOpacity="0.05" />
              </linearGradient>

              {/* Glow filter */}
              <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur stdDeviation="4" result="coloredBlur" />
                <feMerge>
                  <feMergeNode in="coloredBlur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>

              {/* Grid gradient */}
              <linearGradient id="gridGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#374151" stopOpacity="0.5" />
                <stop offset="100%" stopColor="#374151" stopOpacity="0.1" />
              </linearGradient>
            </defs>

            <g transform={`translate(${margin.left}, ${margin.top})`}>
              {/* Grid */}
              {yTickValues.map((value, i) => (
                <line
                  key={`grid-${i}`}
                  x1={0}
                  y1={yScale(value)}
                  x2={chartWidth}
                  y2={yScale(value)}
                  stroke="url(#gridGradient)"
                  strokeWidth={0.5}
                  opacity={0.4}
                  strokeDasharray={i === Math.floor(yTickValues.length / 2) ? "none" : "2 4"}
                />
              ))}

              {/* Crosshair */}
              {mousePos && (
                <>
                  <line
                    x1={mousePos.x}
                    y1={0}
                    x2={mousePos.x}
                    y2={chartHeight}
                    stroke="#60A5FA"
                    strokeWidth={1.5}
                    strokeDasharray="4 4"
                    opacity={0.6}
                    filter="url(#glow)"
                  />
                  <line
                    x1={0}
                    y1={mousePos.y}
                    x2={chartWidth}
                    y2={mousePos.y}
                    stroke="#60A5FA"
                    strokeWidth={1.5}
                    strokeDasharray="4 4"
                    opacity={0.6}
                    filter="url(#glow)"
                  />
                  {/* Crosshair center point */}
                  <circle
                    cx={mousePos.x}
                    cy={mousePos.y}
                    r={4}
                    fill="#60A5FA"
                    opacity={0.8}
                    filter="url(#glow)"
                  />
                </>
              )}

              {/* Bollinger Bands (render first, behind candles) */}
              {renderBB()}

              {/* Chart */}
              {chartType === 'candlestick' && visibleData.map((candle, i) => renderCandle(candle, i))}
              {chartType === 'line' && renderLine()}
              {chartType === 'area' && renderArea()}

              {/* MA */}
              {showMA && ma7.length > 0 && renderMA(ma7, '#FBBF24', 1.5)}
              {showMA && ma20.length > 0 && renderMA(ma20, '#3B82F6', 2)}
              {showMA && ma50.length > 0 && renderMA(ma50, '#A855F7', 2)}

              {/* Axes */}
              {yTickValues.map((value, i) => (
                <text key={`y-${i}`} x={chartWidth + 10} y={yScale(value)} fill="#9CA3AF" fontSize="14" fontWeight="500" dominantBaseline="middle">${value.toFixed(0)}</text>
              ))}
              {[0, Math.floor(filteredData.length / 2), filteredData.length - 1].map((index) => {
                const candle = filteredData[index];
                if (!candle) return null;
                const time = new Date(candle.time * 1000).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
                return <text key={`x-${index}`} x={xScale(index)} y={chartHeight + 25} fill="#9CA3AF" fontSize="13" textAnchor="middle">{time}</text>;
              })}

              {/* RSI */}
              {renderRSI()}

              {/* Volume */}
              {renderVolume()}
            </g>
          </svg>
        </div>

        {/* Footer Stats */}
        <div className="relative z-10 mt-4 pt-4 border-t border-gray-700/50 flex flex-wrap justify-between items-center text-xs">
          <div className="flex gap-4 flex-wrap">
            <div className="px-3 py-1.5 bg-gray-800/40 border border-gray-700/30 rounded-lg backdrop-blur-sm">
              <span className="text-gray-500 mr-2">Périodes:</span>
              <span className="text-cyan-400 font-bold">{filteredData.length}</span>
            </div>
            <div className="px-3 py-1.5 bg-gray-800/40 border border-gray-700/30 rounded-lg backdrop-blur-sm">
              <span className="text-gray-500 mr-2">Min:</span>
              <span className="text-red-400 font-mono font-bold">${minPrice.toFixed(2)}</span>
            </div>
            <div className="px-3 py-1.5 bg-gray-800/40 border border-gray-700/30 rounded-lg backdrop-blur-sm">
              <span className="text-gray-500 mr-2">Max:</span>
              <span className="text-green-400 font-mono font-bold">${maxPrice.toFixed(2)}</span>
            </div>
            <div className="px-3 py-1.5 bg-gray-800/40 border border-gray-700/30 rounded-lg backdrop-blur-sm">
              <span className="text-gray-500 mr-2">Range:</span>
              <span className="text-blue-400 font-mono font-bold">${priceRange.toFixed(2)}</span>
            </div>
          </div>
          <div className="flex gap-4 items-center mt-2 md:mt-0">
            <div className="flex items-center gap-2 px-3 py-1.5 bg-green-500/10 border border-green-500/20 rounded-lg backdrop-blur-sm">
              <div className="w-2.5 h-2.5 rounded-full bg-green-500 shadow-lg shadow-green-500/50"></div>
              <span className="text-green-400 font-semibold">Hausse</span>
            </div>
            <div className="flex items-center gap-2 px-3 py-1.5 bg-red-500/10 border border-red-500/20 rounded-lg backdrop-blur-sm">
              <div className="w-2.5 h-2.5 rounded-full bg-red-500 shadow-lg shadow-red-500/50"></div>
              <span className="text-red-400 font-semibold">Baisse</span>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};
