"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, type Document } from "@/lib/api";

const RIGHTS_INFO: Record<string, { label: string; desc: string; color: string }> = {
  owned: { label: "自有/原创", desc: "可分析，可作为生成参考", color: "text-green-700 bg-green-50 border-green-200" },
  authorized: { label: "已获授权", desc: "可分析，可作为生成参考", color: "text-blue-700 bg-blue-50 border-blue-200" },
  public_domain: { label: "公版作品", desc: "可分析，可作为生成参考", color: "text-teal-700 bg-teal-50 border-teal-200" },
  analysis_only: { label: "仅限分析", desc: "可分析，不可作为生成参考", color: "text-yellow-700 bg-yellow-50 border-yellow-200" },
  unknown: { label: "未确认权利", desc: "可分析，默认不可作为生成参考", color: "text-orange-700 bg-orange-50 border-orange-200" },
  prohibited: { label: "禁止使用", desc: "不可分析，不可作为生成参考", color: "text-red-700 bg-red-50 border-red-200" },
};

export default function DocumentDetailPage() {
  const { id } = useParams() as { id: string };
  const router = useRouter();
  const [doc, setDoc] = useState<Document | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getDocument(id)
      .then(setDoc)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  const handleDelete = async () => {
    if (!doc) return;
    if (!confirm(`确定删除「${doc.title}」？文件和关联数据将被永久删除。`)) return;
    await api.deleteDocument(doc.id);
    router.push("/library");
  };

  if (loading) return <p className="text-gray-400 p-6">加载中...</p>;
  if (error) return <p className="text-red-500 p-6">{error}</p>;
  if (!doc) return <p className="text-gray-400 p-6">资料不存在</p>;

  const rights = RIGHTS_INFO[doc.rights_status] || RIGHTS_INFO.unknown;

  return (
    <div className="space-y-6 max-w-3xl">
      <Link href="/library" className="text-blue-600 hover:underline text-sm">
        &larr; 返回资料库
      </Link>

      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">{doc.title}</h1>
        <button onClick={handleDelete} className="text-red-500 border border-red-300 px-3 py-1.5 rounded text-sm hover:bg-red-50">
          删除
        </button>
      </div>

      {/* Rights status card */}
      <div className={`border rounded-lg p-5 ${rights.color}`}>
        <h2 className="font-semibold mb-2">权利状态：{rights.label}</h2>
        <p className="text-sm">{rights.desc}</p>
        <div className="mt-3 flex gap-4 text-sm">
          <span>
            分析权限:{" "}
            <strong>{doc.analysis_allowed ? "允许" : "禁止"}</strong>
          </span>
          <span>
            生成参考:{" "}
            <strong>{doc.generation_reference_allowed ? "允许" : "禁止"}</strong>
          </span>
        </div>
      </div>

      {/* File info */}
      <div className="bg-white border rounded-lg p-5">
        <h2 className="font-semibold mb-3">文件信息</h2>
        <dl className="grid grid-cols-2 gap-4">
          <div>
            <dt className="text-xs text-gray-500">文件名</dt>
            <dd className="text-sm font-medium">{doc.original_filename}</dd>
          </div>
          <div>
            <dt className="text-xs text-gray-500">文件类型</dt>
            <dd className="text-sm font-medium">{doc.mime_type} ({doc.file_type})</dd>
          </div>
          <div>
            <dt className="text-xs text-gray-500">文件大小</dt>
            <dd className="text-sm font-medium">{(doc.file_size / 1024).toFixed(1)} KB</dd>
          </div>
          <div>
            <dt className="text-xs text-gray-500">SHA-256</dt>
            <dd className="text-xs font-mono text-gray-600 break-all">{doc.sha256}</dd>
          </div>
          <div>
            <dt className="text-xs text-gray-500">来源</dt>
            <dd className="text-sm font-medium">{doc.source_name || "—"}</dd>
          </div>
          <div>
            <dt className="text-xs text-gray-500">作者</dt>
            <dd className="text-sm font-medium">{doc.author_name || "—"}</dd>
          </div>
          <div>
            <dt className="text-xs text-gray-500">解析状态</dt>
            <dd className="text-sm font-medium">{doc.parse_status}</dd>
          </div>
          <div>
            <dt className="text-xs text-gray-500">存储路径</dt>
            <dd className="text-xs font-mono text-gray-400 break-all">{doc.storage_path}</dd>
          </div>
        </dl>
      </div>

      {/* Chapters */}
      <div className="bg-white border rounded-lg p-5">
        <h2 className="font-semibold mb-3">章节管理</h2>
        <div className="flex gap-3">
          <Link
            href={`/library/${doc.id}/parse`}
            className="bg-purple-600 text-white px-4 py-2 rounded text-sm hover:bg-purple-700"
          >
            解析章节
          </Link>
          <Link
            href={`/library/${doc.id}/chapters`}
            className="border px-4 py-2 rounded text-sm hover:bg-gray-50"
          >
            查看章节列表
          </Link>
        </div>
      </div>

      {doc.error_message && (
        <div className="bg-red-50 border border-red-200 rounded p-3 text-sm text-red-700">
          错误信息: {doc.error_message}
        </div>
      )}

      <div className="text-xs text-gray-400">
        创建于 {new Date(doc.created_at).toLocaleString("zh-CN")} · 更新于{" "}
        {new Date(doc.updated_at).toLocaleString("zh-CN")}
      </div>
    </div>
  );
}
