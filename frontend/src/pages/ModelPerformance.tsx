import React, { useEffect, useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, PieChart, Pie, Legend,
} from 'recharts';
import { modelApi } from '../services/api';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { MOCK_MODEL } from '../utils/mockData';

const tooltipStyle = { backgroundColor:'#1a1a28', border:'1px solid #2a2a3d', fontSize:12, color:'#fff' };

export const ModelPerformance: React.FC = () => {
  const [active,    setActive]    = useState<Record<string,unknown> | null>(null);
  const [loading,   setLoading]   = useState(true);
  const [training,  setTraining]  = useState(false);
  const [message,   setMessage]   = useState('');
  const [usingMock, setUsingMock] = useState(false);

  const load = () => {
    setLoading(true);
    modelApi.active()
      .then(d => {
        if (d?.is_ready) {
          setActive(d);
          setUsingMock(false);
        } else {
          setActive({ is_ready:true, version: MOCK_MODEL.version, metadata: MOCK_MODEL });
          setUsingMock(true);
        }
      })
      .catch(() => {
        setActive({ is_ready:true, version: MOCK_MODEL.version, metadata: MOCK_MODEL });
        setUsingMock(true);
      })
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const triggerTrain = async () => {
    setTraining(true);
    setMessage('Training started. This may take 5–15 minutes…');
    await modelApi.train().catch(e => setMessage(`Error: ${e.message}`));
    setTimeout(() => { setTraining(false); load(); setMessage('Training complete. Model reloaded.'); }, 20_000);
  };

  const meta = (active?.metadata ?? active) as typeof MOCK_MODEL | null;

  // Feature importance chart data
  const topFeatures = meta?.feature_importances
    ? Object.entries(meta.feature_importances)
        .sort((a,b) => b[1]-a[1]).slice(0,15)
        .map(([name, importance]) => ({ name, importance: +(importance*100).toFixed(2) }))
    : [];

  // Prediction distribution pie
  const predDist = meta?.prediction_distribution
    ? [
        { name:'BUY',  value: meta.prediction_distribution['BUY']  ?? 0, fill:'#00d084' },
        { name:'SELL', value: meta.prediction_distribution['SELL'] ?? 0, fill:'#ff4d4d' },
        { name:'HOLD', value: meta.prediction_distribution['HOLD'] ?? 0, fill:'#8b8b9b' },
      ]
    : [];

  const InfoCard: React.FC<{label:string; value:string; highlight?:boolean}> = ({ label, value, highlight }) => (
    <div className="bg-bg-card border border-bg-border rounded-xl p-4">
      <div className="text-xs text-muted mb-1 uppercase tracking-wider">{label}</div>
      <div className={`font-mono font-bold text-lg ${highlight ? 'text-accent' : 'text-white'}`}>{value}</div>
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Model Performance</h1>
          <p className="text-muted text-sm mt-1">
            XGBoost prediction engine metrics and feature analysis
          </p>
        </div>
        <div className="flex gap-3">
          <button onClick={() => modelApi.reload().then(load)}
            className="px-4 py-2 bg-bg-card border border-bg-border text-sm rounded-lg hover:border-accent">
            ↺ Reload
          </button>
          <button onClick={triggerTrain} disabled={training}
            className="px-4 py-2 bg-accent hover:bg-accent/80 text-white rounded-lg text-sm font-semibold disabled:opacity-50">
            {training ? '⏳ Training…' : '⚡ Retrain Model'}
          </button>
        </div>
      </div>

      {message && (
        <div className="bg-accent/10 border border-accent/30 rounded-lg p-3 text-sm text-accent">{message}</div>
      )}

      {loading ? (
        <div className="flex justify-center py-24"><LoadingSpinner size={40} /></div>
      ) : (
        <>
          {/* Model info cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <InfoCard label="Algorithm"       value={meta?.model_name ?? 'XGBoost'} highlight />
            <InfoCard label="Version"         value={String(active?.version ?? '—')} />
            <InfoCard label="Training Samples"value={(meta?.training_samples ?? 0).toLocaleString()} />
            <InfoCard label="Trained At"      value={meta?.trained_at ? new Date(meta.trained_at).toLocaleDateString('en-IN') : '—'} />
          </div>

          {/* Accuracy cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label:'Validation Accuracy', value: meta?.val_accuracy,  color:'text-signal-buy' },
              { label:'Test Accuracy',       value: meta?.test_accuracy, color:'text-signal-buy' },
              { label:'Validation F1',       value: meta?.val_f1,        color:'text-accent'     },
              { label:'Test F1',             value: meta?.test_f1,       color:'text-accent'     },
            ].map(({ label, value, color }) => (
              <div key={label} className="bg-bg-card border border-bg-border rounded-xl p-5 text-center">
                <div className="text-xs text-muted mb-2 uppercase tracking-wider">{label}</div>
                <div className={`text-3xl font-bold font-mono ${color}`}>
                  {value ? `${(value*100).toFixed(1)}%` : '—'}
                </div>
                <div className="mt-3 h-1.5 bg-bg-border rounded-full overflow-hidden">
                  <div className="h-full bg-current rounded-full transition-all" style={{ width:`${(value??0)*100}%`, color: color.replace('text-','') }} />
                </div>
              </div>
            ))}
          </div>

          {/* Two-column: distribution + feature importance */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Prediction distribution pie */}
            {predDist.length > 0 && (
              <div className="bg-bg-card border border-bg-border rounded-xl p-5">
                <h2 className="text-sm font-semibold text-muted uppercase tracking-wider mb-4">Test Prediction Distribution</h2>
                <ResponsiveContainer width="100%" height={220}>
                  <PieChart>
                    <Pie data={predDist} dataKey="value" nameKey="name" cx="50%" cy="50%"
                      outerRadius={80} label={({ name, percent }) => `${name} ${(percent*100).toFixed(0)}%`}
                      labelLine={false}>
                      {predDist.map((e,i) => <Cell key={i} fill={e.fill} />)}
                    </Pie>
                    <Legend formatter={(v) => <span style={{ color:'#8b8b9b', fontSize:12 }}>{v}</span>} />
                    <Tooltip contentStyle={tooltipStyle} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Top 8 features */}
            {topFeatures.length > 0 && (
              <div className="bg-bg-card border border-bg-border rounded-xl p-5">
                <h2 className="text-sm font-semibold text-muted uppercase tracking-wider mb-4">Top 8 Feature Importances (%)</h2>
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={topFeatures.slice(0,8)} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" stroke="#2a2a3d" horizontal={false} />
                    <XAxis type="number" stroke="#5a5a7a" tick={{ fontSize:10 }} />
                    <YAxis type="category" dataKey="name" stroke="#5a5a7a" tick={{ fontSize:11 }} width={90} />
                    <Tooltip contentStyle={tooltipStyle} formatter={(v:number) => [`${v}%`, 'Importance']} />
                    <Bar dataKey="importance" fill="#6c63ff" radius={[0,4,4,0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>

          {/* Full feature importance */}
          {topFeatures.length > 0 && (
            <div className="bg-bg-card border border-bg-border rounded-xl p-5">
              <h2 className="text-sm font-semibold text-muted uppercase tracking-wider mb-4">All Feature Importances (%)</h2>
              <ResponsiveContainer width="100%" height={340}>
                <BarChart data={topFeatures} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#2a2a3d" horizontal={false} />
                  <XAxis type="number" stroke="#5a5a7a" tick={{ fontSize:10 }} />
                  <YAxis type="category" dataKey="name" stroke="#5a5a7a" tick={{ fontSize:11 }} width={110} />
                  <Tooltip contentStyle={tooltipStyle} formatter={(v:number) => [`${v}%`, 'Importance']} />
                  <Bar dataKey="importance" fill="#6c63ff" radius={[0,4,4,0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Features list */}
          {meta?.features && (
            <div className="bg-bg-card border border-bg-border rounded-xl p-5">
              <h2 className="text-sm font-semibold text-muted uppercase tracking-wider mb-4">
                Feature Set ({meta.features.length} features)
              </h2>
              <div className="flex flex-wrap gap-2">
                {meta.features.map((f:string) => (
                  <span key={f} className="text-xs font-mono bg-bg-border text-muted px-2 py-1 rounded">{f}</span>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};
