"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, type Document } from "@/lib/api";

const RIGHTS_LABELS: Record<string, { label: string; color: string }> = {
  owned: { label: "自有", color: "bg-green-100 text-green-800" },
  authorized: { label: "已授权", color: "bg-blue-100 text-blue-800" },
  public_domain: { label: "公版", color: "bg-teal-100 text-teal-800" },
  analysis_only: { label: "仅分析", color: "bg-yellow-100 text-yellow-800" },
  unknown: { label: "未确认", color: "bg-orange-100 text-orange-800" },
  prohibited: { label: "禁止", color: "bg-red-100 text-red-800" },
};

export default function LibraryPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterRights, setFilterRights] = useState("");

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- standard data-fetching pattern
    setLoading(true);
    api
      .listDocuments(filterRights ? { rights_status: filterRights } : undefined)
      .then(setDocuments)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [filterRights]);

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`确定删除「${name}」？关联数据也会被删除。`)) return;
    await api.deleteDocument(id);
    setDocuments((prev) => prev.filter((d) => d.id !== id));
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">文本资料库</h1>
        <Link
          href="/library/upload"
          className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm hover:bg-blue-700"
        >
          + 上传文件
        </Link>
      </div>

      {/* Filter bar */}
      <div className="bg-white border rounded-lg p-4 flex gap-3 items-center">
        <span className="text-sm text-gray-500">权利状态筛选：</span>
        <select
          className="border rounded px-2 py-1.5 text-sm"
          value={filterRights}
          onChange={(e) => setFilterRights(e.target.value)}
        >
          <option value="">全部</option>
          <option value="owned">自有</option>
          <option value="authorized">已授权</option>
          <option value="public_domain">公版</option>
          <option value="analysis_only">仅分析</option>
          <option value="unknown">未确认</option>
          <option value="prohibited">禁止</option>
        </select>
        <span className="text-sm text-gray-400 ml-auto">{documents.length} 份资料</span>
      </div>

      {loading && <p className="text-gray-400">加载中...</p>}
      {error && <p className="text-red-500">{error}</p>}

      {!loading && documents.length === 0 && (
        <div className="bg-white border rounded-lg p-12 text-center text-gray-400">
          <p className="text-lg mb-2">暂无资料</p>
          <p className="text-sm">
            <Link href="/library/upload" className="text-blue-600 hover:underline">
              上传 TXT 或 Markdown 文件
            </Link>{" "}
            开始分析
          </p>
        </div>
      )}

      <div className="space-y-3">
        {documents.map((doc) => {
          const rights = RIGHTS_LABELS[doc.rights_status] || RIGHTS_LABELS.unknown;
          return (
            <div
              key={doc.id}
              className="bg-white border rounded-lg p-4 hover:shadow-sm transition-shadow"
            >
              <div className="flex items-center justify-between">
                <Link href={`/library/${doc.id}`} className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold truncate">{doc.title}</h3>
                    <span className={`text-xs px-1.5 py-0.5 rounded ${rights.color}`}>
                      {rights.label}
                    </span>
                    {doc.parse_status === "completed" && (
                      <span className="text-xs bg-green-100 text-green-800 px-1.5 py-0.5 rounded">
                        已解析
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-500 mt-1">
                    {doc.original_filename} · {(doc.file_size / 1024).toFixed(1)} KB · {doc.mime_type}
                  </p>
                  <p className="text-xs text-gray-400 mt-1">
                    来源: {doc.source_name || "未知"} · 作者: {doc.author_name || "未知"}
                    {!doc.analysis_allowed && (
                      <span className="text-red-500 ml-2">不可分析</span>
                    )}
                    {!doc.generation_reference_allowed && doc.analysis_allowed && (
                      <span className="text-orange-500 ml-2">不可作为生成参考</span>
                    )}
                  </p>
                </Link>
                <button
                  onClick={() => handleDelete(doc.id, doc.title)}
                  className="text-red-500 text-sm hover:underline ml-4 shrink-0"
                >
                  删除
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
