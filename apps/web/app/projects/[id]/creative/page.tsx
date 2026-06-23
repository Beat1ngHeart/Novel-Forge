"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { api, type CreativeDirection, type CreativeSession } from "@/lib/api";

const STATUS_COLORS: Record<string, string> = {
  draft: "bg-gray-100 text-gray-700",
  adopted: "bg-green-100 text-green-800",
  rejected: "bg-red-100 text-red-800",
  completed: "bg-blue-100 text-blue-800",
};

function DirectionCard({
  d,
  onAccept,
  onReject,
  onEdit,
}: {
  d: CreativeDirection;
  onAccept: () => void;
  onReject: () => void;
  onEdit: (field: string, value: string) => void;
}) {
  const [editing, setEditing] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");

  const fields = [
    { key: "one_line_hook", label: "一句话卖点" },
    { key: "core_reader_promise", label: "核心读者承诺" },
    { key: "protagonist_identity", label: "主角身份" },
    { key: "protagonist_goal", label: "主角目标" },
    { key: "core_ability", label: "核心能力" },
    { key: "ability_cost", label: "能力代价" },
    { key: "core_conflict", label: "核心矛盾" },
    { key: "world_mystery", label: "世界谜团" },
    { key: "growth_cycle", label: "成长循环" },
    { key: "resource_cycle", label: "资源循环" },
    { key: "payoff_cycle", label: "爽点循环" },
    { key: "long_term_suspense", label: "长期悬念" },
    { key: "difference_from_tropes", label: "与套路差异" },
    { key: "homogenization_risk", label: "同质化风险" },
    { key: "sustainable_length", label: "可持续篇幅" },
    { key: "potential_collapse_point", label: "潜在崩坏位置" },
  ];

  return (
    <div className={`border rounded-lg p-4 flex-1 min-w-0 ${d.status === "adopted" ? "border-green-500 bg-green-50" : d.status === "rejected" ? "border-red-300 opacity-60" : "border-gray-200 bg-white"}`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="font-semibold">方向 {d.direction_index + 1}</span>
          <span className={`text-xs px-1.5 py-0.5 rounded ${STATUS_COLORS[d.status]}`}>{d.status}</span>
        </div>
        {d.status === "draft" && (
          <div className="flex gap-1">
            <button onClick={onAccept} className="text-xs bg-green-600 text-white px-2 py-1 rounded hover:bg-green-700">采用</button>
            <button onClick={onReject} className="text-xs border border-red-300 text-red-600 px-2 py-1 rounded hover:bg-red-50">拒绝</button>
          </div>
        )}
      </div>

      <div className="space-y-2">
        {fields.map(({ key, label }) => {
          const value = (d as unknown as Record<string, string>)[key];
          if (!value) return null;
          return (
            <div key={key}>
              <dt className="text-xs text-gray-500">{label}</dt>
              {editing === key ? (
                <div className="flex gap-2 mt-1">
                  <input
                    className="flex-1 border rounded px-2 py-1 text-sm"
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") { onEdit(key, editValue); setEditing(null); }
                      if (e.key === "Escape") setEditing(null);
                    }}
                  />
                  <button onClick={() => { onEdit(key, editValue); setEditing(null); }} className="text-xs bg-blue-600 text-white px-2 py-1 rounded">保存</button>
                </div>
              ) : (
                <dd
                  className="text-sm cursor-pointer hover:bg-gray-50 rounded px-1 -mx-1"
                  onClick={() => { if (d.status === "draft") { setEditing(key); setEditValue(value); } }}
                  title={d.status === "draft" ? "点击编辑" : ""}
                >
                  {value}
                </dd>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function CreativePage() {
  const { id: projectId } = useParams() as { id: string };
  const [sessions, setSessions] = useState<CreativeSession[]>([]);
  const [directions, setDirections] = useState<CreativeDirection[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    one_line_idea: "",
    genre: "玄幻",
    target_platform: "",
    target_reader: "",
    expected_length: "200万字",
    preferred_pacing: "中速",
    forbidden_content: "",
    gene_tags: "",
  });

  const loadSessions = useCallback(async () => {
    try {
      const s = await api.listCreativeSessions(projectId);
      setSessions(s);
      if (s.length > 0 && !activeSessionId) {
        setActiveSessionId(s[0].id);
      }
    } catch {}
  }, [projectId, activeSessionId]);

  const loadDirections = useCallback(async () => {
    if (!activeSessionId) return;
    try {
      const d = await api.listSessionDirections(projectId, activeSessionId);
      setDirections(d);
    } catch {}
  }, [projectId, activeSessionId]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadSessions().finally(() => setLoading(false));
  }, [loadSessions]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadDirections();
  }, [loadDirections]);

  const handleGenerate = async () => {
    if (!form.one_line_idea.trim()) return setError("请输入创意");
    setGenerating(true);
    setError(null);
    try {
      const dirs = await api.generateDirections(projectId, form);
      setDirections(dirs);
      if (dirs.length > 0) setActiveSessionId(dirs[0].session_id);
      setShowForm(false);
      loadSessions();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "生成失败");
    }
    setGenerating(false);
  };

  const handleAccept = async (directionId: string) => {
    await api.acceptDirection(projectId, directionId);
    loadDirections();
    loadSessions();
  };

  const handleReject = async (directionId: string) => {
    await api.rejectDirection(projectId, directionId);
    loadDirections();
  };

  const handleEdit = async (directionId: string, field: string, value: string) => {
    await api.editDirection(projectId, directionId, { [field]: value });
    loadDirections();
  };

  if (loading) return <p className="text-gray-400 p-6">加载中...</p>;

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="flex items-center justify-between">
        <div>
          <Link href={`/projects/${projectId}`} className="text-blue-600 hover:underline text-sm">&larr; 返回项目</Link>
          <h1 className="text-2xl font-bold mt-2">创意方向</h1>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700"
        >
          {showForm ? "收起" : "生成新方向"}
        </button>
      </div>

      {error && <div className="bg-red-50 border border-red-200 rounded p-3 text-sm text-red-700">{error}</div>}

      {/* Input Form */}
      {showForm && (
        <div className="bg-white border rounded-lg p-5 space-y-4">
          <h2 className="font-semibold">创意输入</h2>
          <div>
            <label className="block text-sm font-medium mb-1">一句话创意 *</label>
            <textarea
              className="w-full border rounded px-3 py-2 text-sm h-20"
              value={form.one_line_idea}
              onChange={(e) => setForm({ ...form, one_line_idea: e.target.value })}
              placeholder="描述你的小说创意..."
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-gray-500 mb-1">题材</label>
              <select className="w-full border rounded px-2 py-1.5 text-sm" value={form.genre} onChange={(e) => setForm({ ...form, genre: e.target.value })}>
                {["玄幻","仙侠","都市","科幻","历史","游戏","悬疑","言情"].map(g => <option key={g}>{g}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">目标平台</label>
              <input className="w-full border rounded px-2 py-1.5 text-sm" value={form.target_platform} onChange={(e) => setForm({ ...form, target_platform: e.target.value })} placeholder="起点中文网" />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">目标读者</label>
              <input className="w-full border rounded px-2 py-1.5 text-sm" value={form.target_reader} onChange={(e) => setForm({ ...form, target_reader: e.target.value })} placeholder="18-30岁男性" />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">预计篇幅</label>
              <input className="w-full border rounded px-2 py-1.5 text-sm" value={form.expected_length} onChange={(e) => setForm({ ...form, expected_length: e.target.value })} />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">偏好节奏</label>
              <input className="w-full border rounded px-2 py-1.5 text-sm" value={form.preferred_pacing} onChange={(e) => setForm({ ...form, preferred_pacing: e.target.value })} />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">禁止内容</label>
              <input className="w-full border rounded px-2 py-1.5 text-sm" value={form.forbidden_content} onChange={(e) => setForm({ ...form, forbidden_content: e.target.value })} placeholder="不写后宫" />
            </div>
          </div>
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="bg-purple-600 text-white px-5 py-2 rounded text-sm hover:bg-purple-700 disabled:opacity-50"
          >
            {generating ? "生成中..." : "生成 3 个方向"}
          </button>
        </div>
      )}

      {/* Session Selector */}
      {sessions.length > 1 && (
        <div className="flex gap-2 flex-wrap">
          {sessions.map((s, i) => (
            <button
              key={s.id}
              onClick={() => { setActiveSessionId(s.id); setDirections([]); }}
              className={`text-xs px-3 py-1.5 rounded border ${activeSessionId === s.id ? "bg-blue-100 border-blue-300" : "hover:bg-gray-50"}`}
            >
              会话 {i + 1} — {s.one_line_idea.slice(0, 20)}...
              <span className={`ml-1 ${STATUS_COLORS[s.status]}`}>{s.status}</span>
            </button>
          ))}
        </div>
      )}

      {/* Directions */}
      {directions.length === 0 && !showForm && (
        <div className="bg-white border rounded-lg p-12 text-center text-gray-400">
          <p className="text-lg mb-2">暂无创意方向</p>
          <p className="text-sm">点击「生成新方向」开始</p>
        </div>
      )}

      {directions.length > 0 && (
        <div className="flex gap-4 overflow-x-auto pb-2">
          {directions.sort((a, b) => a.direction_index - b.direction_index).map((d) => (
            <DirectionCard
              key={d.id}
              d={d}
              onAccept={() => handleAccept(d.id)}
              onReject={() => handleReject(d.id)}
              onEdit={(field, value) => handleEdit(d.id, field, value)}
            />
          ))}
        </div>
      )}

      {/* Info */}
      {directions.some(d => d.status === "adopted") && (
        <div className="bg-green-50 border border-green-200 rounded p-3 text-sm text-green-800">
          已采用的方向将作为项目创意基础。未采用的方向已自动标记为拒绝。
        </div>
      )}
    </div>
  );
}
