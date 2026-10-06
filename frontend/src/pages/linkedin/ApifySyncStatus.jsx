/**
 * ApifySyncStatus — Admin Sync Status section for the LinkedIn Admin Dashboard.
 *
 * Shows:
 *  - Last sync timestamp & status
 *  - Real live counts (fetched, new, duplicates, classified, review_required, errors)
 *  - Last checkpoint
 *  - "Run Update Now" button (triggers manual sync via POST /api/admin/apify/sync)
 *  - Running state with animated indicator
 *
 * Security: API token is NEVER included in any request or response.
 * All counts come from the database via /api/admin/apify/status.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { adminApi } from "../../services/api";

function fmt(val) {
  if (val === null || val === undefined) return "—";
  return Number(val).toLocaleString();
}

function fmtDate(iso) {
  if (!iso) return "Never";
  try {
    return new Date(iso + "Z").toLocaleString("en-IN", {
      day: "2-digit", month: "short", year: "numeric",
      hour: "2-digit", minute: "2-digit", hour12: true,
    });
  } catch {
    return iso;
  }
}

function StatusBadge({ isRunning, lastStatus }) {
  if (isRunning) {
    return (
      <span className="sync-badge running">
        <span className="sync-running-dot" />
        Running…
      </span>
    );
  }
  if (lastStatus === "failed") return <span className="sync-badge error">Last run failed</span>;
  if (lastStatus === "partial") return <span className="sync-badge error">Last run partial</span>;
  return <span className="sync-badge idle">Idle</span>;
}

const POLL_INTERVAL_MS = 5000; // poll every 5 s while a sync is running

export default function ApifySyncStatus() {
  const [status, setStatus]     = useState(null);
  const [loading, setLoading]   = useState(true);
  const [syncing, setSyncing]   = useState(false);
  const [error, setError]       = useState("");
  const [syncResult, setSyncResult] = useState(null);
  const pollRef = useRef(null);

  const fetchStatus = useCallback(() => {
    adminApi.get("/api/admin/apify/status")
      .then((data) => {
        setStatus(data);
        setLoading(false);
        // If a sync is running, keep polling; otherwise stop
        if (!data.is_running) {
          clearInterval(pollRef.current);
          pollRef.current = null;
        }
      })
      .catch(() => {
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    fetchStatus();
    return () => clearInterval(pollRef.current);
  }, [fetchStatus]);

  // Start polling while a sync is running
  useEffect(() => {
    if (status?.is_running && !pollRef.current) {
      pollRef.current = setInterval(fetchStatus, POLL_INTERVAL_MS);
    }
  }, [status, fetchStatus]);

  async function handleRunNow() {
    if (syncing) return;
    setSyncing(true);
    setError("");
    setSyncResult(null);
    try {
      const result = await adminApi.post("/api/admin/apify/sync", { mock: "false" });
      setSyncResult(result);
      fetchStatus();
    } catch (err) {
      if (err.message?.includes("already running")) {
        setError("A sync is already running. Please wait for it to complete.");
      } else {
        setError(err.message || "Sync failed. Check server logs.");
      }
      fetchStatus();
    } finally {
      setSyncing(false);
    }
  }

  async function handleRunMock() {
    if (syncing) return;
    setSyncing(true);
    setError("");
    setSyncResult(null);
    try {
      const result = await adminApi.post("/api/admin/apify/sync", { mock: "true" });
      setSyncResult(result);
      fetchStatus();
    } catch (err) {
      setError(err.message || "Mock sync failed.");
      fetchStatus();
    } finally {
      setSyncing(false);
    }
  }

  if (loading) return (
    <div className="sync-status-panel">
      <p className="muted">Loading sync status…</p>
    </div>
  );

  const isRunning  = status?.is_running || syncing;
  const lastStatus = status?.last_run_status;

  const STATS = [
    { key: "fetched",        label: "Fetched" },
    { key: "new_posts",      label: "New" },
    { key: "duplicates",     label: "Duplicates" },
    { key: "classified",     label: "Classified" },
    { key: "review_required",label: "Review Reqd." },
    { key: "non_activity",   label: "Non-Activity" },
    { key: "errors",         label: "Errors" },
  ];

  return (
    <div className="sync-status-panel">
      <div className="sync-status-header">
        <h3 className="sync-status-title">LinkedIn Sync Status (Apify)</h3>
        <StatusBadge isRunning={isRunning} lastStatus={lastStatus} />
      </div>

      {/* Counts grid */}
      <div className="sync-stats-grid">
        {STATS.map(({ key, label }) => (
          <div key={key} className="sync-stat">
            <div className="sync-stat-value">{fmt(status?.[key])}</div>
            <div className="sync-stat-label">{label}</div>
          </div>
        ))}
      </div>

      {/* Meta info */}
      <div className="sync-meta">
        <span>
          🕐 Last sync:{" "}
          <strong>{fmtDate(status?.last_sync)}</strong>
        </span>
        {status?.last_checkpoint && (
          <span>
            📍 Last checkpoint:{" "}
            <strong>{fmtDate(status.last_checkpoint)}</strong>
          </span>
        )}
        <span>
          📅 Schedule: <strong>Every Monday at 09:00 IST</strong>
        </span>
      </div>

      {/* Sync result feedback */}
      {syncResult && !error && (
        <p className="ok state" role="status" style={{ marginBottom: 12 }}>
          ✓ Sync complete — {fmt(syncResult.new_posts)} new{" "}
          {syncResult.new_posts === 1 ? "activity" : "activities"} added
          {syncResult.duplicates > 0 ? `, ${fmt(syncResult.duplicates)} duplicates skipped` : ""}.
        </p>
      )}
      {error && (
        <p className="error state" role="alert" style={{ marginBottom: 12 }}>
          {error}
        </p>
      )}

      {/* Actions */}
      <div className="sync-actions">
        <button
          type="button"
          id="apify-run-now-btn"
          className="primary"
          onClick={handleRunNow}
          disabled={isRunning}
        >
          {isRunning ? "Syncing…" : "▶ Run Update Now"}
        </button>
        <button
          type="button"
          id="apify-run-mock-btn"
          className="ghost"
          onClick={handleRunMock}
          disabled={isRunning}
          title="Run with 5 mock posts — safe for testing"
        >
          🧪 Test with Mock Data
        </button>
        <button
          type="button"
          className="ghost"
          onClick={fetchStatus}
          disabled={isRunning}
        >
          ↻ Refresh
        </button>
      </div>

      <p className="muted note" style={{ marginTop: 12 }}>
        The API token is stored server-side only and is never exposed to the frontend.
        Apify posts go through staging → deduplication → classification → reportable pipeline.
        Existing Admin edits are never overwritten.
      </p>
    </div>
  );
}
