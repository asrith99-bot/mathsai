import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Provider } from 'react-redux';
import { store } from './store/store';
import { Layout }          from './components/layout/Layout';
import { Dashboard }       from './pages/Dashboard';
import { Scanner }         from './pages/Scanner';
import { StockDetail }     from './pages/StockDetail';
import { SignalCenter }    from './pages/SignalCenter';
import { Backtesting }     from './pages/Backtesting';
import { ModelPerformance } from './pages/ModelPerformance';
import { useWebSocket }    from './hooks/useWebSocket';

// Inner component so hooks can access the Redux store
const AppInner: React.FC = () => {
  useWebSocket();  // Connect WS once at app root
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/"             element={<Dashboard />}        />
        <Route path="/scanner"      element={<Scanner />}          />
        <Route path="/stock/:symbol" element={<StockDetail />}     />
        <Route path="/signals"      element={<SignalCenter />}     />
        <Route path="/backtest"     element={<Backtesting />}      />
        <Route path="/model"        element={<ModelPerformance />} />
      </Route>
    </Routes>
  );
};

const App: React.FC = () => (
  <Provider store={store}>
    <BrowserRouter>
      <AppInner />
    </BrowserRouter>
  </Provider>
);

export default App;
