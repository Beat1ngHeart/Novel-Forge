"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { api, type VolumeOutline } from "@/lib/api";

const STATUS_COLORS: Record<string, string> = {
  draft: "bg-gray-100 text-gray-700",
  adopted: "bg-green-100 text-green-800",
};

export default function VolumesPage() {
  const { id: projectId } = useParams() as { id: string };
  const [volumes, setVolumes] = useState<VolumeOutline[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState<string | null>(null);
  const [editField, setEditField] = useState("");
    const [editValue, setEditValue] = useState("");
  const [synopsisId, setSynopsisId] = useState("");
  const [synopses, setSynopses] = useState<{ id: string; label: string }[]>([]);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [vols, syns] = await Promise.all([
        api.listVolumes(projectId),
        api.listSynopses(projectId),
      ]);
      setVolumes(vols);
      const adopted = syns.filter((s) => s.status === "adopted");
      setSynopses(adopted.map((s) => ({ id: s.id, label: `v${s.version}: ${s.one_liner.slice(0, 30)}` })));
      if (adopted.length > 0 && !synopsisId) setSynopsisId(adopted[0].id);
    } catch {}
    setLoading(false);
  }, [projectId, synopsisId]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, [load]);

  const handleGenerate = async () => {
    if (!synopsisId) return;
    setGenerating(true);
    try {
      await api.generateVolumes(projectId, synopsisId);
      load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "生成失败");
    }
    setGenerating(false);
  };

  const handleEdit = async (volumeId: string, field: string, value: string) => {
    await api.updateVolume(projectId, volumeId, { [field]: value });
    setEditing(null);
    load();
  };

  const handleAdopt = async (volumeId: string) => {
    await api.adoptVolume(projectId, volumeId);
    load();
  };

  const handleRegenerate = async (volumeId: string) => {
    await api.regenerateVolume(projectId, volumeId);
    load();
  };

  if (loading) return <p className="text-gray-400 p-6">加载中...</p>;

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex items-center justify-between">
        <div>
          <Link href={`/projects/${projectId}`} className="text-blue-600 hover:underline text-sm">
            &larr; 返回项目
          </Link>
          <h1 className="text-2xl font-bold mt-2">分卷大纲</h1>
        </div>
      </div>

      {error && <div className="bg-red-50 border border-red-200 rounded p-3 text-sm text-red-700">{error}</div>}

      {/* Generate */}
      {volumes.length === 0 && (
        <div className="bg-white border rounded-lg p-5 space-y-3">
          <h2 className="font-semibold">从正式总纲生成分卷</h2>
          {synopses.length === 0 ? (
            <p className="text-sm text-gray-400">请先在「总纲」页面采用一个正式总纲。</p>
          ) : (
            <div className="flex gap-3 items-end">
              <select
                className="border rounded px-2 py-1.5 text-sm w-80"
                value={synopsisId}
                onChange={(e) => setSynopsisId(e.target.value)}
              >
                {synopses.map((s) => (
                  <option key={s.id} value={s.id}>{s.label}</option>
                ))}
              </select>
              <button
                onClick={handleGenerate}
                disabled={generating || !synopsisId}
                className="bg-purple-600 text-white px-4 py-1.5 rounded text-sm hover:bg-purple-700 disabled:opacity-50"
              >
                {generating ? "生成中..." : "生成全部分卷"}
              </button>
            </div>
          )}
        </div>
      )}

      {/* Volumes list */}
      {volumes.length === 0 && !loading && (
        <div className="bg-white border rounded-lg p-12 text-center text-gray-400">
          <p className="text-lg mb-2">暂无分卷</p>
        </div>
      )}

      {volumes.map((vol, idx) => (
        <div key={vol.id} className={`bg-white border rounded-lg p-5 ${vol.status === "adopted" ? "border-green-300" : ""}`}>
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-400">#{idx + 1}</span>
              <h2 className="font-semibold text-lg">{vol.volume_name}</h2>
              <span className={`text-xs px-1.5 py-0.5 rounded ${STATUS_COLORS[vol.status]}`}>{vol.status}</span>
              <span className="text-xs text-gray-400">预计 {vol.estimated_chapters} 章 / {vol.estimated_words.toLocaleString()} 字</span>
            </div>
            <div className="flex gap-2">
              {vol.status === "draft" && (
                <button onClick={() => handleAdopt(vol.id)} className="text-xs bg-green-600 text-white px-2 py-1 rounded hover:bg-green-700">采用</button>
              )}
              <Link href={`/projects/${projectId}/volumes/${vol.id}/rhythm`} className="text-xs border px-2 py-1 rounded hover:bg-gray-50">节奏表</Link>
              <button onClick={() => handleRegenerate(vol.id)} className="text-xs border px-2 py-1 rounded hover:bg-gray-50">重新生成</button>
            </div>
          </div>

          <div className="space-y-2">
            {[
              { key: "volume_goal", label: "卷目标" },
              { key: "core_conflict", label: "核心冲突" },
              { key: "start_state", label: "开始状态" },
              { key: "end_state", label: "结束状态" },
              { key: "main_enemy", label: "主要敌人" },
              { key: "character_changes", label: "人物变化" },
              { key: "growth_milestone", label: "成长节点" },
              { key: "payoff_climax", label: "爽点高潮" },
              { key: "volume_twist", label: "卷末转折" },
              { key: "foreshadow_planted", label: "伏笔埋设" },
              { key: "foreshadow_resolved", label: "伏笔回收" },
              { key: "reader_promise_fulfilled", label: "读者承诺兑现" },
            ].map(({ key, label }) => {
              const value = (vol as unknown as Record<string, string>)[key];
              if (!value) return null;
              return (
                <div key={key}>
                  <dt className="text-xs text-gray-500">{label}</dt>
                  {editing === `${vol.id}-${key}` ? (
                    <div className="flex gap-2 mt-1">
                      <textarea
                        className="flex-1 border rounded px-2 py-1 text-sm min-h-[40px]"
                        value={editValue}
                        onChange={(e) => setEditValue(e.target.value)}
                      />
                      <div className="flex flex-col gap-1">
                        <button onClick={() => handleEdit(vol.id, editField, editValue)} className="text-xs bg-blue-600 text-white px-2 py-1 rounded">保存</button>
                        <button onClick={() => setEditing(null)} className="text-xs border px-2 py-1 rounded">取消</button>
                      </div>
                    </div>
                  ) : (
                    <dd
                      className="text-sm whitespace-pre-wrap cursor-pointer hover:bg-gray-50 rounded px-1 -mx-1"
                      onClick={() => { setEditing(`${vol.id}-${key}`); setEditField(key); setEditValue(value); }}
                    >
                      {value}
                    </dd>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      ))}

      {volumes.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded p-3 text-sm text-yellow-800">
          重新生成某一卷不会覆盖其他卷的人工修改内容。
        </div>
      )}
    </div>
  );
}
