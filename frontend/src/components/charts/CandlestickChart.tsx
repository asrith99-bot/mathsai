/**
 * TradingView Lightweight Charts candlestick chart.
 * Renders OHLCV candles, volume, and optional signal lines.
 */
import React, { useEffect, useRef } from 'react';
import { createChart, ColorType, CrosshairMode } from 'lightweight-charts';
import type { OHLCVBar, Signal } from '../../types';

interface Props {
  ohlcv: OHLCVBar[];
  signals?: Signal[];
  height?: number;
}

export const CandlestickChart: React.FC<Props> = ({ ohlcv, signals = [], height = 420 }) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current || ohlcv.length === 0) return;

    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#1a1a28' },
        textColor: '#8b8b9b',
      },
      grid: {
        vertLines: { color: '#2a2a3d' },
        horzLines: { color: '#2a2a3d' },
      },
      crosshair: { mode: CrosshairMode.Normal },
      rightPriceScale: { borderColor: '#2a2a3d' },
      timeScale: {
        borderColor: '#2a2a3d',
        timeVisible: true,
        secondsVisible: false,
      },
      width: containerRef.current.clientWidth,
      height,
    });

    // Candlestick series
    const candleSeries = chart.addCandlestickSeries({
      upColor:   '#00d084',
      downColor: '#ff4d4d',
      borderUpColor:   '#00d084',
      borderDownColor: '#ff4d4d',
      wickUpColor:   '#00d084',
      wickDownColor: '#ff4d4d',
    });

    const candles = ohlcv.map(bar => ({
      time: (new Date(bar.timestamp).getTime() / 1000) as unknown as string,
      open:  bar.open,
      high:  bar.high,
      low:   bar.low,
      close: bar.close,
    }));
    candleSeries.setData(candles as never[]);

    // Volume series
    const volumeSeries = chart.addHistogramSeries({
      color: '#6c63ff',
      priceFormat: { type: 'volume' },
      priceScaleId: 'volume',
    });
    chart.priceScale('volume').applyOptions({
      scaleMargins: { top: 0.85, bottom: 0 },
    });
    const volumes = ohlcv.map(bar => ({
      time: (new Date(bar.timestamp).getTime() / 1000) as unknown as string,
      value: bar.volume,
      color: bar.close >= bar.open ? '#00d08440' : '#ff4d4d40',
    }));
    volumeSeries.setData(volumes as never[]);

    // Signal markers
    if (signals.length > 0) {
      const markers = signals
        .filter(s => s.signal_type !== 'HOLD')
        .map(s => ({
          time: (new Date(s.generated_at).getTime() / 1000) as unknown as string,
          position: s.signal_type === 'BUY' ? 'belowBar' : 'aboveBar',
          color: s.signal_type === 'BUY' ? '#00d084' : '#ff4d4d',
          shape: s.signal_type === 'BUY' ? 'arrowUp' : 'arrowDown',
          text: `${s.signal_type} ${(s.confidence * 100).toFixed(0)}%`,
        }));
      candleSeries.setMarkers(markers as never[]);
    }

    chart.timeScale().fitContent();

    // Responsive resize
    const observer = new ResizeObserver(() => {
      chart.applyOptions({ width: containerRef.current?.clientWidth ?? 600 });
    });
    if (containerRef.current) observer.observe(containerRef.current);

    return () => {
      observer.disconnect();
      chart.remove();
    };
  }, [ohlcv, signals, height]);

  return (
    <div
      ref={containerRef}
      className="w-full rounded-xl overflow-hidden border border-bg-border"
      style={{ height }}
    />
  );
};
