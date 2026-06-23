"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, type Project } from "@/lib/api";

export default function ProjectSettingsPage() {
  const { id } = useParams() as { id: string };
  const router = useRouter();
  const [project, setProject] = useState<Project | null>(null);
  const [form, setForm] = useState<Record<string, unknown>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getProject(id)
      .then((p) => {
        setProject(p);
        setForm({
          name: p.name,
          description: p.description,
          genre: p.genre,
          subgenre: p.subgenre,
          audience_type: p.audience_type,
          target_platform: p.target_platform,
          target_reader: p.target_reader,
          target_word_count: p.target_word_count,
          chapter_word_count: p.chapter_word_count,
          update_frequency: p.update_frequency,
          language: p.language,
          status: p.status,
          current_volume: p.current_volume,
          current_chapter: p.current_chapter,
        });
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      const updated = await api.updateProject(id, form);
      setProject(updated);
      router.push(`/projects/${id}`);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "保存失败");
    }
    setSaving(false);
  };

  const handleDelete = async () => {
    if (!project) return;
    if (!confirm(`确定删除项目「${project.name}」？此操作不可撤销，关联数据也会被删除。`)) return;
    await api.deleteProject(id);
    router.push("/projects");
  };

  if (loading) return <p className="text-gray-400 p-6">加载中...</p>;
  if (!project) return <p className="text-gray-400 p-6">项目不存在</p>;

  const field = (label: string, key: string, type = "text") => (
    <div>
      <label className="block text-sm font-medium mb-1">{label}</label>
      <input
        type={type}
        className="w-full border rounded-md px-3 py-2 text-sm"
        value={String(form[key] ?? "")}
        onChange={(e) => setForm({ ...form, [key]: type === "number" ? Number(e.target.value) : e.target.value })}
      />
    </div>
  );

  return (
    <div className="max-w-2xl space-y-6">
      <Link href={`/projects/${id}`} className="text-blue-600 hover:underline text-sm">
        &larr; 返回项目详情
      </Link>

      <h1 className="text-2xl font-bold">项目设置 — {project.name}</h1>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded p-3 text-sm text-red-700">{error}</div>
      )}

      <div className="bg-white border rounded-lg p-6 space-y-4">
        <h2 className="font-semibold">基本信息</h2>
        {field("项目名称", "name")}
        <div>
          <label className="block text-sm font-medium mb-1">简介</label>
          <textarea
            className="w-full border rounded-md px-3 py-2 text-sm h-20"
            value={String(form.description ?? "")}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
          />
        </div>
        <div className="grid grid-cols-2 gap-4">
          {field("题材", "genre")}
          {field("子题材", "subgenre")}
          {field("频道", "audience_type")}
          {field("目标平台", "target_platform")}
          {field("目标读者", "target_reader")}
          {field("目标总字数", "target_word_count", "number")}
          {field("单章目标字数", "chapter_word_count", "number")}
          {field("更新频率", "update_frequency")}
          {field("语言", "language")}
          {field("状态", "status")}
          {field("当前卷", "current_volume", "number")}
          {field("当前章", "current_chapter", "number")}
        </div>
      </div>

      <div className="flex gap-3">
        <button
          onClick={handleSave}
          disabled={saving}
          className="bg-blue-600 text-white px-6 py-2 rounded-md text-sm hover:bg-blue-700 disabled:opacity-50"
        >
          {saving ? "保存中..." : "保存修改"}
        </button>
        <Link href={`/projects/${id}`} className="border px-6 py-2 rounded-md text-sm hover:bg-gray-50">
          取消
        </Link>
      </div>

      <div className="border-t pt-4">
        <h2 className="font-semibold text-red-600 mb-2">危险操作</h2>
        <button
          onClick={handleDelete}
          className="border border-red-300 text-red-600 px-4 py-2 rounded-md text-sm hover:bg-red-50"
        >
          删除项目
        </button>
        <p className="text-xs text-gray-400 mt-1">删除后不可恢复，关联的资料和章节也会被删除。</p>
      </div>
    </div>
  );
}
