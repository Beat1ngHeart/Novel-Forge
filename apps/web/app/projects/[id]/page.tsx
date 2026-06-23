"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api, type Project } from "@/lib/api";

function InfoItem({ label, value }: { label: string; value: string | number | null }) {
  return (
    <div>
      <dt className="text-xs text-gray-500">{label}</dt>
      <dd className="text-sm font-medium">{value || "—"}</dd>
    </div>
  );
}

export default function ProjectDetailPage() {
  const { id } = useParams() as { id: string };
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getProject(id)
      .then(setProject)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  const handleArchive = async () => {
    if (!project) return;
    const updated = await api.archiveProject(project.id);
    setProject(updated);
  };

  const handleRestore = async () => {
    if (!project) return;
    const updated = await api.restoreProject(project.id);
    setProject(updated);
  };

  if (loading) return <p className="text-gray-400 p-6">加载中...</p>;
  if (error) return <p className="text-red-500 p-6">{error}</p>;
  if (!project) return <p className="text-gray-400 p-6">项目不存在</p>;

  return (
    <div className="space-y-6 max-w-3xl">
      <Link href="/projects" className="text-blue-600 hover:underline text-sm">
        &larr; 返回项目列表
      </Link>

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">
            {project.name}
            {project.archived_at && (
              <span className="ml-2 text-sm bg-gray-200 px-2 py-0.5 rounded">已归档</span>
            )}
          </h1>
          <p className="text-sm text-gray-500 mt-1">{project.description || "暂无简介"}</p>
        </div>
        <div className="flex gap-2">
          {!project.archived_at && (
            <>
              <Link
                href={`/projects/${project.id}/volumes`}
                className="border px-3 py-1.5 rounded text-sm hover:bg-gray-50"
              >
                分卷
              </Link>
              <Link
                href={`/projects/${project.id}/synopsis`}
                className="border px-3 py-1.5 rounded text-sm hover:bg-gray-50"
              >
                总纲
              </Link>
              <Link
                href={`/projects/${project.id}/creative`}
                className="border px-3 py-1.5 rounded text-sm hover:bg-gray-50"
              >
                创意方向
              </Link>
              <Link
                href={`/projects/${project.id}/bible`}
                className="border px-3 py-1.5 rounded text-sm hover:bg-gray-50"
              >
                小说圣经
              </Link>
              <Link
                href={`/projects/${project.id}/settings`}
                className="border px-3 py-1.5 rounded text-sm hover:bg-gray-50"
              >
                设置
              </Link>
              <button onClick={handleArchive} className="text-orange-500 border border-orange-300 px-3 py-1.5 rounded text-sm hover:bg-orange-50">
                归档
              </button>
            </>
          )}
          {project.archived_at && (
            <button onClick={handleRestore} className="text-green-600 border border-green-300 px-3 py-1.5 rounded text-sm hover:bg-green-50">
              恢复
            </button>
          )}
        </div>
      </div>

      <div className="bg-white border rounded-lg p-5">
        <h2 className="font-semibold mb-3">项目信息</h2>
        <dl className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <InfoItem label="题材" value={project.genre} />
          <InfoItem label="子题材" value={project.subgenre} />
          <InfoItem label="频道" value={project.audience_type} />
          <InfoItem label="目标平台" value={project.target_platform} />
          <InfoItem label="目标读者" value={project.target_reader} />
          <InfoItem label="语言" value={project.language} />
          <InfoItem label="状态" value={project.status} />
          <InfoItem label="更新频率" value={project.update_frequency} />
          <InfoItem label="目标总字数" value={project.target_word_count ? project.target_word_count.toLocaleString() : "—"} />
          <InfoItem label="单章目标字数" value={project.chapter_word_count.toLocaleString()} />
          <InfoItem label="当前卷" value={project.current_volume} />
          <InfoItem label="当前章" value={project.current_chapter} />
        </dl>
      </div>

      <div className="bg-white border rounded-lg p-5">
        <h2 className="font-semibold mb-3">进度</h2>
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-blue-50 rounded p-3">
            <div className="text-2xl font-bold">{project.document_count}</div>
            <div className="text-sm text-gray-500">已导入资料</div>
          </div>
          <div className="bg-green-50 rounded p-3">
            <div className="text-2xl font-bold">{project.chapter_count}</div>
            <div className="text-sm text-gray-500">已识别章节</div>
          </div>
        </div>
      </div>

      <div className="text-xs text-gray-400">
        创建于 {new Date(project.created_at).toLocaleString("zh-CN")} · 更新于{" "}
        {new Date(project.updated_at).toLocaleString("zh-CN")}
        {project.archived_at && ` · 归档于 ${new Date(project.archived_at).toLocaleString("zh-CN")}`}
      </div>
    </div>
  );
}
