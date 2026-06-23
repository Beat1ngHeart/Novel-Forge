"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { api, type ChapterDraft, type DraftVersion } from "@/lib/api";

const VERSION_LABELS: Record<string, { label: string; color: string }> = {
  ai_draft: { label: "AI 草稿", color: "bg-blue-100 text-blue-800" },
  ai_rewrite: { label: "AI 改写", color: "bg-purple-100 text-purple-800" },
  user_edit: { label: "用户编辑", color: "bg-green-100 text-green-800" },
  final: { label: "正式稿", color: "bg-yellow-100 text-yellow-800" },
  discarded: { label: "已废弃", color: "bg-gray-100 text-gray-500" },
};

export default function DraftPage() {
  const { id: projectId, planId } = useParams() as { id: string; planId: string };
  const [draft, setDraft] = useState<ChapterDraft | null>(null);
  const [versions, setVersions] = useState<DraftVersion[]>([]);
  const [bodyText, setBodyText] = useState("");
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [saving, setSaving] = useState(false);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [error, setError] = useState<string | null>(null);
  const [showVersions, setShowVersions] = useState(false);
  const [showRewrite, setShowRewrite] = useState(false);
  const [selectedText, setSelectedText] = useState("");
  const [rewriteInstruction, setRewriteInstruction] = useState("");
  const [rewriteMode, setRewriteMode] = useState<"rewrite" | "expand" | "compress" | "tone">("rewrite");
  const [autoSaveStatus, setAutoSaveStatus] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [showSearch, setShowSearch] = useState(false);
  const [searchText, setSearchText] = useState("");
  const [replaceText, setReplaceText] = useState("");
  const [fullscreen, setFullscreen] = useState(false);
  const [showDiff, setShowDiff] = useState<{ a: string; b: string } | null>(null);
  const [diffResult, setDiffResult] = useState<Record<string, unknown> | null>(null);

  const autoSaveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const textRef = useRef<HTMLTextAreaElement>(null);

  const loadDraft = useCallback(async () => {
    try {
      const drafts = await api.listDrafts(projectId, planId);
      if (drafts.length > 0) {
        const d = drafts[0];
        setDraft(d);
        setBodyText(d.body_text);
      }
    } catch {}
    setLoading(false);
  }, [projectId, planId]);

  const loadVersions = useCallback(async () => {
    if (!draft) return;
    try {
      const v = await api.listDraftVersions(projectId, draft.id);
      setVersions(v);
    } catch {}
  }, [projectId, draft]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadDraft();
  }, [loadDraft]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadVersions();
  }, [loadVersions]);

  // Auto-save
  useEffect(() => {
    if (!draft || bodyText === draft.body_text) return;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setAutoSaveStatus("idle");
    if (autoSaveTimer.current) clearTimeout(autoSaveTimer.current);
    autoSaveTimer.current = setTimeout(async () => {
      setAutoSaveStatus("saving");
      try {
        await api.saveDraftVersion(projectId, draft.id, bodyText, "user_edit");
        setAutoSaveStatus("saved");
        setTimeout(() => setAutoSaveStatus("idle"), 2000);
      } catch {
        setAutoSaveStatus("error");
      }
    }, 3000);
    return () => {
      if (autoSaveTimer.current) clearTimeout(autoSaveTimer.current);
    };
  }, [bodyText, draft, projectId]);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const d = await api.generateDraft(projectId, planId);
      setDraft(d);
      setBodyText(d.body_text);
      loadVersions();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "生成失败");
    }
    setGenerating(false);
  };

  const handleSave = async () => {
    if (!draft) return;
    setSaving(true);
    try {
      await api.saveDraftVersion(projectId, draft.id, bodyText, "user_edit");
      setAutoSaveStatus("saved");
      loadVersions();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "保存失败");
    }
    setSaving(false);
  };

  const handleMarkFinal = async (versionId: string) => {
    await api.markDraftFinal(projectId, versionId);
    loadVersions();
  };

  const handleRestore = async (versionId: string) => {
    await api.restoreDraftVersion(projectId, versionId);
    loadDraft();
    loadVersions();
  };

  const handleRewrite = async () => {
    if (!draft || !selectedText) return;
    try {
      await api.aiRewrite(projectId, draft.id, selectedText, rewriteInstruction, rewriteMode);
      loadDraft();
      loadVersions();
      setShowRewrite(false);
      setSelectedText("");
      setRewriteInstruction("");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "重写失败");
    }
  };

  const handleSearchReplace = () => {
    if (!searchText) return;
    const newText = bodyText.replaceAll(searchText, replaceText);
    setBodyText(newText);
    setShowSearch(false);
    setSearchText("");
    setReplaceText("");
  };

  const handleDiff = async (aId: string, bId: string) => {
    try {
      const result = await api.diffDraftVersions(projectId, aId, bId);
      setDiffResult(result);
      setShowDiff({ a: aId, b: bId });
    } catch {}
  };

  const handleTextSelect = () => {
    const el = textRef.current;
    if (!el) return;
    const start = el.selectionStart;
    const end = el.selectionEnd;
    if (start !== end) {
      setSelectedText(bodyText.substring(start, end));
      setShowRewrite(true);
    }
  };

  const wordCount = bodyText.length;

  if (loading) return <p className="text-gray-400 p-6">加载中...</p>;

  return (
    <div className={`space-y-4 ${fullscreen ? "fixed inset-0 z-50 bg-gray-50 p-6 overflow-auto" : "max-w-5xl"}`}>
      {!fullscreen && (
        <Link href={`/projects/${projectId}/rhythm/${planId}/plans`} className="text-blue-600 hover:underline text-sm">
          &larr; 返回策划方案
        </Link>
      )}

      {/* Toolbar */}
      <div className="flex items-center justify-between bg-white border rounded-lg p-3">
        <div className="flex items-center gap-3">
          <h1 className="font-semibold">正文编辑</h1>
          <span className="text-xs text-gray-500">{wordCount} 字</span>
          {autoSaveStatus === "saving" && <span className="text-xs text-blue-500">保存中...</span>}
          {autoSaveStatus === "saved" && <span className="text-xs text-green-500">已保存</span>}
          {autoSaveStatus === "error" && <span className="text-xs text-red-500">保存失败</span>}
          {draft?.status && (
            <span className={`text-xs px-1.5 py-0.5 rounded ${VERSION_LABELS[draft.status]?.color || "bg-gray-100"}`}>
              {VERSION_LABELS[draft.status]?.label || draft.status}
            </span>
          )}
        </div>
        <div className="flex gap-2">
          <button onClick={() => setShowSearch(!showSearch)} className="text-xs border px-2 py-1 rounded hover:bg-gray-50">搜索替换</button>
          <button onClick={() => setShowVersions(!showVersions)} className="text-xs border px-2 py-1 rounded hover:bg-gray-50">版本历史</button>
          <button onClick={() => setFullscreen(!fullscreen)} className="text-xs border px-2 py-1 rounded hover:bg-gray-50">{fullscreen ? "退出全屏" : "全屏"}</button>
          <button onClick={handleSave} disabled={saving} className="text-xs bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700 disabled:opacity-50">保存</button>
        </div>
      </div>

      {/* Search/Replace */}
      {showSearch && (
        <div className="bg-white border rounded-lg p-4 flex gap-3 items-end">
          <div>
            <label className="text-xs text-gray-500">搜索</label>
            <input className="border rounded px-2 py-1 text-sm w-48" value={searchText} onChange={(e) => setSearchText(e.target.value)} />
          </div>
          <div>
            <label className="text-xs text-gray-500">替换</label>
            <input className="border rounded px-2 py-1 text-sm w-48" value={replaceText} onChange={(e) => setReplaceText(e.target.value)} />
          </div>
          <button onClick={handleSearchReplace} className="text-xs bg-blue-600 text-white px-3 py-1.5 rounded">全部替换</button>
        </div>
      )}

      {/* AI Rewrite Panel */}
      {showRewrite && selectedText && (
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 space-y-3">
          <h3 className="text-sm font-semibold">AI 改写选中内容</h3>
          <p className="text-xs text-gray-600 bg-white rounded p-2 max-h-20 overflow-auto">{selectedText}</p>
          <div className="flex gap-2">
            {(["rewrite", "expand", "compress", "tone"] as const).map((m) => (
              <button key={m} onClick={() => setRewriteMode(m)}
                className={`text-xs px-2 py-1 rounded ${rewriteMode === m ? "bg-purple-600 text-white" : "border"}`}>
                {m === "rewrite" ? "改写" : m === "expand" ? "扩写" : m === "compress" ? "压缩" : "调整语气"}
              </button>
            ))}
          </div>
          <input className="w-full border rounded px-2 py-1 text-sm" placeholder="改写指令..."
            value={rewriteInstruction} onChange={(e) => setRewriteInstruction(e.target.value)} />
          <div className="flex gap-2">
            <button onClick={handleRewrite} className="text-xs bg-purple-600 text-white px-3 py-1 rounded">执行改写</button>
            <button onClick={() => setShowRewrite(false)} className="text-xs border px-3 py-1 rounded">取消</button>
          </div>
        </div>
      )}

      {/* Editor */}
      <div className="bg-white border rounded-lg">
        <textarea
          ref={textRef}
          className="w-full min-h-[500px] p-6 text-sm leading-relaxed resize-y focus:outline-none"
          value={bodyText}
          onChange={(e) => setBodyText(e.target.value)}
          onMouseUp={handleTextSelect}
          placeholder="正文内容..."
        />
      </div>

      {/* Version History */}
      {showVersions && (
        <div className="bg-white border rounded-lg p-5 space-y-3">
          <h2 className="font-semibold">版本历史</h2>
          {versions.length === 0 && <p className="text-sm text-gray-400">暂无版本记录</p>}
          <div className="space-y-2 max-h-64 overflow-auto">
            {versions.map((v) => {
              const label = VERSION_LABELS[v.version_type] || VERSION_LABELS.user_edit;
              return (
                <div key={v.id} className="flex items-center justify-between border rounded p-3 text-sm">
                  <div className="flex items-center gap-3">
                    <span className={`text-xs px-1.5 py-0.5 rounded ${label.color}`}>{label.label}</span>
                    <span className="text-xs text-gray-500">{v.word_count} 字</span>
                    <span className="text-xs text-gray-400">{new Date(v.created_at).toLocaleString("zh-CN")}</span>
                    {v.is_final && <span className="text-xs bg-yellow-200 px-1.5 py-0.5 rounded">正式稿</span>}
                  </div>
                  <div className="flex gap-2">
                    <button onClick={() => handleRestore(v.id)} className="text-xs text-blue-600 hover:underline">恢复</button>
                    {!v.is_final && (
                      <button onClick={() => handleMarkFinal(v.id)} className="text-xs text-green-600 hover:underline">标记正式</button>
                    )}
                    {versions.length > 1 && (
                      <button
                        onClick={() => {
                          const other = versions.find((x) => x.id !== v.id);
                          if (other) handleDiff(v.id, other.id);
                        }}
                        className="text-xs text-gray-500 hover:underline"
                      >
                        比较
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Diff View */}
      {showDiff && diffResult && (
        <div className="bg-white border rounded-lg p-5 space-y-3">
          <h2 className="font-semibold">版本比较</h2>
          <p className="text-sm text-gray-500">
            新增 {(diffResult as Record<string, unknown>).additions as number} 行 · 删除{" "}
            {(diffResult as Record<string, unknown>).deletions as number} 行
          </p>
          <div className="text-xs font-mono bg-gray-50 rounded p-3 max-h-48 overflow-auto">
            {((diffResult as Record<string, unknown>).changes as { type: string; content: string }[])?.map(
              (c, i) => (
                <div key={i} className={c.type === "add" ? "text-green-700" : "text-red-700"}>
                  {c.type === "add" ? "+" : "-"} {c.content}
                </div>
              )
            )}
          </div>
        </div>
      )}

      {/* Info */}
      {draft && (
        <div className="text-xs text-gray-400 flex gap-4">
          <span>参数: {draft.person} · {draft.pov} · 对话{draft.dialogue_density} · 节奏{draft.pacing}</span>
          {draft.chapter_summary && <span>摘要: {draft.chapter_summary.slice(0, 60)}...</span>}
        </div>
      )}
    </div>
  );
}
