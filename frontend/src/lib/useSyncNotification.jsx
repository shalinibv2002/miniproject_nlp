/**
 * useSyncNotification — lightweight hook for real-time Apify sync notifications.
 *
 * Polls /api/admin/apify/notification every 60 s (non-blocking, background).
 * Returns the notification object or null.
 * Marks it as seen when the user dismisses it.
 *
 * Uses REAL counts from the database. Never hard-codes any values.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../services/api";

const POLL_INTERVAL_MS = 60_000; // 1 minute — non-blocking

export function useSyncNotification() {
  const [notification, setNotification] = useState(null);
  const timerRef = useRef(null);

  const poll = useCallback(async () => {
    try {
      const data = await api.get("/api/admin/apify/notification");
      if (data?.notification) {
        setNotification(data.notification);
      }
    } catch {
      // Silently ignore — notifications are non-critical
    }
  }, []);

  useEffect(() => {
    poll();
    timerRef.current = setInterval(poll, POLL_INTERVAL_MS);
    return () => clearInterval(timerRef.current);
  }, [poll]);

  const dismiss = useCallback(async () => {
    if (!notification) return;
    const runId = notification.run_id;
    setNotification(null);
    try {
      await api.post("/api/admin/apify/notification/seen", { run_id: runId });
    } catch {
      // Ignore — best effort
    }
  }, [notification]);

  return { notification, dismiss };
}

/**
 * SyncNotificationBanner — compact, dismissible banner shown on the Dashboard.
 *
 * Renders only when there is a new sync notification.
 * Uses real counts from the notification object.
 */
export function SyncNotificationBanner({ notification, onDismiss }) {
  if (!notification) return null;

  const { new_activities, review_required } = notification;

  return (
    <div className="sync-notification" role="status" aria-live="polite">
      <span className="sync-notification-icon">🔄</span>
      <div className="sync-notification-body">
        <strong>
          LinkedIn sync completed — {new_activities}{" "}
          {new_activities === 1 ? "new activity" : "new activities"} added
        </strong>
        {review_required > 0 && (
          <p>{review_required} {review_required === 1 ? "record requires" : "records require"} admin review.</p>
        )}
      </div>
      <button
        type="button"
        className="sync-notification-close"
        onClick={onDismiss}
        aria-label="Dismiss notification"
        title="Dismiss"
      >
        ×
      </button>
    </div>
  );
}
