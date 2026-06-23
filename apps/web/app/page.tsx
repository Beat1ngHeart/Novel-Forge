"use client";

import { useEffect, useState } from "react";
import { api, type HealthResponse } from "@/lib/api";

function StatusBadge({ label, value, ok }: { label: string; value: string; ok: boolean }) {
  return (
    <div className="flex items-center gap-2">
      <span className={`w-2 h-2 rounded-full ${ok ? "bg-green-500" : "bg-red-500"}`} />
      <span className="text-sm text-gray-600">{label}</span>
      <span className={`text-sm font-medium ${ok ? "text-green-700" : "text-red-700"}`}>{value}</span>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="bg-white rounded-lg border p-5">
      <div className="text-2xl font-bold">{value}</div>
      <div className="text-sm text-gray-500 mt-1">{label}</div>
    </div>
  );
}

export default function DashboardPage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .health()
      .then(setHealth)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">仪表盘</h1>

      <div className="bg-white rounded-lg border p-5 space-y-3">
        <h2 className="font-semibold">系统状态</h2>
        {loading && <p className="text-sm text-gray-400">检查中...</p>}
        {error && <p className="text-sm text-red-500">无法连接后端: {error}</p>}
        {health && (
          <div className="space-y-2">
            <StatusBadge label="后端服务" value={health.status} ok={health.status === "healthy"} />
            <StatusBadge label="数据库" value={health.database} ok={health.database === "connected"} />
            <StatusBadge
              label="LLM Provider"
              value={`${health.llm.provider} (${health.llm.status})`}
              ok={health.llm.status === "ok"}
            />
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="小说项目" value={0} />
        <StatCard label="已导入资料" value={0} />
        <StatCard label="已分析章节" value={0} />
        <StatCard label="AI 任务" value={0} />
      </div>

      <p className="text-xs text-gray-400">统计数据在接入真实数据后自动更新，当前显示零值。</p>
    </div>
  );
}
