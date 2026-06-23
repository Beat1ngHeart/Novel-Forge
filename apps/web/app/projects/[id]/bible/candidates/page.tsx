"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { api, type BibleCandidate } from "@/lib/api";

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-gray-100 text-gray-700",
  approved: "bg-green-100 text-green-800",
  rejected: "bg-red-100 text-red-800",
  applied: "bg-blue-100 text-blue-800",
};

const CATEGORY_LABELS: Record<string, string> = {
  world_rule: "世界规则",
  character: "人物",
  plot_thread: "剧情线",
  foreshadowing: "伏笔",
  secret: "秘密",
  limitation: "限制",
  reader_promise: "读者承诺",
};

export default function BibleCandidatesPage() {
  const { id: projectId } = useParams() as { id: string };
  const [candidates, setCandidates] = useState<BibleCandidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [directionId, setDirectionId] = useState("");
  const [directions, setDirections] = useState<{ id: string; name: string }[]>([]);
  const [applying, setApplying] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [cands, dirs] = await Promise.all([
        api.listBibleCandidates(projectId),
        api.listCreativeSessions(projectId),
      ]);
      setCandidates(cands);
      // Load adopted directions
      const adopted: { id: string; name: string }[] = [];
      for (const s of dirs) {
        const sDirs = await api.listSessionDirections(projectId, s.id);
        for (const d of sDirs) {
          if (d.status === "adopted") adopted.push({ id: d.id, name: d.one_line_hook.slice(0, 40) });
        }
      }
      setDirections(adopted);
    } catch {}
    setLoading(false);
  }, [projectId]);

  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { load(); }, [load]);

  const handleGenerate = async () => {
    if (!directionId) return;
    setGenerating(true);
    try {
      await api.generateBibleCandidates(projectId, directionId);
      load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "生成失败");
    }
    setGenerating(false);
  };

  const handleApprove = async (id: string) => {
    await api.approveBibleCandidate(projectId, id);
    load();
  };

  const handleReject = async (id: string) => {
    await api.rejectBibleCandidate(projectId, id);
    load();
  };

  const handleApply = async () => {
    const approved = candidates.filter((c) => c.status === "approved");
    if (approved.length === 0) return;
    setApplying(true);
    try {
      await api.applyBibleCandidates(projectId, approved.map((c) => c.id));
      load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "应用失败");
    }
    setApplying(false);
  };

  const handleUndo = async (id: string) => {
    await api.undoBibleCandidate(projectId, id);
    load();
  };

  const pending = candidates.filter((c) => c.status === "pending");
  const approved = candidates.filter((c) => c.status === "approved");
  const applied = candidates.filter((c) => c.status === "applied");

  if (loading) return <p className="text-gray-400 p-6">加载中...</p>;

  return (
    <div className="space-y-6 max-w-4xl">
      <Link href={`/projects/${projectId}/bible`} className="text-blue-600 hover:underline text-sm">
        &larr; 返回小说圣经
      </Link>

      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">圣经候选</h1>
        <div className="flex gap-2">
          {approved.length > 0 && (
            <button
              onClick={handleApply}
              disabled={applying}
              className="bg-green-600 text-white px-4 py-2 rounded text-sm hover:bg-green-700 disabled:opacity-50"
            >
              {applying ? "应用中..." : `应用 ${approved.length} 项到圣经`}
            </button>
          )}
        </div>
      </div>

      {error && <div className="bg-red-50 border border-red-200 rounded p-3 text-sm text-red-700">{error}</div>}

      {/* Generate */}
      {candidates.length === 0 && (
        <div className="bg-white border rounded-lg p-5 space-y-3">
          <h2 className="font-semibold">从创意方向生成</h2>
          {directions.length === 0 ? (
            <p className="text-sm text-gray-400">请先在「创意方向」页面采用一个方向。</p>
          ) : (
            <div className="flex gap-3 items-end">
              <div>
                <label className="block text-xs text-gray-500 mb-1">选择已采用的方向</label>
                <select
                  className="border rounded px-2 py-1.5 text-sm w-80"
                  value={directionId}
                  onChange={(e) => setDirectionId(e.target.value)}
                >
                  <option value="">请选择...</option>
                  {directions.map((d) => (
                    <option key={d.id} value={d.id}>{d.name}</option>
                  ))}
                </select>
              </div>
              <button
                onClick={handleGenerate}
                disabled={generating || !directionId}
                className="bg-purple-600 text-white px-4 py-1.5 rounded text-sm hover:bg-purple-700 disabled:opacity-50"
              >
                {generating ? "生成中..." : "生成圣经候选"}
              </button>
            </div>
          )}
        </div>
      )}

      {/* Summary */}
      {candidates.length > 0 && (
        <div className="flex gap-4 text-sm">
          <span>总计: <strong>{candidates.length}</strong></span>
          <span className="text-gray-500">待确认: <strong>{pending.length}</strong></span>
          <span className="text-green-600">已确认: <strong>{approved.length}</strong></span>
          <span className="text-blue-600">已应用: <strong>{applied.length}</strong></span>
        </div>
      )}

      {/* Candidates by category */}
      {Object.entries(CATEGORY_LABELS).map(([cat, label]) => {
        const items = candidates.filter((c) => c.category === cat);
        if (items.length === 0) return null;
        return (
          <div key={cat} className="bg-white border rounded-lg p-5">
            <h2 className="font-semibold mb-3">{label} ({items.length})</h2>
            <div className="space-y-2">
              {items.map((c) => {
                const content = JSON.parse(c.content_json);
                return (
                  <div key={c.id} className={`border rounded p-3 ${c.status === "rejected" ? "opacity-50" : ""}`}>
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-sm">{c.title}</span>
                        <span className={`text-xs px-1.5 py-0.5 rounded ${STATUS_COLORS[c.status]}`}>{c.status}</span>
                        <span className="text-xs text-gray-400">{c.source_status}</span>
                      </div>
                      <div className="flex gap-1">
                        {c.status === "pending" && (
                          <>
                            <button onClick={() => handleApprove(c.id)} className="text-xs bg-green-600 text-white px-2 py-1 rounded hover:bg-green-700">确认</button>
                            <button onClick={() => handleReject(c.id)} className="text-xs border border-red-300 text-red-600 px-2 py-1 rounded hover:bg-red-50">拒绝</button>
                          </>
                        )}
                        {c.status === "applied" && (
                          <button onClick={() => handleUndo(c.id)} className="text-xs text-orange-600 hover:underline">撤销</button>
                        )}
                      </div>
                    </div>
                    {/* Content preview */}
                    <div className="text-xs text-gray-600 space-y-0.5">
                      {Object.entries(content).slice(0, 4).map(([k, v]) => v ? (
                        <div key={k}><strong>{k}:</strong> {String(v).slice(0, 100)}</div>
                      ) : null)}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        );
      })}

      {candidates.length > 0 && pending.length === 0 && applied.length === 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded p-3 text-sm text-yellow-800">
          所有候选项已处理。已确认的项目请点击「应用到圣经」写入正式数据。
        </div>
      )}
    </div>
  );
}
