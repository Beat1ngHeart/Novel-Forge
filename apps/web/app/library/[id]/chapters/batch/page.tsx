"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import {
  api,
  type AnalysisTask,
  type AnalysisTaskDetail,
  type AnalysisTaskItem,
  type Chapter,
} from "@/lib/api";

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-gray-200 text-gray-700",
  running: "bg-blue-100 text-blue-800",
  succeeded: "bg-green-100 text-green-800",
  failed: "bg-red-100 text-red-800",
  skipped: "bg-yellow-100 text-yellow-800",
  cancelled: "bg-gray-300 text-gray-600",
};

function ProgressBar({ percent }: { percent: number }) {
  return (
    <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden">
      <div
        className="h-full bg-blue-500 rounded-full transition-all duration-300"
        style={{ width: `${percent}%` }}
      />
    </div>
  );
}

export default function BatchAnalyzePage() {
  const { id: docId } = useParams() as { id: string };
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [task, setTask] = useState<AnalysisTaskDetail | null>(null);
  const [tasks, setTasks] = useState<AnalysisTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [polling, setPolling] = useState(false);

  const loadChapters = useCallback(async () => {
    setLoading(true);
    try {
      const [chs, tsks] = await Promise.all([
        api.listChapters(docId),
        api.listTasks(docId),
      ]);
      setChapters(chs);
      setTasks(tsks);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "加载失败");
    }
    setLoading(false);
  }, [docId]);

  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { loadChapters(); }, [loadChapters]);

  // Poll active task
  useEffect(() => {
    if (!task || !["pending", "running"].includes(task.status)) return;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setPolling(true);
    const interval = setInterval(async () => {
      try {
        const updated = await api.getTask(task.id);
        setTask(updated);
        if (!["pending", "running"].includes(updated.status)) {
          clearInterval(interval);
          setPolling(false);
          loadChapters();
        }
      } catch { /* ignore poll errors */ }
    }, 1000);
    return () => { clearInterval(interval); setPolling(false); };
  }, [task, loadChapters]);

  const toggleSelect = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const selectAll = () => setSelected(new Set(chapters.map((c) => c.id)));
  const clearSelection = () => setSelected(new Set());

  const handleCreate = async () => {
    if (selected.size === 0) return;
    setCreating(true);
    setError(null);
    try {
      const t = await api.createTask([...selected]);
      const detail = await api.getTask(t.id);
      setTask(detail);
      setSelected(new Set());
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "创建失败");
    }
    setCreating(false);
  };

  const handleCancel = async () => {
    if (!task) return;
    try {
      await api.cancelTask(task.id);
      const updated = await api.getTask(task.id);
      setTask(updated);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "取消失败");
    }
  };

  const handleRetryFailed = async () => {
    if (!task) return;
    const failedIds = task.items.filter((i) => i.status === "failed").map((i) => i.id);
    if (failedIds.length === 0) return;
    try {
      await api.retryTask(task.id, failedIds);
      const updated = await api.getTask(task.id);
      setTask(updated);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "重试失败");
    }
  };

  const handleViewTask = async (taskId: string) => {
    try {
      const detail = await api.getTask(taskId);
      setTask(detail);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "加载失败");
    }
  };

  if (loading) return <p className="text-gray-400 p-6">加载中...</p>;

  return (
    <div className="space-y-6 max-w-4xl">
      <Link href={`/library/${docId}/chapters`} className="text-blue-600 hover:underline text-sm">
        &larr; 返回章节列表
      </Link>

      <h1 className="text-2xl font-bold">批量分析</h1>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded p-3 text-sm text-red-700">{error}</div>
      )}

      {/* Chapter Selection */}
      {!task && (
        <div className="bg-white border rounded-lg p-5">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-semibold">选择章节 ({selected.size}/{chapters.length})</h2>
            <div className="flex gap-2">
              <button onClick={selectAll} className="text-blue-600 text-sm hover:underline">全选</button>
              <button onClick={clearSelection} className="text-gray-500 text-sm hover:underline">清除</button>
            </div>
          </div>
          <div className="space-y-1 max-h-64 overflow-auto">
            {chapters.map((ch) => (
              <label
                key={ch.id}
                className={`flex items-center gap-3 px-3 py-2 rounded cursor-pointer hover:bg-gray-50 ${
                  selected.has(ch.id) ? "bg-blue-50" : ""
                }`}
              >
                <input
                  type="checkbox"
                  checked={selected.has(ch.id)}
                  onChange={() => toggleSelect(ch.id)}
                />
                <span className="text-xs text-gray-400 w-8">{ch.chapter_index}</span>
                <span className="flex-1 text-sm truncate">{ch.title}</span>
                <span className="text-xs text-gray-400">{ch.word_count} 字</span>
              </label>
            ))}
          </div>
          <div className="mt-3 flex gap-3">
            <button
              onClick={handleCreate}
              disabled={creating || selected.size === 0}
              className="bg-purple-600 text-white px-5 py-2 rounded text-sm hover:bg-purple-700 disabled:opacity-50"
            >
              {creating ? "创建中..." : `开始分析 ${selected.size} 章`}
            </button>
          </div>
        </div>
      )}

      {/* Task Progress */}
      {task && (
        <div className="bg-white border rounded-lg p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">
              任务进度
              <span className={`ml-2 text-xs px-2 py-0.5 rounded ${STATUS_COLORS[task.status]}`}>
                {task.status}
              </span>
              {polling && <span className="ml-2 text-xs text-blue-500 animate-pulse">监控中...</span>}
            </h2>
            <div className="flex gap-2">
              {["pending", "running"].includes(task.status) && (
                <button onClick={handleCancel} className="text-red-500 text-sm border border-red-300 px-3 py-1 rounded hover:bg-red-50">
                  取消任务
                </button>
              )}
              {task.status === "failed" && (
                <button onClick={handleRetryFailed} className="text-blue-600 text-sm border border-blue-300 px-3 py-1 rounded hover:bg-blue-50">
                  重试失败项
                </button>
              )}
              <button onClick={() => { setTask(null); loadChapters(); }} className="text-gray-500 text-sm hover:underline">
                返回选择
              </button>
            </div>
          </div>

          <ProgressBar percent={task.progress_percent} />

          <div className="flex gap-6 text-sm">
            <span>总计: <strong>{task.total_items}</strong></span>
            <span className="text-green-600">成功: <strong>{task.completed_items}</strong></span>
            <span className="text-red-600">失败: <strong>{task.failed_items}</strong></span>
            <span className="text-yellow-600">跳过: <strong>{task.skipped_items}</strong></span>
            <span className="text-gray-400">{task.progress_percent}%</span>
          </div>

          {task.summary && (
            <div className="text-sm text-gray-600 bg-gray-50 rounded p-3">{task.summary}</div>
          )}

          {/* Item list */}
          <div className="space-y-1 max-h-80 overflow-auto">
            {task.items.map((item: AnalysisTaskItem) => (
              <div key={item.id} className="flex items-center gap-3 px-3 py-2 border rounded text-sm">
                <span className={`w-2 h-2 rounded-full ${STATUS_COLORS[item.status]?.split(" ")[0] || "bg-gray-300"}`} />
                <span className="text-xs text-gray-400 w-8">{item.chapter_index}</span>
                <span className="flex-1 truncate">{item.chapter_title}</span>
                <span className={`text-xs px-1.5 py-0.5 rounded ${STATUS_COLORS[item.status]}`}>
                  {item.status}
                </span>
                {item.error_message && (
                  <span className="text-xs text-red-500 max-w-32 truncate">{item.error_message}</span>
                )}
                {item.analysis_id && (
                  <Link
                    href={`/library/${docId}/chapters/${item.chapter_id}/analyze`}
                    className="text-xs text-blue-600 hover:underline"
                  >
                    查看
                  </Link>
                )}
                {item.status === "failed" && (
                  <button
                    onClick={async () => {
                      try {
                        await api.retryTask(task.id, [item.id]);
                        const updated = await api.getTask(task.id);
                        setTask(updated);
                      } catch {}
                    }}
                    className="text-xs text-orange-600 hover:underline"
                  >
                    重试
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Task History */}
      {tasks.length > 0 && !task && (
        <div className="bg-white border rounded-lg p-5">
          <h2 className="font-semibold mb-3">任务历史</h2>
          <div className="space-y-2">
            {tasks.map((t) => (
              <button
                key={t.id}
                onClick={() => handleViewTask(t.id)}
                className="w-full text-left flex items-center justify-between border rounded p-3 hover:bg-gray-50"
              >
                <div className="flex items-center gap-3">
                  <span className={`text-xs px-1.5 py-0.5 rounded ${STATUS_COLORS[t.status]}`}>{t.status}</span>
                  <span className="text-sm">{t.total_items} 章</span>
                  <span className="text-xs text-gray-400">{new Date(t.created_at).toLocaleString("zh-CN")}</span>
                </div>
                <span className="text-xs text-gray-400">{t.progress_percent}%</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
