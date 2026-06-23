"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { api, type StateChangeCandidate } from "@/lib/api";

const TYPE_LABELS: Record<string, { label: string; icon: string }> = {
  character_location: { label: "位置变化", icon: "📍" },
  character_relationship: { label: "关系变化", icon: "🤝" },
  character_goal: { label: "目标变化", icon: "🎯" },
  power_change: { label: "战力变化", icon: "⚔️" },
  resource_change: { label: "资源变化", icon: "💰" },
  health_change: { label: "伤势变化", icon: "🏥" },
  new_skill: { label: "新增技能", icon: "✨" },
  new_world_rule: { label: "新增规则", icon: "📜" },
  new_character: { label: "新增人物", icon: "👤" },
  new_foreshadow: { label: "新增伏笔", icon: "🔮" },
  foreshadow_resolved: { label: "伏笔兑现", icon: "✅" },
  plot_thread_progress: { label: "剧情推进", icon: "📖" },
  timeline_event: { label: "时间线事件", icon: "⏰" },
  knowledge_change: { label: "知情范围", icon: "🧠" },
};

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-gray-100 text-gray-700",
  accepted: "bg-green-100 text-green-800",
  rejected: "bg-red-100 text-red-800",
  failed: "bg-orange-100 text-orange-800",
};

export default function StateChangesPage() {
  const { id: projectId, draftId } = useParams() as { id: string; draftId: string };
  const [candidates, setCandidates] = useState<StateChangeCandidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const c = await api.listStateChanges(projectId, {
        draft_id: draftId,
        status: filterStatus || undefined,
      });
      setCandidates(c);
    } catch {}
    setLoading(false);
  }, [projectId, draftId, filterStatus]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, [load]);

  const handleGenerate = async () => {
    setGenerating(true);
    setError(null);
    try {
      const c = await api.generateStateChanges(projectId, draftId);
      setCandidates(c);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "提取失败");
    }
    setGenerating(false);
  };

  const handleAccept = async (id: string) => {
    await api.acceptStateChange(projectId, id);
    load();
  };

  const handleReject = async (id: string) => {
    const reason = prompt("拒绝原因（可选）") || "";
    await api.rejectStateChange(projectId, id, reason);
    load();
  };

  const handleUndo = async (id: string) => {
    await api.undoStateChange(projectId, id);
    load();
  };

  const pending = candidates.filter((c) => c.status === "pending");
  const accepted = candidates.filter((c) => c.status === "accepted");

  if (loading) return <p className="text-gray-400 p-6">加载中...</p>;

  return (
    <div className="space-y-6 max-w-4xl">
      <Link href={`/projects/${projectId}/plans/${draftId}/draft`} className="text-blue-600 hover:underline text-sm">
        &larr; 返回正文
      </Link>

      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">状态变化候选</h1>
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="bg-purple-600 text-white px-4 py-2 rounded text-sm hover:bg-purple-700 disabled:opacity-50"
        >
          {generating ? "提取中..." : "从正文提取变化"}
        </button>
      </div>

      {error && <div className="bg-red-50 border border-red-200 rounded p-3 text-sm text-red-700">{error}</div>}

      {/* Filter */}
      {candidates.length > 0 && (
        <div className="flex gap-3 items-center">
          <select
            className="border rounded px-2 py-1.5 text-sm"
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
          >
            <option value="">全部状态</option>
            <option value="pending">待处理</option>
            <option value="accepted">已接受</option>
            <option value="rejected">已拒绝</option>
          </select>
          <span className="text-sm text-gray-500">
            {pending.length} 待处理 · {accepted.length} 已接受
          </span>
        </div>
      )}

      {candidates.length === 0 && !loading && (
        <div className="bg-white border rounded-lg p-12 text-center text-gray-400">
          <p className="text-lg mb-2">暂无状态变化</p>
          <p className="text-sm">点击「从正文提取变化」开始</p>
        </div>
      )}

      {/* Candidates by type */}
      {candidates.length > 0 && (
        <div className="space-y-3">
          {candidates.map((c) => {
            const typeInfo = TYPE_LABELS[c.change_type] || { label: c.change_type, icon: "❓" };
            return (
              <div
                key={c.id}
                className={`bg-white border rounded-lg p-4 ${c.status === "rejected" ? "opacity-50" : ""}`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span>{typeInfo.icon}</span>
                    <span className="text-sm font-medium">{typeInfo.label}</span>
                    <span className="text-sm text-gray-600">— {c.entity_name}</span>
                    <span className={`text-xs px-1.5 py-0.5 rounded ${STATUS_COLORS[c.status]}`}>{c.status}</span>
                  </div>
                  <div className="flex gap-1">
                    {c.status === "pending" && (
                      <>
                        <button
                          onClick={() => handleAccept(c.id)}
                          className="text-xs bg-green-600 text-white px-2 py-1 rounded hover:bg-green-700"
                        >
                          接受
                        </button>
                        <button
                          onClick={() => handleReject(c.id)}
                          className="text-xs border border-red-300 text-red-600 px-2 py-1 rounded hover:bg-red-50"
                        >
                          拒绝
                        </button>
                      </>
                    )}
                    {c.status === "accepted" && (
                      <button
                        onClick={() => handleUndo(c.id)}
                        className="text-xs text-orange-600 hover:underline"
                      >
                        撤销
                      </button>
                    )}
                  </div>
                </div>
                <div className="text-sm space-y-1">
                  {c.before_value && (
                    <p>
                      <span className="text-xs text-gray-500">之前：</span>
                      <span className="text-gray-600">{c.before_value}</span>
                    </p>
                  )}
                  <p>
                    <span className="text-xs text-gray-500">之后：</span>
                    <span className="text-gray-800 font-medium">{c.after_value}</span>
                  </p>
                  <p>
                    <span className="text-xs text-gray-500">原因：</span>
                    <span className="text-gray-600">{c.reason}</span>
                  </p>
                  {c.rejection_reason && (
                    <p className="text-xs text-red-500">拒绝原因: {c.rejection_reason}</p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
