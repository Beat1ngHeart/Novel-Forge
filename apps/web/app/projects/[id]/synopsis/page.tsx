"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { api, type NovelSynopsis } from "@/lib/api";

const STATUS_COLORS: Record<string, string> = {
  draft: "bg-gray-100 text-gray-700",
  adopted: "bg-green-100 text-green-800",
  superseded: "bg-yellow-100 text-yellow-800",
};

const FIELDS = [
  { key: "one_liner", label: "一句话故事" },
  { key: "core_selling_point", label: "核心卖点" },
  { key: "protagonist_start", label: "主角起点" },
  { key: "final_goal", label: "最终目标" },
  { key: "core_conflict", label: "核心矛盾" },
  { key: "story_phases", label: "全书阶段" },
  { key: "growth_arc", label: "主角成长路线" },
  { key: "main_antagonist", label: "主要反派" },
  { key: "relationship_changes", label: "主要关系变化" },
  { key: "world_truth", label: "世界真相" },
  { key: "key_foreshadowings", label: "关键伏笔" },
  { key: "reader_promise_plan", label: "读者承诺兑现计划" },
  { key: "ending", label: "最终结局" },
  { key: "risk_warnings", label: "风险提示" },
];

export default function SynopsisPage() {
  const { id: projectId } = useParams() as { id: string };
  const [synopses, setSynopses] = useState<NovelSynopsis[]>([]);
  const [selected, setSelected] = useState<NovelSynopsis | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [editing, setEditing] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [directionId, setDirectionId] = useState("");
  const [directions, setDirections] = useState<{ id: string; name: string }[]>([]);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [syns, sess] = await Promise.all([
        api.listSynopses(projectId),
        api.listCreativeSessions(projectId),
      ]);
      setSynopses(syns);
      if (syns.length > 0 && !selected) {
        setSelected(syns[0]);
      }
      // Load adopted directions
      const adopted: { id: string; name: string }[] = [];
      for (const s of sess) {
        const sDirs = await api.listSessionDirections(projectId, s.id);
        for (const d of sDirs) {
          if (d.status === "adopted") adopted.push({ id: d.id, name: d.one_line_hook.slice(0, 40) });
        }
      }
      setDirections(adopted);
    } catch {}
    setLoading(false);
  }, [projectId, selected]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, [load]);

  const handleGenerate = async () => {
    if (!directionId) return;
    setGenerating(true);
    try {
      const s = await api.generateSynopsis(projectId, directionId);
      setSynopses((prev) => [s, ...prev]);
      setSelected(s);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "生成失败");
    }
    setGenerating(false);
  };

  const handleEdit = async (field: string, value: string) => {
    if (!selected) return;
    try {
      const updated = await api.updateSynopsis(projectId, selected.id, { [field]: value });
      setSelected(updated);
      setSynopses((prev) => prev.map((s) => (s.id === updated.id ? updated : s)));
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "编辑失败");
    }
    setEditing(null);
  };

  const handleAdopt = async () => {
    if (!selected) return;
    if (selected.status === "adopted") {
      alert("该版本已经是当前正式版本");
      return;
    }
    try {
      const adopted = await api.adoptSynopsis(projectId, selected.id);
      setSelected(adopted);
      load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "采用失败");
    }
  };

  const handleRestore = async (synopsisId: string) => {
    try {
      const restored = await api.restoreSynopsis(projectId, synopsisId);
      setSelected(restored);
      load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "恢复失败");
    }
  };

  if (loading) return <p className="text-gray-400 p-6">加载中...</p>;

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex items-center justify-between">
        <div>
          <Link href={`/projects/${projectId}`} className="text-blue-600 hover:underline text-sm">
            &larr; 返回项目
          </Link>
          <h1 className="text-2xl font-bold mt-2">全书总纲</h1>
        </div>
        <div className="flex gap-2">
          {selected && selected.status !== "adopted" && (
            <button
              onClick={handleAdopt}
              className="bg-green-600 text-white px-4 py-2 rounded text-sm hover:bg-green-700"
            >
              采用为正式总纲
            </button>
          )}
        </div>
      </div>

      {error && <div className="bg-red-50 border border-red-200 rounded p-3 text-sm text-red-700">{error}</div>}

      {/* Generate */}
      {synopses.length === 0 && (
        <div className="bg-white border rounded-lg p-5 space-y-3">
          <h2 className="font-semibold">从创意方向生成总纲</h2>
          {directions.length === 0 ? (
            <p className="text-sm text-gray-400">请先在「创意方向」页面采用一个方向。</p>
          ) : (
            <div className="flex gap-3 items-end">
              <select
                className="border rounded px-2 py-1.5 text-sm w-80"
                value={directionId}
                onChange={(e) => setDirectionId(e.target.value)}
              >
                <option value="">选择已采用的方向...</option>
                {directions.map((d) => (
                  <option key={d.id} value={d.id}>{d.name}</option>
                ))}
              </select>
              <button
                onClick={handleGenerate}
                disabled={generating || !directionId}
                className="bg-purple-600 text-white px-4 py-1.5 rounded text-sm hover:bg-purple-700 disabled:opacity-50"
              >
                {generating ? "生成中..." : "生成总纲"}
              </button>
            </div>
          )}
        </div>
      )}

      {/* Version selector */}
      {synopses.length > 0 && (
        <div className="flex gap-2 flex-wrap">
          {synopses.map((s) => (
            <button
              key={s.id}
              onClick={() => setSelected(s)}
              className={`text-xs px-3 py-1.5 rounded border ${
                selected?.id === s.id ? "bg-blue-100 border-blue-300" : "hover:bg-gray-50"
              }`}
            >
              v{s.version}
              <span className={`ml-1 ${STATUS_COLORS[s.status]}`}>{s.status}</span>
              {s.is_current && <span className="ml-1 text-green-600">★</span>}
            </button>
          ))}
          <button
            onClick={handleGenerate}
            disabled={generating || !directionId}
            className="text-xs px-3 py-1.5 rounded border border-dashed hover:bg-gray-50"
          >
            + 生成新版本
          </button>
        </div>
      )}

      {/* Synopsis content */}
      {selected && (
        <div className="bg-white border rounded-lg p-5 space-y-4">
          <div className="flex items-center justify-between border-b pb-3">
            <div>
              <span className="text-sm text-gray-500">
                版本 {selected.version} · {selected.status}
                {selected.is_current && " · 当前正式版本"}
              </span>
            </div>
            <div className="flex gap-2">
              {selected.status === "superseded" && (
                <button
                  onClick={() => handleRestore(selected.id)}
                  className="text-xs text-blue-600 hover:underline"
                >
                  恢复此版本
                </button>
              )}
            </div>
          </div>

          {FIELDS.map(({ key, label }) => {
            const value = (selected as unknown as Record<string, string>)[key];
            return (
              <div key={key} className="border-b border-gray-100 pb-3">
                <dt className="text-xs text-gray-500 mb-1">{label}</dt>
                {editing === key ? (
                  <div className="flex gap-2">
                    <textarea
                      className="flex-1 border rounded px-2 py-1 text-sm min-h-[60px]"
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                    />
                    <div className="flex flex-col gap-1">
                      <button onClick={() => handleEdit(key, editValue)} className="text-xs bg-blue-600 text-white px-2 py-1 rounded">保存</button>
                      <button onClick={() => setEditing(null)} className="text-xs border px-2 py-1 rounded">取消</button>
                    </div>
                  </div>
                ) : (
                  <dd
                    className="text-sm whitespace-pre-wrap cursor-pointer hover:bg-gray-50 rounded px-2 py-1 -mx-2"
                    onClick={() => { setEditing(key); setEditValue(value || ""); }}
                    title="点击编辑"
                  >
                    {value || <span className="text-gray-300">点击编辑...</span>}
                  </dd>
                )}
              </div>
            );
          })}
        </div>
      )}

      {selected && selected.status === "adopted" && (
        <div className="bg-yellow-50 border border-yellow-200 rounded p-3 text-sm text-yellow-800">
          <strong>注意：</strong>修改已采用的总纲后，后续生成的分卷大纲可能需要重新生成。本阶段不会自动删除已有大纲。
        </div>
      )}
    </div>
  );
}
