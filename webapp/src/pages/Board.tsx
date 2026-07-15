import { useEffect, useState } from "react";

import { type Case, fetchCases } from "../api";
import { useAuth } from "../auth/context";

const STATUS_OPTIONS = [
  "new",
  "in_prep",
  "draft_ready",
  "reply_filed",
  "dropped",
  "order_passed",
  "appeal_window",
  "closed",
];

const URGENCY_STYLES: Record<string, string> = {
  overdue: "bg-red-100 text-red-800",
  due_soon_3d: "bg-amber-100 text-amber-800",
  due_soon_7d: "bg-yellow-100 text-yellow-800",
  on_track: "bg-green-100 text-green-800",
  no_deadline: "bg-gray-100 text-gray-600",
};

export default function Board() {
  const { user, signOut } = useAuth();
  const [cases, setCases] = useState<Case[]>([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    fetchCases(statusFilter || undefined)
      .then((data) => {
        if (!cancelled) setCases(data);
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Failed to load cases");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [statusFilter]);

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="mx-auto max-w-5xl">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-gray-900">NoticeDesk board</h1>
            <p className="text-sm text-gray-500">{user?.email}</p>
          </div>
          <button
            type="button"
            onClick={() => void signOut()}
            className="rounded-md border border-gray-300 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-100"
          >
            Sign out
          </button>
        </div>

        <div className="mb-4">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
          >
            <option value="">All statuses</option>
            {STATUS_OPTIONS.map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </select>
        </div>

        {loading && <p className="text-sm text-gray-500">Loading cases…</p>}
        {error && <p className="text-sm text-red-600">{error}</p>}

        {!loading && !error && cases.length === 0 && (
          <p className="text-sm text-gray-500">No cases yet. Upload a notice to get started.</p>
        )}

        {!loading && !error && cases.length > 0 && (
          <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left font-medium text-gray-500">Notice type</th>
                  <th className="px-4 py-2 text-left font-medium text-gray-500">Period</th>
                  <th className="px-4 py-2 text-left font-medium text-gray-500">Status</th>
                  <th className="px-4 py-2 text-left font-medium text-gray-500">Due date</th>
                  <th className="px-4 py-2 text-left font-medium text-gray-500">Urgency</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {cases.map((c) => (
                  <tr key={c.id}>
                    <td className="px-4 py-2 text-gray-900">{c.notice_type}</td>
                    <td className="px-4 py-2 text-gray-600">{c.fy_period ?? "—"}</td>
                    <td className="px-4 py-2 text-gray-600">{c.status}</td>
                    <td className="px-4 py-2 text-gray-600">
                      {c.due_date ? new Date(c.due_date).toLocaleDateString() : "—"}
                    </td>
                    <td className="px-4 py-2">
                      <span
                        className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                          URGENCY_STYLES[c.urgency] ?? URGENCY_STYLES.no_deadline
                        }`}
                      >
                        {c.urgency.replace(/_/g, " ")}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
