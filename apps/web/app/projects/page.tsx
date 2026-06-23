"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, type PaginatedResponse, type Project } from "@/lib/api";

export default function ProjectsPage() {
  const [data, setData] = useState<PaginatedResponse<Project> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [genre, setGenre] = useState("");
  const [status, setStatus] = useState("");
  const [includeArchived, setIncludeArchived] = useState(false);
  const [page, setPage] = useState(1);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- standard data-fetching pattern
    setLoading(true);
    api
      .listProjects({ search, genre, status, include_archived: includeArchived, page, page_size: 10 })
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [search, genre, status, includeArchived, page]);

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`确定删除项目「${name}」？关联的资料和章节也会被删除。`)) return;
    await api.deleteProject(id);
    // Reload
    api.listProjects({ search, genre, status, include_archived: includeArchived, page, page_size: 10 }).then(setData);
  };

  const handleArchive = async (id: string) => {
    await api.archiveProject(id);
    api.listProjects({ search, genre, status, include_archived: includeArchived, page, page_size: 10 }).then(setData);
  };

  const handleRestore = async (id: string) => {
    await api.restoreProject(id);
    api.listProjects({ search, genre, status, include_archived: includeArchived, page, page_size: 10 }).then(setData);
  };

  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = data?.total_pages ?? 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">小说项目</h1>
        <Link
          href="/projects/new"
          className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm hover:bg-blue-700"
        >
          + 新建项目
        </Link>
      </div>

      {/* Search / Filter bar */}
      <div className="bg-white border rounded-lg p-4 flex flex-wrap gap-3 items-end">
        <div>
          <label className="block text-xs text-gray-500 mb-1">搜索</label>
          <input
            className="border rounded px-2 py-1.5 text-sm w-40"
            placeholder="项目名称..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">题材</label>
          <select className="border rounded px-2 py-1.5 text-sm" value={genre} onChange={(e) => { setGenre(e.target.value); setPage(1); }}>
            <option value="">全部</option>
            {["玄幻", "仙侠", "都市", "科幻", "历史", "游戏", "悬疑", "言情"].map((g) => (
              <option key={g} value={g}>{g}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">状态</label>
          <select className="border rounded px-2 py-1.5 text-sm" value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }}>
            <option value="">全部</option>
            {["drafting", "writing", "completed", "paused"].map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>
        <label className="flex items-center gap-1.5 text-sm cursor-pointer">
          <input type="checkbox" checked={includeArchived} onChange={(e) => { setIncludeArchived(e.target.checked); setPage(1); }} />
          包含已归档
        </label>
        <span className="text-sm text-gray-400 ml-auto">共 {total} 个项目</span>
      </div>

      {loading && <p className="text-gray-400">加载中...</p>}
      {error && <p className="text-red-500">{error}</p>}

      {!loading && items.length === 0 && (
        <div className="bg-white border rounded-lg p-12 text-center text-gray-400">
          <p className="text-lg mb-2">暂无项目</p>
          <p className="text-sm">{search || genre || status ? "没有匹配的项目" : "点击「新建项目」开始创作"}</p>
        </div>
      )}

      <div className="space-y-3">
        {items.map((p) => (
          <div
            key={p.id}
            className={`bg-white border rounded-lg p-4 hover:shadow-sm transition-shadow ${p.archived_at ? "opacity-60" : ""}`}
          >
            <div className="flex items-center justify-between">
              <Link href={`/projects/${p.id}`} className="flex-1 min-w-0">
                <h3 className="font-semibold truncate">
                  {p.name}
                  {p.archived_at && <span className="ml-2 text-xs bg-gray-200 px-1.5 py-0.5 rounded">已归档</span>}
                </h3>
                <p className="text-sm text-gray-500">
                  {p.genre || "未分类"} · {p.audience_type || "未指定"} · {p.status} · {p.document_count} 份资料 · {p.chapter_count} 章
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  更新于 {new Date(p.updated_at).toLocaleDateString("zh-CN")}
                </p>
              </Link>
              <div className="flex gap-2 ml-4 shrink-0">
                {p.archived_at ? (
                  <button onClick={() => handleRestore(p.id)} className="text-green-600 text-sm hover:underline">
                    恢复
                  </button>
                ) : (
                  <button onClick={() => handleArchive(p.id)} className="text-orange-500 text-sm hover:underline">
                    归档
                  </button>
                )}
                <button onClick={() => handleDelete(p.id, p.name)} className="text-red-500 text-sm hover:underline">
                  删除
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button
            disabled={page <= 1}
            onClick={() => setPage(page - 1)}
            className="px-3 py-1 text-sm border rounded disabled:opacity-40"
          >
            上一页
          </button>
          <span className="text-sm text-gray-500">
            {page} / {totalPages}
          </span>
          <button
            disabled={page >= totalPages}
            onClick={() => setPage(page + 1)}
            className="px-3 py-1 text-sm border rounded disabled:opacity-40"
          >
            下一页
          </button>
        </div>
      )}
    </div>
  );
}
