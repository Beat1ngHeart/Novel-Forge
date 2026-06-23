"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useRef, useState } from "react";
import { api } from "@/lib/api";

const RIGHTS_OPTIONS = [
  { value: "owned", label: "自有/原创", desc: "分析和生成参考均可" },
  { value: "authorized", label: "已获授权", desc: "分析和生成参考均可" },
  { value: "public_domain", label: "公版作品", desc: "分析和生成参考均可" },
  { value: "analysis_only", label: "仅限分析", desc: "可用于分析，不可作为生成参考" },
  { value: "unknown", label: "未确认权利", desc: "可用于分析，默认不可作为生成参考" },
  { value: "prohibited", label: "禁止使用", desc: "不可分析，不可作为生成参考" },
];

export default function UploadPage() {
  const router = useRouter();
  const fileRef = useRef<HTMLInputElement>(null);
  const [form, setForm] = useState({
    title: "",
    source_name: "",
    author_name: "",
    rights_status: "unknown",
  });
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;
    setSelectedFile(file);
    if (file && !form.title) {
      setForm({ ...form, title: file.name.replace(/\.[^.]+$/, "") });
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return setError("请选择文件");
    setUploading(true);
    setError(null);
    try {
      await api.uploadDocument(selectedFile, form);
      router.push("/library");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "上传失败");
    }
    setUploading(false);
  };

  const selectedRights = RIGHTS_OPTIONS.find((r) => r.value === form.rights_status);

  return (
    <div className="max-w-2xl space-y-6">
      <Link href="/library" className="text-blue-600 hover:underline text-sm">
        &larr; 返回资料库
      </Link>

      <h1 className="text-2xl font-bold">上传文本资料</h1>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded p-3 text-sm text-red-700">{error}</div>
      )}

      <div className="bg-white border rounded-lg p-6 space-y-4">
        <h2 className="font-semibold">选择文件</h2>
        <div>
          <input
            ref={fileRef}
            type="file"
            accept=".txt,.md,.markdown"
            onChange={handleFileChange}
            className="text-sm"
          />
          <p className="text-xs text-gray-400 mt-1">
            支持 TXT 和 Markdown，最大 10MB。不允许上传可执行文件。
          </p>
        </div>
        {selectedFile && (
          <div className="text-sm text-gray-600 bg-gray-50 rounded p-2">
            {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
          </div>
        )}
      </div>

      <div className="bg-white border rounded-lg p-6 space-y-4">
        <h2 className="font-semibold">文件信息</h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">标题</label>
            <input
              className="w-full border rounded-md px-3 py-2 text-sm"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              placeholder="文件标题"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">来源</label>
            <input
              className="w-full border rounded-md px-3 py-2 text-sm"
              value={form.source_name}
              onChange={(e) => setForm({ ...form, source_name: e.target.value })}
              placeholder="原创/公版/出版社名"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">作者</label>
            <input
              className="w-full border rounded-md px-3 py-2 text-sm"
              value={form.author_name}
              onChange={(e) => setForm({ ...form, author_name: e.target.value })}
              placeholder="作者名"
            />
          </div>
        </div>
      </div>

      <div className="bg-white border rounded-lg p-6 space-y-4">
        <h2 className="font-semibold">权利登记</h2>
        <p className="text-sm text-gray-500">
          请如实填写文件的权利状态。未确认权利的文件默认不进入生成参考库。
        </p>
        <div className="space-y-2">
          {RIGHTS_OPTIONS.map((opt) => (
            <label
              key={opt.value}
              className={`flex items-start gap-3 p-3 rounded border cursor-pointer transition-colors ${
                form.rights_status === opt.value ? "border-blue-500 bg-blue-50" : "border-gray-200 hover:bg-gray-50"
              }`}
            >
              <input
                type="radio"
                name="rights"
                value={opt.value}
                checked={form.rights_status === opt.value}
                onChange={(e) => setForm({ ...form, rights_status: e.target.value })}
                className="mt-0.5"
              />
              <div>
                <div className="text-sm font-medium">{opt.label}</div>
                <div className="text-xs text-gray-500">{opt.desc}</div>
              </div>
            </label>
          ))}
        </div>
        {selectedRights && (
          <div className="text-sm bg-gray-50 rounded p-3">
            <strong>效果：</strong> {selectedRights.desc}
          </div>
        )}
      </div>

      <div className="flex gap-3">
        <button
          onClick={handleUpload}
          disabled={uploading || !selectedFile}
          className="bg-blue-600 text-white px-6 py-2 rounded-md text-sm hover:bg-blue-700 disabled:opacity-50"
        >
          {uploading ? "上传中..." : "上传文件"}
        </button>
        <Link href="/library" className="border px-6 py-2 rounded-md text-sm hover:bg-gray-50">
          取消
        </Link>
      </div>
    </div>
  );
}
