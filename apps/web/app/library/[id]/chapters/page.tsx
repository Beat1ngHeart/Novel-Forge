"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api, type Chapter } from "@/lib/api";

export default function ChaptersPage() {
  const { id: docId } = useParams() as { id: string };
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [editVolume, setEditVolume] = useState("");

  const load = () => {
    setLoading(true);
    api
      .listChapters(docId)
      .then(setChapters)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- standard data-fetching pattern
    setLoading(true);
    api
      .listChapters(docId)
      .then(setChapters)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [docId]);

  const handleRename = async (chId: string) => {
    if (!editTitle.trim()) return;
    await api.updateChapter(docId, chId, { title: editTitle });
    setEditingId(null);
    load();
  };

  const handleVolumeChange = async (chId: string) => {
    await api.updateChapter(docId, chId, { volume_name: editVolume });
    setEditingId(null);
    load();
  };

  const handleMarkSource = async (chId: string, source: string) => {
    await api.updateChapter(docId, chId, { parse_source: source });
    load();
  };

  const handleDelete = async (chId: string, title: string) => {
    if (!confirm(`确定删除「${title}」？`)) return;
    await api.deleteChapter(docId, chId);
    load();
  };

  if (loading) return <p className="text-gray-400 p-6">加载中...</p>;
  if (error) return <p className="text-red-500 p-6">{error}</p>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <Link href={`/library/${docId}`} className="text-blue-600 hover:underline text-sm">
            &larr; 返回文件详情
          </Link>
          <h1 className="text-2xl font-bold mt-2">章节列表</h1>
          <p className="text-sm text-gray-500">{chapters.length} 个章节</p>
        </div>
        <div className="flex gap-2">
          <Link
            href={`/library/${docId}/chapters/batch`}
            className="bg-orange-600 text-white px-4 py-2 rounded-md text-sm hover:bg-orange-700"
          >
            批量分析
          </Link>
          <Link
            href={`/library/${docId}/parse`}
            className="bg-purple-600 text-white px-4 py-2 rounded-md text-sm hover:bg-purple-700"
          >
            重新解析
          </Link>
        </div>
      </div>

      {chapters.length === 0 && (
        <div className="bg-white border rounded-lg p-12 text-center text-gray-400">
          <p className="text-lg mb-2">暂无章节</p>
          <Link href={`/library/${docId}/parse`} className="text-blue-600 hover:underline text-sm">
            前往解析页面
          </Link>
        </div>
      )}

      <div className="space-y-2">
        {chapters.map((ch) => (
          <div key={ch.id} className="bg-white border rounded-lg p-4">
            {editingId === ch.id ? (
              <div className="space-y-3">
                <div className="flex gap-3">
                  <input
                    className="border rounded px-2 py-1.5 text-sm flex-1"
                    value={editTitle}
                    onChange={(e) => setEditTitle(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleRename(ch.id)}
                  />
                  <button
                    onClick={() => handleRename(ch.id)}
                    className="bg-blue-600 text-white px-3 py-1.5 rounded text-sm"
                  >
                    保存标题
                  </button>
                  <button onClick={() => setEditingId(null)} className="border px-3 py-1.5 rounded text-sm">
                    取消
                  </button>
                </div>
                <div className="flex gap-3 items-center">
                  <label className="text-xs text-gray-500">卷名：</label>
                  <input
                    className="border rounded px-2 py-1.5 text-sm w-40"
                    value={editVolume}
                    onChange={(e) => setEditVolume(e.target.value)}
                  />
                  <button
                    onClick={() => handleVolumeChange(ch.id)}
                    className="text-blue-600 text-sm hover:underline"
                  >
                    更新卷名
                  </button>
                </div>
                <div className="flex gap-2">
                  <span className="text-xs text-gray-500">标记为：</span>
                  {["序章", "番外", "尾声"].map((label) => (
                    <button
                      key={label}
                      onClick={() => {
                        setEditTitle(label);
                        handleRename(ch.id);
                        handleMarkSource(ch.id, "manual");
                      }}
                      className="text-xs border px-2 py-0.5 rounded hover:bg-gray-50"
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-400 w-8">{ch.chapter_index}</span>
                    <span className="font-medium truncate">{ch.title}</span>
                    {ch.volume_name && (
                      <span className="text-xs bg-blue-100 text-blue-800 px-1.5 py-0.5 rounded">
                        {ch.volume_name}
                      </span>
                    )}
                    {ch.parse_source === "manual" && (
                      <span className="text-xs bg-yellow-100 text-yellow-800 px-1.5 py-0.5 rounded">
                        手动
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-400 mt-1 ml-10">{ch.word_count} 字</p>
                </div>
                <div className="flex gap-2 shrink-0">
                  <Link
                    href={`/library/${docId}/chapters/${ch.id}/analyze`}
                    className="text-purple-600 text-sm hover:underline"
                  >
                    分析
                  </Link>
                  <button
                    onClick={() => {
                      setEditingId(ch.id);
                      setEditTitle(ch.title);
                      setEditVolume(ch.volume_name);
                    }}
                    className="text-blue-600 text-sm hover:underline"
                  >
                    编辑
                  </button>
                  <button
                    onClick={() => handleDelete(ch.id, ch.title)}
                    className="text-red-500 text-sm hover:underline"
                  >
                    删除
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
