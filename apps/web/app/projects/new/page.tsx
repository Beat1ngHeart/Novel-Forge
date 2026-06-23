"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

const GENRES = ["玄幻", "仙侠", "都市", "科幻", "历史", "游戏", "悬疑", "言情", "其他"];

export default function NewProjectPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    name: "",
    description: "",
    genre: "玄幻",
    subgenre: "",
    audience_type: "男频",
    target_platform: "",
    target_reader: "",
    target_word_count: 1000000,
    chapter_word_count: 3000,
    update_frequency: "日更",
    language: "zh-CN",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!form.name.trim()) return setError("请输入项目名称");
    setSaving(true);
    setError(null);
    try {
      await api.createProject(form);
      router.push("/projects");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "创建失败");
    }
    setSaving(false);
  };

  const field = (label: string, key: keyof typeof form, type = "text", placeholder = "") => (
    <div>
      <label className="block text-sm font-medium mb-1">{label}</label>
      <input
        type={type}
        className="w-full border rounded-md px-3 py-2 text-sm"
        value={form[key] as string}
        placeholder={placeholder}
        onChange={(e) =>
          setForm({ ...form, [key]: type === "number" ? Number(e.target.value) : e.target.value })
        }
      />
    </div>
  );

  return (
    <div className="max-w-2xl space-y-6">
      <h1 className="text-2xl font-bold">新建小说项目</h1>
      <div className="bg-white border rounded-lg p-6 space-y-4">
        {error && (
          <div className="bg-red-50 border border-red-200 rounded p-3 text-sm text-red-700">{error}</div>
        )}

        {field("项目名称 *", "name", "text", "我的小说")}

        <div>
          <label className="block text-sm font-medium mb-1">简介</label>
          <textarea
            className="w-full border rounded-md px-3 py-2 text-sm h-20"
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            placeholder="故事简介..."
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">题材</label>
            <select
              className="w-full border rounded-md px-3 py-2 text-sm"
              value={form.genre}
              onChange={(e) => setForm({ ...form, genre: e.target.value })}
            >
              {GENRES.map((g) => (
                <option key={g}>{g}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">频道</label>
            <select
              className="w-full border rounded-md px-3 py-2 text-sm"
              value={form.audience_type}
              onChange={(e) => setForm({ ...form, audience_type: e.target.value })}
            >
              <option>男频</option>
              <option>女频</option>
            </select>
          </div>
          {field("子题材", "subgenre", "text", "升级流")}
          {field("目标平台", "target_platform", "text", "起点中文网")}
          {field("目标读者", "target_reader", "text", "18-30岁男性")}
          {field("目标总字数", "target_word_count", "number")}
          {field("单章目标字数", "chapter_word_count", "number")}
          {field("更新频率", "update_frequency", "text", "日更")}
          <div>
            <label className="block text-sm font-medium mb-1">语言</label>
            <select
              className="w-full border rounded-md px-3 py-2 text-sm"
              value={form.language}
              onChange={(e) => setForm({ ...form, language: e.target.value })}
            >
              <option value="zh-CN">中文</option>
              <option value="en">English</option>
            </select>
          </div>
        </div>

        <div className="flex gap-3 pt-2">
          <button
            onClick={handleSubmit}
            disabled={saving}
            className="bg-blue-600 text-white px-6 py-2 rounded-md text-sm hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? "创建中..." : "创建项目"}
          </button>
          <button onClick={() => router.back()} className="border px-6 py-2 rounded-md text-sm hover:bg-gray-50">
            取消
          </button>
        </div>
      </div>
    </div>
  );
}
