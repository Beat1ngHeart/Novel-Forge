"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { api, type ChapterRhythmPlan } from "@/lib/api";

const FUNCTION_COLORS: Record<string, string> = {
  "开场铺垫": "bg-blue-100 text-blue-800",
  "世界观建立": "bg-teal-100 text-teal-800",
  "冲突升级": "bg-orange-100 text-orange-800",
  "高潮": "bg-red-100 text-red-800",
  "过渡": "bg-gray-100 text-gray-600",
  "伏笔埋设": "bg-purple-100 text-purple-800",
};

export default function RhythmPage() {
  const { id: projectId, volumeId } = useParams() as { id: string; volumeId: string };
  const [plans, setPlans] = useState<ChapterRhythmPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [editing, setEditing] = useState<string | null>(null);
  const [editField, setEditField] = useState("");
  const [editValue, setEditValue] = useState("");
  const [expanded, setExpanded] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const p = await api.listRhythms(projectId, volumeId);
      setPlans(p);
    } catch {}
    setLoading(false);
  }, [projectId, volumeId]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, [load]);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      await api.generateRhythm(projectId, volumeId, 10);
      load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "生成失败");
    }
    setGenerating(false);
  };

  const handleEdit = async (planId: string, field: string, value: string) => {
    await api.updateRhythm(projectId, planId, { [field]: value });
    setEditing(null);
    load();
  };

  const handleDelete = async (planId: string) => {
    if (!confirm("确定删除此章节计划？")) return;
    await api.deleteRhythm(projectId, planId);
    load();
  };

  const handleRegenerate = async (planId: string) => {
    await api.regenerateRhythm(projectId, planId);
    load();
  };

  if (loading) return <p className="text-gray-400 p-6">加载中...</p>;

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex items-center justify-between">
        <div>
          <Link href={`/projects/${projectId}/volumes`} className="text-blue-600 hover:underline text-sm">
            &larr; 返回分卷大纲
          </Link>
          <h1 className="text-2xl font-bold mt-2">章节节奏表</h1>
          <p className="text-sm text-gray-500">{plans.length} 个章节计划</p>
        </div>
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="bg-purple-600 text-white px-4 py-2 rounded text-sm hover:bg-purple-700 disabled:opacity-50"
        >
          {generating ? "生成中..." : plans.length > 0 ? "重新生成全部" : "生成前10章"}
        </button>
      </div>

      {error && <div className="bg-red-50 border border-red-200 rounded p-3 text-sm text-red-700">{error}</div>}

      {plans.length === 0 && (
        <div className="bg-white border rounded-lg p-12 text-center text-gray-400">
          <p className="text-lg mb-2">暂无章节计划</p>
          <p className="text-sm">点击「生成前10章」开始</p>
        </div>
      )}

      <div className="space-y-3">
        {plans.map((p) => (
          <div key={p.id} className={`bg-white border rounded-lg p-4 ${p.status === "adopted" ? "border-green-300" : ""}`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 flex-1 min-w-0">
                <span className="text-xs text-gray-400 w-8">{p.chapter_index + 1}</span>
                <span
                  className="font-medium truncate cursor-pointer hover:text-blue-600"
                  onClick={() => setExpanded(expanded === p.id ? null : p.id)}
                >
                  {p.temp_title}
                </span>
                <span className={`text-xs px-1.5 py-0.5 rounded ${FUNCTION_COLORS[p.chapter_function] || "bg-gray-100"}`}>
                  {p.chapter_function}
                </span>
                <span className="text-xs text-gray-400">{p.estimated_words}字</span>
              </div>
              <div className="flex gap-1 shrink-0">
                <Link href={`/projects/${projectId}/rhythm/${p.id}/plans`} className="text-xs text-purple-600 hover:underline">策划</Link>
                <button onClick={() => handleRegenerate(p.id)} className="text-xs text-gray-500 hover:underline">重生成</button>
                <button onClick={() => handleDelete(p.id)} className="text-xs text-red-500 hover:underline">删除</button>
              </div>
            </div>

            {expanded === p.id && (
              <div className="mt-3 space-y-2 border-t pt-3">
                {[
                  { key: "core_event", label: "核心事件" },
                  { key: "protagonist_goal", label: "主角目标" },
                  { key: "main_obstacle", label: "主要阻碍" },
                  { key: "conflict_type", label: "冲突类型" },
                  { key: "information_gain", label: "信息增量" },
                  { key: "character_change", label: "人物变化" },
                  { key: "payoff_or_emotion", label: "爽点/情绪" },
                  { key: "foreshadow_action", label: "伏笔" },
                  { key: "chapter_hook", label: "章末钩子" },
                  { key: "volume_goal_connection", label: "与卷目标关系" },
                  { key: "risk_notes", label: "风险备注" },
                ].map(({ key, label }) => {
                  const value = (p as unknown as Record<string, string>)[key];
                  if (!value) return null;
                  return (
                    <div key={key} className="flex gap-2 text-sm">
                      <span className="text-xs text-gray-500 w-20 shrink-0">{label}</span>
                      {editing === `${p.id}-${key}` ? (
                        <div className="flex gap-2 flex-1">
                          <input
                            className="flex-1 border rounded px-2 py-1 text-sm"
                            value={editValue}
                            onChange={(e) => setEditValue(e.target.value)}
                            onKeyDown={(e) => {
                              if (e.key === "Enter") handleEdit(p.id, editField, editValue);
                              if (e.key === "Escape") setEditing(null);
                            }}
                          />
                          <button onClick={() => handleEdit(p.id, editField, editValue)} className="text-xs bg-blue-600 text-white px-2 py-1 rounded">保存</button>
                        </div>
                      ) : (
                        <span
                          className="flex-1 cursor-pointer hover:bg-gray-50 rounded px-1 -mx-1"
                          onClick={() => { setEditing(`${p.id}-${key}`); setEditField(key); setEditValue(value); }}
                        >
                          {value}
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
