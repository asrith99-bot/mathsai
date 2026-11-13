/**
 * RSI and MACD indicator panels using Recharts.
 */
import React from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine, BarChart, Bar,
} from 'recharts';
import type { OHLCVBar } from '../../types';

interface Props {
  data: Array<OHLCVBar & { rsi?: number; macd?: number; macd_signal?: number; macd_hist?: number }>;
}

const tooltipStyle = {
  backgroundColor: '#1a1a28',
  border: '1px solid #2a2a3d',
  color: '#fff',
  fontSize: 12,
};

export const IndicatorChart: React.FC<Props> = ({ data }) => {
  const slice = data.slice(-100);
  const labels = slice.map(d => {
    const ts = new Date(d.timestamp);
    return `${ts.getHours()}:${String(ts.getMinutes()).padStart(2, '0')}`;
  });

  const rsiData = slice.map((d, i) => ({ t: labels[i], rsi: d.rsi }));
  const macdData = slice.map((d, i) => ({
    t: labels[i],
    macd: d.macd,
    signal: d.macd_signal,
    hist: d.macd_hist,
  }));

  return (
    <div className="flex flex-col gap-4">
      {/* RSI */}
      <div className="bg-bg-card border border-bg-border rounded-xl p-4">
        <div className="text-xs text-muted mb-3 uppercase tracking-wider">RSI (14)</div>
        <ResponsiveContainer width="100%" height={120}>
          <LineChart data={rsiData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2a2a3d" />
            <XAxis dataKey="t" stroke="#5a5a7a" tick={{ fontSize: 10 }} interval="preserveStartEnd" />
            <YAxis domain={[0, 100]} stroke="#5a5a7a" tick={{ fontSize: 10 }} width={30} />
            <Tooltip contentStyle={tooltipStyle} />
            <ReferenceLine y={70} stroke="#ff4d4d" strokeDasharray="4 2" />
            <ReferenceLine y={30} stroke="#00d084" strokeDasharray="4 2" />
            <ReferenceLine y={50} stroke="#2a2a3d" />
            <Line type="monotone" dataKey="rsi" stroke="#6c63ff" dot={false} strokeWidth={1.5} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* MACD */}
      <div className="bg-bg-card border border-bg-border rounded-xl p-4">
        <div className="text-xs text-muted mb-3 uppercase tracking-wider">MACD (12,26,9)</div>
        <ResponsiveContainer width="100%" height={120}>
          <BarChart data={macdData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2a2a3d" />
            <XAxis dataKey="t" stroke="#5a5a7a" tick={{ fontSize: 10 }} interval="preserveStartEnd" />
            <YAxis stroke="#5a5a7a" tick={{ fontSize: 10 }} width={40} />
            <Tooltip contentStyle={tooltipStyle} />
            <ReferenceLine y={0} stroke="#2a2a3d" />
            <Bar dataKey="hist" fill="#6c63ff" opacity={0.7} />
            <Line type="monotone" dataKey="macd"   stroke="#00d084" dot={false} />
            <Line type="monotone" dataKey="signal" stroke="#ff4d4d" dot={false} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
