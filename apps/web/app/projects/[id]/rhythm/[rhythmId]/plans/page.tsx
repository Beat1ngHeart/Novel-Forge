"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { api, type ChapterPlan } from "@/lib/api";

const STATUS_COLORS: Record<string, string> = {
  draft: "bg-gray-100 text-gray-700",
  adopted: "bg-green-100 text-green-800",
  rejected: "bg-red-100 text-red-800",
};

const PLAN_FIELDS = [
  { key: "chapter_goal", label: "本章目标" },
  { key: "characters", label: "出场人物" },
  { key: "scenes", label: "场景顺序" },
  { key: "obstacle", label: "阻碍" },
  { key: "turning_point", label: "转折" },
  { key: "information_gain", label: "信息增量" },
  { key: "emotion_curve", label: "情绪曲线" },
  { key: "payoff", label: "爽点" },
  { key: "foreshadow_action", label: "伏笔" },
  { key: "foreshadow_resolved", label: "伏笔兑现" },
  { key: "relationship_changes", label: "人物关系变化" },
  { key: "end_state", label: "章节结束状态" },
  { key: "chapter_hook", label: "章末钩子" },
  { key: "repetition_risk", label: "重复风险" },
  { key: "logic_issues", label: "逻辑问题" },
];

export default function ChapterPlansPage() {
  const { id: projectId, rhythmId } = useParams() as { id: string; rhythmId: string };
  const [plans, setPlans] = useState<ChapterPlan[]>([]);
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
      const p = await api.listChapterPlans(projectId, rhythmId);
      setPlans(p);
    } catch {}
    setLoading(false);
  }, [projectId, rhythmId]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, [load]);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      await api.generateChapterPlans(projectId, rhythmId);
      load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "生成失败");
    }
    setGenerating(false);
  };

  const handleEdit = async (planId: string, field: string, value: string) => {
    await api.updateChapterPlan(projectId, planId, { [field]: value });
    setEditing(null);
    load();
  };

  const handleAdopt = async (planId: string) => {
    await api.adoptChapterPlan(projectId, planId);
    load();
  };

  const handleReject = async (planId: string) => {
    await api.rejectChapterPlan(projectId, planId);
    load();
  };

  const handleRegenerate = async (planId: string) => {
    await api.regenerateChapterPlan(projectId, planId);
    load();
  };

  if (loading) return <p className="text-gray-400 p-6">加载中...</p>;

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="flex items-center justify-between">
        <div>
          <Link href={`/projects/${projectId}/volumes`} className="text-blue-600 hover:underline text-sm">
            &larr; 返回分卷大纲
          </Link>
          <h1 className="text-2xl font-bold mt-2">单章策划</h1>
          <p className="text-sm text-gray-500">{plans.length} 个方案</p>
        </div>
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="bg-purple-600 text-white px-4 py-2 rounded text-sm hover:bg-purple-700 disabled:opacity-50"
        >
          {generating ? "生成中..." : plans.length > 0 ? "重新生成方案" : "生成3个方案"}
        </button>
      </div>

      {error && <div className="bg-red-50 border border-red-200 rounded p-3 text-sm text-red-700">{error}</div>}

      {plans.length === 0 && (
        <div className="bg-white border rounded-lg p-12 text-center text-gray-400">
          <p className="text-lg mb-2">暂无策划方案</p>
          <p className="text-sm">点击「生成3个方案」开始</p>
        </div>
      )}

      {/* Plans grid */}
      {plans.length > 0 && (
        <div className="grid grid-cols-1 gap-4">
          {plans.map((plan, idx) => (
            <div
              key={plan.id}
              className={`bg-white border rounded-lg p-5 ${
                plan.status === "adopted"
                  ? "border-green-400 ring-2 ring-green-200"
                  : plan.status === "rejected"
                    ? "opacity-50"
                    : ""
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="font-semibold">方案 {idx + 1}</span>
                  <span className={`text-xs px-1.5 py-0.5 rounded ${STATUS_COLORS[plan.status]}`}>
                    {plan.status}
                  </span>
                  {plan.is_adopted && <span className="text-xs text-green-600">✓ 正式采用</span>}
                </div>
                <div className="flex gap-1">
                  {plan.status === "draft" && (
                    <>
                      <button
                        onClick={() => handleAdopt(plan.id)}
                        className="text-xs bg-green-600 text-white px-2 py-1 rounded hover:bg-green-700"
                      >
                        采用
                      </button>
                      <button
                        onClick={() => handleReject(plan.id)}
                        className="text-xs border border-red-300 text-red-600 px-2 py-1 rounded hover:bg-red-50"
                      >
                        拒绝
                      </button>
                      <button
                        onClick={() => handleRegenerate(plan.id)}
                        className="text-xs border px-2 py-1 rounded hover:bg-gray-50"
                      >
                        重生成
                      </button>
                    </>
                  )}
                  <button
                    onClick={() => setExpanded(expanded === plan.id ? null : plan.id)}
                    className="text-xs border px-2 py-1 rounded hover:bg-gray-50"
                  >
                    {expanded === plan.id ? "收起" : "展开"}
                  </button>
                </div>
              </div>

              {/* Summary */}
              <div className="text-sm text-gray-700 mb-2">
                <strong>目标：</strong>{plan.chapter_goal}
              </div>
              <div className="text-sm text-gray-500 mb-2">
                <strong>钩子：</strong>{plan.chapter_hook}
              </div>

              {/* Expanded details */}
              {expanded === plan.id && (
                <div className="mt-3 space-y-2 border-t pt-3">
                  {PLAN_FIELDS.map(({ key, label }) => {
                    const value = (plan as unknown as Record<string, string>)[key];
                    if (!value) return null;
                    return (
                      <div key={key} className="flex gap-2 text-sm">
                        <span className="text-xs text-gray-500 w-24 shrink-0">{label}</span>
                        {editing === `${plan.id}-${key}` ? (
                          <div className="flex gap-2 flex-1">
                            <textarea
                              className="flex-1 border rounded px-2 py-1 text-sm min-h-[40px]"
                              value={editValue}
                              onChange={(e) => setEditValue(e.target.value)}
                            />
                            <div className="flex flex-col gap-1">
                              <button
                                onClick={() => handleEdit(plan.id, editField, editValue)}
                                className="text-xs bg-blue-600 text-white px-2 py-1 rounded"
                              >
                                保存
                              </button>
                              <button onClick={() => setEditing(null)} className="text-xs border px-2 py-1 rounded">
                                取消
                              </button>
                            </div>
                          </div>
                        ) : (
                          <span
                            className="flex-1 whitespace-pre-wrap cursor-pointer hover:bg-gray-50 rounded px-1 -mx-1"
                            onClick={() => {
                              setEditing(`${plan.id}-${key}`);
                              setEditField(key);
                              setEditValue(value);
                            }}
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
      )}

      {plans.some((p) => p.status === "adopted") && (
        <div className="bg-green-50 border border-green-200 rounded p-3 text-sm text-green-800">
          已采用的方案将作为正文生成的依据。其他方案已自动标记为拒绝。
        </div>
      )}
    </div>
  );
}
