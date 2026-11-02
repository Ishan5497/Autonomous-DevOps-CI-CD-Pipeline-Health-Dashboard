import { useState, useEffect, useRef, useCallback } from 'react';

/**
 * Custom React hook that maintains a persistent WebSocket connection to
 * the FastAPI real-time telemetry stream. Automatically reconnects on
 * disconnect, processes typed events, and exposes live activity logs +
 * metric state for the dashboard.
 */
export default function useWebSocket({ maxLogEntries = 200 } = {}) {
  const [isConnected, setIsConnected] = useState(false);
  const [metrics, setMetrics] = useState(null);
  const [activityLog, setActivityLog] = useState([]);
  const wsRef = useRef(null);
  const reconnectTimerRef = useRef(null);
  const heartbeatTimerRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);

  // Derive the WebSocket URL from the current page origin or environment variable
  const getWsUrl = useCallback(() => {
    if (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_WS_URL) {
      return import.meta.env.VITE_WS_URL;
    }
    if (typeof window !== 'undefined' && window.location && window.location.host) {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      return `${protocol}//${host}/api/v1/ws`;
    }
    return 'ws://127.0.0.1:8000/api/v1/ws';
  }, []);

  // Append a log entry, capping at maxLogEntries
  const appendLog = useCallback(
    (entry) => {
      setActivityLog((prev) => {
        const next = [entry, ...prev];
        return next.length > maxLogEntries ? next.slice(0, maxLogEntries) : next;
      });
    },
    [maxLogEntries]
  );

  // Format incoming WebSocket messages into log entries
  const processMessage = useCallback(
    (event) => {
      try {
        const msg = JSON.parse(event.data);

        // Update metrics whenever they arrive in any event
        if (msg.metrics) {
          setMetrics(msg.metrics);
        }

        const timestamp = msg.timestamp || new Date().toISOString();

        switch (msg.type) {
          case 'CONNECTION_ESTABLISHED':
            appendLog({
              id: `conn-${Date.now()}`,
              type: 'CONNECTION',
              severity: 'info',
              title: 'WebSocket Connected',
              message: msg.message || 'Real-time telemetry stream established',
              timestamp,
            });
            break;

          case 'PIPELINE_UPDATE':
            appendLog({
              id: `pipe-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
              type: 'PIPELINE_UPDATE',
              severity: msg.data?.status === 'success' ? 'success' : 'info',
              title: `Pipeline ${msg.data?.pipeline_id || 'unknown'}`,
              message: `${msg.data?.status?.toUpperCase()} — ${msg.data?.commit_message || 'Pipeline run'} (${msg.data?.branch || 'main'})`,
              author: msg.data?.author,
              repository: msg.data?.repository,
              data: msg.data,
              timestamp,
            });
            break;

          case 'BUILD_FAILURE':
            appendLog({
              id: `fail-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
              type: 'BUILD_FAILURE',
              severity: 'error',
              title: `Build Failed: ${msg.data?.pipeline_id || 'unknown'}`,
              message: msg.data?.failure_reason || `Build failed on ${msg.data?.branch || 'main'}`,
              author: msg.data?.author,
              repository: msg.data?.repository,
              data: msg.data,
              timestamp,
            });
            break;

          case 'SECURITY_ALERT':
            appendLog({
              id: `sec-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
              type: 'SECURITY_ALERT',
              severity: 'critical',
              title: `Security Alert — ${msg.data?.findings_count || 0} finding(s)`,
              message: `${msg.data?.critical_count || 0} CRITICAL, ${msg.data?.high_count || 0} HIGH in ${msg.data?.repository || 'repo'} @ ${(msg.data?.commit_sha || '').substring(0, 7)}`,
              repository: msg.data?.repository,
              data: msg.data,
              timestamp,
            });
            break;

          case 'METRICS_UPDATE':
            // Metrics-only update, no log entry needed
            break;

          case 'PONG':
            break;

          default:
            appendLog({
              id: `evt-${Date.now()}`,
              type: msg.type || 'UNKNOWN',
              severity: 'info',
              title: msg.type || 'Event',
              message: JSON.stringify(msg.data || msg).substring(0, 200),
              timestamp,
            });
        }
      } catch {
        // Non-JSON message (e.g. "pong")
      }
    },
    [appendLog]
  );

  // Connect / reconnect logic
  const connect = useCallback(() => {
    if (typeof WebSocket === 'undefined') {
      return;
    }
    // Don't reconnect if already open or connecting
    if (
      wsRef.current &&
      (wsRef.current.readyState === WebSocket.OPEN ||
        wsRef.current.readyState === WebSocket.CONNECTING)
    ) {
      return;
    }

    try {
      const ws = new WebSocket(getWsUrl());
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        reconnectAttemptsRef.current = 0;

        // Start heartbeat pings every 25 seconds
        if (heartbeatTimerRef.current) clearInterval(heartbeatTimerRef.current);
        heartbeatTimerRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send('ping');
          }
        }, 25_000);
      };

      ws.onmessage = processMessage;

      ws.onclose = () => {
        setIsConnected(false);
        if (heartbeatTimerRef.current) clearInterval(heartbeatTimerRef.current);

        // Exponential backoff reconnect (max 15s)
        const delay = Math.min(1000 * 2 ** reconnectAttemptsRef.current, 15_000);
        reconnectAttemptsRef.current += 1;
        reconnectTimerRef.current = setTimeout(connect, delay);
      };

      ws.onerror = () => {
        // onclose will fire after onerror, triggering reconnect
      };
    } catch {
      // Schedule a retry
      const delay = Math.min(1000 * 2 ** reconnectAttemptsRef.current, 15_000);
      reconnectAttemptsRef.current += 1;
      reconnectTimerRef.current = setTimeout(connect, delay);
    }
  }, [getWsUrl, processMessage]);

  // Manually request fresh metrics from the server
  const requestMetrics = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: 'get_metrics' }));
    }
  }, []);

  // Clear the activity log
  const clearLog = useCallback(() => {
    setActivityLog([]);
  }, []);

  // Lifecycle: connect on mount, cleanup on unmount
  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      if (heartbeatTimerRef.current) clearInterval(heartbeatTimerRef.current);
      if (wsRef.current) {
        wsRef.current.onclose = null; // prevent reconnect on intentional close
        wsRef.current.close();
      }
    };
  }, [connect]);

  return {
    isConnected,
    metrics,
    activityLog,
    requestMetrics,
    clearLog,
  };
}

