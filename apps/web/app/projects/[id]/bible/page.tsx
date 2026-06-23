"use client";

import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import {
  api,
  type Character,
  type WorldRule,
  type PlotThread,
  type Foreshadowing,
} from "@/lib/api";

type Tab = "characters" | "world-rules" | "plot-threads" | "foreshadowings";

const SOURCE_LABELS: Record<string, { label: string; color: string }> = {
  ai_suggestion: { label: "AI 建议", color: "bg-blue-100 text-blue-800" },
  user_confirmed: { label: "用户确认", color: "bg-green-100 text-green-800" },
  text_fact: { label: "文本事实", color: "bg-teal-100 text-teal-800" },
  deprecated: { label: "已废弃", color: "bg-gray-200 text-gray-500 line-through" },
};

const FORESHADOW_STATUS: Record<string, string> = {
  planted: "已埋设",
  progressing: "推进中",
  paid_off: "已回收",
  abandoned: "已放弃",
};

function SourceBadge({ status }: { status: string }) {
  const s = SOURCE_LABELS[status] || SOURCE_LABELS.user_confirmed;
  return <span className={`text-xs px-1.5 py-0.5 rounded ${s.color}`}>{s.label}</span>;
}

export default function BiblePage() {
  const { id: projectId } = useParams() as { id: string };
  const [tab, setTab] = useState<Tab>("characters");
  const [characters, setCharacters] = useState<Character[]>([]);
  const [worldRules, setWorldRules] = useState<WorldRule[]>([]);
  const [plotThreads, setPlotThreads] = useState<PlotThread[]>([]);
  const [foreshadowings, setForeshadowings] = useState<Foreshadowing[]>([]);
  const [loading, setLoading] = useState(true);

  const loadAll = useCallback(async () => {
    setLoading(true);
    try {
      const [c, w, p, f] = await Promise.all([
        api.listCharacters(projectId),
        api.listWorldRules(projectId),
        api.listPlotThreads(projectId),
        api.listForeshadowings(projectId),
      ]);
      setCharacters(c);
      setWorldRules(w);
      setPlotThreads(p);
      setForeshadowings(f);
    } catch {}
    setLoading(false);
  }, [projectId]);

  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { loadAll(); }, [loadAll]);

  const handleDelete = async (type: Tab, id: string, name: string) => {
    if (!confirm(`确定删除「${name}」？`)) return;
    if (type === "characters") await api.deleteCharacter(projectId, id);
    else if (type === "world-rules") await api.deleteWorldRule(projectId, id);
    else if (type === "plot-threads") await api.deletePlotThread(projectId, id);
    else if (type === "foreshadowings") await api.deleteForeshadowing(projectId, id);
    loadAll();
  };

  const handleSourceToggle = async (type: Tab, id: string, current: string) => {
    const next = current === "deprecated" ? "user_confirmed" : "deprecated";
    if (type === "characters") await api.updateCharacter(projectId, id, { source_status: next });
    else if (type === "world-rules") await api.updateWorldRule(projectId, id, { source_status: next });
    else if (type === "plot-threads") await api.updatePlotThread(projectId, id, { source_status: next });
    else if (type === "foreshadowings") await api.updateForeshadowing(projectId, id, { source_status: next });
    loadAll();
  };

  const tabs: { key: Tab; label: string; count: number }[] = [
    { key: "characters", label: "人物", count: characters.length },
    { key: "world-rules", label: "世界规则", count: worldRules.length },
    { key: "plot-threads", label: "剧情线", count: plotThreads.length },
    { key: "foreshadowings", label: "伏笔", count: foreshadowings.length },
  ];

  return (
    <div className="space-y-6 max-w-4xl">
      <h1 className="text-2xl font-bold">小说圣经</h1>

      {/* Tabs */}
      <div className="flex border-b">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              tab === t.key
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            {t.label} ({t.count})
          </button>
        ))}
      </div>

      {loading && <p className="text-gray-400">加载中...</p>}

      {/* Characters Tab */}
      {tab === "characters" && (
        <div className="space-y-3">
          {characters.length === 0 && (
            <p className="text-gray-400 text-center py-8">暂无人物，使用 API 创建。</p>
          )}
          {characters.map((c) => (
            <div key={c.id} className="bg-white border rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold">{c.name}</h3>
                  {c.aliases && <span className="text-xs text-gray-400">({c.aliases})</span>}
                  <SourceBadge status={c.source_status} />
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleSourceToggle("characters", c.id, c.source_status)}
                    className="text-xs text-gray-500 hover:underline"
                  >
                    {c.source_status === "deprecated" ? "恢复" : "废弃"}
                  </button>
                  <button
                    onClick={() => handleDelete("characters", c.id, c.name)}
                    className="text-xs text-red-500 hover:underline"
                  >
                    删除
                  </button>
                </div>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-x-4 gap-y-1 text-xs text-gray-600">
                {c.age && <div><strong>年龄:</strong> {c.age}</div>}
                {c.identity && <div><strong>身份:</strong> {c.identity}</div>}
                {c.current_location && <div><strong>位置:</strong> {c.current_location}</div>}
                {c.personality && <div className="col-span-2"><strong>性格:</strong> {c.personality}</div>}
                {c.desire && <div className="col-span-2"><strong>欲望:</strong> {c.desire}</div>}
                {c.current_goal && <div className="col-span-2"><strong>当前目标:</strong> {c.current_goal}</div>}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* World Rules Tab */}
      {tab === "world-rules" && (
        <div className="space-y-3">
          {worldRules.length === 0 && <p className="text-gray-400 text-center py-8">暂无世界规则。</p>}
          {worldRules.map((r) => (
            <div key={r.id} className="bg-white border rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold">{r.name}</h3>
                  {r.category && <span className="text-xs bg-gray-100 px-1.5 py-0.5 rounded">{r.category}</span>}
                  <SourceBadge status={r.source_status} />
                </div>
                <div className="flex gap-2">
                  <button onClick={() => handleSourceToggle("world-rules", r.id, r.source_status)} className="text-xs text-gray-500 hover:underline">{r.source_status === "deprecated" ? "恢复" : "废弃"}</button>
                  <button onClick={() => handleDelete("world-rules", r.id, r.name)} className="text-xs text-red-500 hover:underline">删除</button>
                </div>
              </div>
              {r.description && <p className="text-sm text-gray-600">{r.description}</p>}
            </div>
          ))}
        </div>
      )}

      {/* Plot Threads Tab */}
      {tab === "plot-threads" && (
        <div className="space-y-3">
          {plotThreads.length === 0 && <p className="text-gray-400 text-center py-8">暂无剧情线。</p>}
          {plotThreads.map((t) => (
            <div key={t.id} className="bg-white border rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold">{t.title}</h3>
                  <span className="text-xs bg-purple-100 text-purple-800 px-1.5 py-0.5 rounded">{t.thread_type}</span>
                  <span className="text-xs bg-gray-100 px-1.5 py-0.5 rounded">{t.current_status}</span>
                  <SourceBadge status={t.source_status} />
                </div>
                <div className="flex gap-2">
                  <button onClick={() => handleSourceToggle("plot-threads", t.id, t.source_status)} className="text-xs text-gray-500 hover:underline">{t.source_status === "deprecated" ? "恢复" : "废弃"}</button>
                  <button onClick={() => handleDelete("plot-threads", t.id, t.title)} className="text-xs text-red-500 hover:underline">删除</button>
                </div>
              </div>
              {t.description && <p className="text-sm text-gray-600">{t.description}</p>}
            </div>
          ))}
        </div>
      )}

      {/* Foreshadowings Tab */}
      {tab === "foreshadowings" && (
        <div className="space-y-3">
          {foreshadowings.length === 0 && <p className="text-gray-400 text-center py-8">暂无伏笔。</p>}
          {foreshadowings.map((f) => (
            <div key={f.id} className="bg-white border rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold text-sm">{f.content}</h3>
                  <span className="text-xs bg-orange-100 text-orange-800 px-1.5 py-0.5 rounded">
                    {FORESHADOW_STATUS[f.status] || f.status}
                  </span>
                  <SourceBadge status={f.source_status} />
                </div>
                <div className="flex gap-2">
                  <button onClick={() => handleSourceToggle("foreshadowings", f.id, f.source_status)} className="text-xs text-gray-500 hover:underline">{f.source_status === "deprecated" ? "恢复" : "废弃"}</button>
                  <button onClick={() => handleDelete("foreshadowings", f.id, f.content)} className="text-xs text-red-500 hover:underline">删除</button>
                </div>
              </div>
              <div className="text-xs text-gray-500 space-y-0.5">
                {f.planted_chapter && <div>埋设: {f.planted_chapter}</div>}
                {f.expected_payoff_range && <div>预期回收: {f.expected_payoff_range}</div>}
                {f.related_characters && <div>关联人物: {f.related_characters}</div>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
