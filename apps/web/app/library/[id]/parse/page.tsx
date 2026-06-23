"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { api, type ParsePreview } from "@/lib/api";

export default function ParsePage() {
  const { id: docId } = useParams() as { id: string };
  const router = useRouter();
  const [preview, setPreview] = useState<ParsePreview | null>(null);
  const [loading, setLoading] = useState(false);
  const [parsing, setParsing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handlePreview = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.parsePreview(docId);
      setPreview(result);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "预览失败");
    }
    setLoading(false);
  };

  const handleParse = async () => {
    setParsing(true);
    setError(null);
    try {
      await api.parseDocument(docId);
      router.push(`/library/${docId}/chapters`);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "解析失败");
    }
    setParsing(false);
  };

  return (
    <div className="space-y-6 max-w-3xl">
      <Link href={`/library/${docId}`} className="text-blue-600 hover:underline text-sm">
        &larr; 返回文件详情
      </Link>

      <h1 className="text-2xl font-bold">解析章节</h1>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded p-3 text-sm text-red-700">{error}</div>
      )}

      <div className="bg-white border rounded-lg p-5 space-y-4">
        <h2 className="font-semibold">预览解析结果</h2>
        <p className="text-sm text-gray-500">
          点击「预览」查看系统将如何切分章节。确认无误后点击「执行解析」保存章节。
        </p>
        <div className="flex gap-3">
          <button
            onClick={handlePreview}
            disabled={loading}
            className="border px-4 py-2 rounded text-sm hover:bg-gray-50 disabled:opacity-50"
          >
            {loading ? "分析中..." : "预览解析"}
          </button>
          {preview && (
            <button
              onClick={handleParse}
              disabled={parsing}
              className="bg-purple-600 text-white px-4 py-2 rounded text-sm hover:bg-purple-700 disabled:opacity-50"
            >
              {parsing ? "解析中..." : "执行解析"}
            </button>
          )}
        </div>
      </div>

      {preview && (
        <div className="bg-white border rounded-lg p-5 space-y-4">
          <div className="flex items-center gap-4">
            <h2 className="font-semibold">解析预览</h2>
            <span className="text-sm text-gray-500">
              编码: {preview.encoding_detected} · 共 {preview.total_chapters} 个章节
            </span>
          </div>

          <div className="space-y-2">
            {preview.chapters.map((ch) => (
              <div key={ch.index} className="border rounded p-3">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-400 w-8">{ch.index}</span>
                  <span className="font-medium">{ch.title}</span>
                  {ch.volume_name && (
                    <span className="text-xs bg-blue-100 text-blue-800 px-1.5 py-0.5 rounded">
                      {ch.volume_name}
                    </span>
                  )}
                  <span className="text-xs text-gray-400 ml-auto">{ch.word_count} 字</span>
                </div>
                <p className="text-xs text-gray-500 mt-1 ml-10 line-clamp-2">{ch.preview}</p>
              </div>
            ))}
          </div>

          {preview.total_chapters > 20 && (
            <p className="text-xs text-gray-400">仅显示前 20 个章节预览</p>
          )}
        </div>
      )}

      <div className="bg-yellow-50 border border-yellow-200 rounded p-4 text-sm text-yellow-800">
        <strong>注意：</strong>执行解析会替换该文件的所有现有章节。如果已有手动编辑的章节，请谨慎操作。
      </div>
    </div>
  );
}
