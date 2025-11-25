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

  // Mouse move handler
  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!svgRef.current) return;
    const rect = svgRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left - margin.left;
    const y = e.clientY - rect.top - margin.top;

    if (x >= 0 && x <= chartWidth && y >= 0 && y <= chartHeight) {
      setMousePos({ x, y });
      const index = Math.round((x / chartWidth) * (filteredData.length - 1));
      setHoveredIndex(Math.max(0, Math.min(index, filteredData.length - 1)));
    } else {
      setMousePos(null);
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

    const bodyTop = Math.min(openY, closeY);
    const bodyBottom = Math.max(openY, closeY);
    const bodyHeight = Math.max(Math.abs(bodyBottom - bodyTop), 1);

    return (
      <g key={`candle-${actualIndex}`}>
        <line x1={x} y1={highY} x2={x} y2={lowY} stroke={color} strokeWidth={Math.max(2, zoomLevel)} opacity={0.8} />
        <rect
          x={x - candleWidth / 2}
          y={bodyTop}
          width={candleWidth}
          height={bodyHeight}
          fill={color}
          stroke={color}
          strokeWidth={1}
          rx={1}
          opacity={hoveredIndex === actualIndex ? 1 : 0.9}
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
  const renderMA = (maData: (number | null)[], color: string, width: number) => {
    const points = maData
      .map((value, i) => value !== null ? `${xScale(i)},${yScale(value)}` : null)
      .filter(p => p !== null)
      .join(' ');
    return <polyline points={points} fill="none" stroke={color} strokeWidth={width} opacity={0.7} />;
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
    <div className="w-full bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 rounded-2xl border border-gray-700 p-6 shadow-2xl">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <BarChart3 className="w-6 h-6 text-blue-400" />
            <h3 className="text-xl font-bold text-white">Analyse Technique</h3>
            <div className="flex items-center gap-2 px-2 py-1 bg-green-900/30 rounded-lg">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-xs text-green-400">Live</span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-3xl font-bold text-white">${currentPrice.toFixed(2)}</span>
            <div className={`flex items-center gap-1 px-3 py-1 rounded-lg ${priceChange >= 0 ? 'bg-green-900/30 text-green-400' : 'bg-red-900/30 text-red-400'}`}>
              {priceChange >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
              <span className="font-bold">{priceChange >= 0 ? '+' : ''}{priceChangePercent}%</span>
            </div>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Dernière mise à jour: {lastUpdate.toLocaleTimeString('fr-FR')}
          </p>
        </div>

        {/* Controls */}
        <div className="flex flex-wrap gap-2">
          {/* Chart Type */}
          <div className="flex gap-1 bg-gray-800 p-1 rounded-lg border border-gray-700">
            <button onClick={() => setChartType('candlestick')} className={`p-2 rounded transition ${chartType === 'candlestick' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white hover:bg-gray-700'}`} title="Bougies">
              <CandlestickChart className="w-4 h-4" />
            </button>
            <button onClick={() => setChartType('line')} className={`p-2 rounded transition ${chartType === 'line' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white hover:bg-gray-700'}`} title="Ligne">
              <LineChartIcon className="w-4 h-4" />
            </button>
            <button onClick={() => setChartType('area')} className={`p-2 rounded transition ${chartType === 'area' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white hover:bg-gray-700'}`} title="Zone">
              <AreaChartIcon className="w-4 h-4" />
            </button>
          </div>

          {/* Timeframe */}
          <div className="flex gap-1 bg-gray-800 p-1 rounded-lg border border-gray-700">
            {(['15m', '1h', '4h', '1d', '1w'] as const).map((tf) => (
              <button key={tf} onClick={() => onTimeframeChange(tf)} className={`px-2 py-1 rounded text-xs font-semibold transition ${timeframe === tf ? 'bg-green-600 text-white' : 'text-gray-400 hover:text-white'}`}>
                {tf.toUpperCase()}
              </button>
            ))}
          </div>

          {/* Indicators */}
          <button onClick={() => setShowMA(!showMA)} className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${showMA ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400 hover:text-white'}`}>MA</button>
          <button onClick={() => setShowBB(!showBB)} className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${showBB ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400 hover:text-white'}`}>BB</button>
          <button onClick={() => setShowVolume(!showVolume)} className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${showVolume ? 'bg-purple-600 text-white' : 'bg-gray-800 text-gray-400 hover:text-white'}`}>VOL</button>
          <button onClick={() => setShowRSI(!showRSI)} className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${showRSI ? 'bg-purple-600 text-white' : 'bg-gray-800 text-gray-400 hover:text-white'}`}>RSI</button>

          {/* Zoom Controls */}
          <div className="flex gap-1 bg-gray-800 p-1 rounded-lg border border-gray-700">
            <button onClick={handleZoomOut} className="p-1 text-gray-400 hover:text-white transition" title="Zoom Out">
              <ZoomOut className="w-4 h-4" />
            </button>
            <button onClick={handleResetZoom} className="px-2 text-xs text-gray-400 hover:text-white transition" title="Reset Zoom">
              {(zoomLevel * 100).toFixed(0)}%
            </button>
            <button onClick={handleZoomIn} className="p-1 text-gray-400 hover:text-white transition" title="Zoom In">
              <ZoomIn className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-4 mb-3 text-xs">
        {showMA && (
          <>
            <div className="flex items-center gap-2"><div className="w-4 h-0.5 bg-yellow-400"></div><span className="text-gray-400">MA7</span></div>
            <div className="flex items-center gap-2"><div className="w-4 h-0.5 bg-blue-400"></div><span className="text-gray-400">MA20</span></div>
            <div className="flex items-center gap-2"><div className="w-4 h-0.5 bg-purple-400"></div><span className="text-gray-400">MA50</span></div>
          </>
        )}
        {showBB && <div className="flex items-center gap-2"><div className="w-4 h-2 bg-blue-400 opacity-20 border border-blue-400"></div><span className="text-gray-400">BB(20,2)</span></div>}
        {showVolume && <div className="flex items-center gap-2"><div className="w-3 h-3 bg-purple-500 opacity-40"></div><span className="text-gray-400">Volume</span></div>}
        {showRSI && <div className="flex items-center gap-2"><div className="w-4 h-0.5 bg-purple-400"></div><span className="text-gray-400">RSI(14)</span></div>}
        <div className="flex items-center gap-2 ml-auto">
          <div className="w-2 h-2 rounded-full bg-green-500"></div>
          <span className="text-gray-400 font-semibold">{timeframeConfig.label}</span>
          <span className="text-gray-500">•</span>
          <span className="text-gray-400">{filteredData.length} bougies</span>
        </div>
      </div>

      {/* Tooltip */}
      {hoveredCandle && (
        <div className="mb-3 p-3 bg-gray-800/95 border border-gray-700 rounded-lg backdrop-blur-sm">
          <div className="grid grid-cols-2 md:grid-cols-6 gap-3 text-xs">
            <div><span className="text-gray-400">O:</span><span className="ml-1 text-white font-mono">${hoveredCandle.open.toFixed(2)}</span></div>
            <div><span className="text-gray-400">H:</span><span className="ml-1 text-green-400 font-mono">${hoveredCandle.high.toFixed(2)}</span></div>
            <div><span className="text-gray-400">L:</span><span className="ml-1 text-red-400 font-mono">${hoveredCandle.low.toFixed(2)}</span></div>
            <div><span className="text-gray-400">C:</span><span className="ml-1 text-white font-mono font-bold">${hoveredCandle.close.toFixed(2)}</span></div>
            <div><span className="text-gray-400">Δ:</span><span className={`ml-1 font-mono font-bold ${hoveredCandle.close >= hoveredCandle.open ? 'text-green-400' : 'text-red-400'}`}>{((hoveredCandle.close - hoveredCandle.open) / hoveredCandle.open * 100).toFixed(2)}%</span></div>
            {hoveredRSI !== null && typeof hoveredRSI === 'number' && <div><span className="text-gray-400">RSI:</span><span className="ml-1 text-purple-400 font-mono">{hoveredRSI.toFixed(1)}</span></div>}
          </div>
        </div>
      )}

      {/* Chart */}
      <div className="w-full overflow-x-auto bg-gray-900/50 rounded-lg p-2">
        <svg ref={svgRef} viewBox={`0 0 ${width} ${totalHeight}`} className="w-full h-auto" onMouseMove={handleMouseMove} onMouseLeave={() => { setMousePos(null); setHoveredIndex(null); }} onWheel={handleWheel}>
          <defs>
            <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#3B82F6" stopOpacity="0.8" />
              <stop offset="100%" stopColor="#3B82F6" stopOpacity="0.05" />
            </linearGradient>
          </defs>

          <g transform={`translate(${margin.left}, ${margin.top})`}>
            {/* Grid */}
            {yTickValues.map((value, i) => (
              <line key={`grid-${i}`} x1={0} y1={yScale(value)} x2={chartWidth} y2={yScale(value)} stroke="#374151" strokeWidth={0.5} opacity={0.3} />
            ))}

            {/* Crosshair */}
            {mousePos && (
              <>
                <line x1={mousePos.x} y1={0} x2={mousePos.x} y2={chartHeight} stroke="#6B7280" strokeWidth={1} strokeDasharray="4 4" opacity={0.5} />
                <line x1={0} y1={mousePos.y} x2={chartWidth} y2={mousePos.y} stroke="#6B7280" strokeWidth={1} strokeDasharray="4 4" opacity={0.5} />
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
      <div className="mt-3 pt-3 border-t border-gray-700 flex flex-wrap justify-between items-center text-xs text-gray-400">
        <div className="flex gap-3">
          <span>{filteredData.length} périodes</span><span>•</span>
          <span>Min: ${minPrice.toFixed(2)}</span><span>•</span>
          <span>Max: ${maxPrice.toFixed(2)}</span><span>•</span>
          <span>Range: ${priceRange.toFixed(2)}</span>
        </div>
        <div className="flex gap-2 items-center">
          <div className="w-2 h-2 rounded-full bg-green-500"></div><span>Hausse</span>
          <div className="w-2 h-2 rounded-full bg-red-500 ml-2"></div><span>Baisse</span>
        </div>
      </div>
    </div>
  );
};
