import { useState, useEffect, useCallback } from 'react';
import './App.css';

import Sidebar from './components/Sidebar';
import Header from './components/Header';
import MetricsCards from './components/MetricsCards';
import StatusTable from './components/StatusTable';
import HealthVisualizer from './components/HealthVisualizer';
import WebhookSimulator from './components/WebhookSimulator';
import StaticDiffScanner from './components/StaticDiffScanner';
import LiveActivityLog from './components/LiveActivityLog';
import useWebSocket from './hooks/useWebSocket';
import { api } from './services/api';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  // Dashboard data loaded via REST API
  const [dashboardData, setDashboardData] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isSeeding, setIsSeeding] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [recommendations, setRecommendations] = useState([]);

  // Real-time WebSocket connection
  const { isConnected, metrics: wsMetrics, activityLog, requestMetrics, clearLog } =
    useWebSocket({ maxLogEntries: 250 });

  // Use WS metrics if available, otherwise fall back to REST data
  const health = wsMetrics || dashboardData?.health || {};
  const runs = dashboardData?.recent_runs || [];
  const pullRequests = dashboardData?.recent_pull_requests || [];
  const findings = dashboardData?.recent_findings || [];

  // Fetch full dashboard data from REST API
  const fetchDashboard = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const summary = await api.getDashboardSummary();
      setDashboardData(summary);
      setLastUpdated(new Date());

      // Fetch recommendations separately for the AI Guardrails tab
      try {
        const healthData = await api.getPipelineHealth();
        setRecommendations(healthData.recommendations || []);
      } catch {
        // non-critical
      }
    } catch (err) {
      console.error('Failed to fetch dashboard:', err);
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  // Seed demo data
  const handleSeedData = useCallback(async () => {
    setIsSeeding(true);
    try {
      await api.seedDemoData();
      await fetchDashboard();
      requestMetrics();
    } catch (err) {
      console.error('Seed failed:', err);
    } finally {
      setIsSeeding(false);
    }
  }, [fetchDashboard, requestMetrics]);

  // After a webhook simulation, refresh REST data and request fresh WS metrics
  const handleEventSent = useCallback(() => {
    fetchDashboard();
    requestMetrics();
  }, [fetchDashboard, requestMetrics]);

  // Initial load
  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  // Render tab content
  const renderTabContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return (
          <div className="space-y-5">
            <MetricsCards
              health={health}
              runs={runs}
              pullRequests={pullRequests}
            />
            <HealthVisualizer health={health} runs={runs} />
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
              <LiveActivityLog
                activityLog={activityLog}
                isConnected={isConnected}
                onClearLog={clearLog}
              />
              <StatusTable runs={runs} />
            </div>
          </div>
        );

      case 'pipelines':
        return (
          <div className="space-y-5">
            <StatusTable runs={runs} />
            <LiveActivityLog
              activityLog={activityLog.filter(
                (e) =>
                  e.type === 'PIPELINE_UPDATE' || e.type === 'BUILD_FAILURE'
              )}
              isConnected={isConnected}
              onClearLog={clearLog}
            />
          </div>
        );

      case 'scanner':
        return <StaticDiffScanner onScanComplete={handleEventSent} />;

      case 'simulator':
        return <WebhookSimulator onEventSent={handleEventSent} />;

      case 'recommendations':
        return (
          <div className="space-y-3">
            <div className="glass-panel rounded-2xl p-5">
              <h3 className="text-sm font-semibold text-slate-100 mb-4 flex items-center gap-2">
                <span className="w-4 h-4 text-cyan-400">✨</span>
                Autonomous AI Guardrails & Recommendations
              </h3>
              {recommendations.length === 0 ? (
                <p className="text-xs text-slate-400 font-mono">
                  No recommendations at this time. System is healthy.
                </p>
              ) : (
                <div className="space-y-2.5">
                  {recommendations.map((rec) => (
                    <div
                      key={rec.id}
                      className={`rounded-xl p-3.5 border text-xs space-y-1.5 ${
                        rec.priority === 'HIGH'
                          ? 'bg-rose-950/20 border-rose-500/40'
                          : rec.priority === 'MEDIUM'
                          ? 'bg-amber-950/20 border-amber-500/40'
                          : 'bg-slate-900/60 border-slate-700/60'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-slate-200">
                          {rec.title}
                        </span>
                        <span
                          className={`px-2 py-0.5 rounded font-mono text-[10px] font-bold ${
                            rec.priority === 'HIGH'
                              ? 'bg-rose-500 text-slate-950'
                              : rec.priority === 'MEDIUM'
                              ? 'bg-amber-500 text-slate-950'
                              : 'bg-slate-700 text-slate-200'
                          }`}
                        >
                          {rec.priority}
                        </span>
                      </div>
                      <p className="text-slate-300">{rec.message}</p>
                      <div className="text-[11px] text-cyan-300/90 font-mono bg-cyan-950/30 p-2 rounded border border-cyan-500/20">
                        <strong>Suggested Action:</strong>{' '}
                        {rec.suggested_action}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="flex min-h-screen bg-[#070b14]">
      {/* Desktop Sidebar */}
      <div className="hidden lg:block">
        <Sidebar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          systemStatus={{}}
        />
      </div>

      {/* Mobile Sidebar Overlay */}
      {mobileSidebarOpen && (
        <div className="lg:hidden fixed inset-0 z-40 flex">
          <div
            className="fixed inset-0 bg-black/50"
            onClick={() => setMobileSidebarOpen(false)}
          />
          <div className="relative z-50">
            <Sidebar
              activeTab={activeTab}
              setActiveTab={(tab) => {
                setActiveTab(tab);
                setMobileSidebarOpen(false);
              }}
              systemStatus={{}}
            />
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        <Header
          onRefresh={fetchDashboard}
          onSeedData={handleSeedData}
          isRefreshing={isRefreshing}
          isSeeding={isSeeding}
          lastUpdated={lastUpdated}
          onToggleMobileSidebar={() => setMobileSidebarOpen(!mobileSidebarOpen)}
        />

        <main className="flex-1 p-5 lg:p-6 overflow-y-auto">
          {renderTabContent()}
        </main>
      </div>
    </div>
  );
}

export default App;
