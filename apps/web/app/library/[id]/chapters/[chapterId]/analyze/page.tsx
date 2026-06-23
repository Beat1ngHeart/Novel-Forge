"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api, type AnalysisOut, type AnalysisResultView, type ChapterDetail } from "@/lib/api";

const EMOTION_LABELS: Record<string, string> = {
  calm: "平静", anticipation: "期待", tension: "紧张", excitement: "兴奋",
  fear: "恐惧", anger: "愤怒", sadness: "悲伤", despair: "绝望",
  joy: "喜悦", surprise: "惊讶", hope: "希望", determination: "坚定",
  relief: "释然", betrayal: "背叛感", disgust: "厌恶",
};

const FUNCTION_LABELS: Record<string, string> = {
  opening: "开场铺垫", setup: "世界建立", rising: "冲突升级", climax: "高潮",
  falling: "冲突消退", transition: "过渡", twist: "转折", cliffhanger: "悬念章",
  character_development: "角色塑造", world_building: "世界展开",
  foreshadow_plant: "伏笔埋设", foreshadow_payoff: "伏笔回收",
  epilogue: "尾声", filler: "日常", other: "其他",
};

function IntensityBar({ value, max = 10, color }: { value: number; max?: number; color: string }) {
  return (
    <div className="flex items-center gap-2">
      <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full`} style={{ width: `${(value / max) * 100}%` }} />
      </div>
      <span className="text-xs text-gray-500">{value}/{max}</span>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white border rounded-lg p-5">
      <h3 className="font-semibold mb-3 text-gray-800">{title}</h3>
      {children}
    </div>
  );
}

export default function AnalyzePage() {
  const { id: docId, chapterId } = useParams() as { id: string; chapterId: string };
  const [chapter, setChapter] = useState<ChapterDetail | null>(null);
  const [analyses, setAnalyses] = useState<AnalysisOut[]>([]);
  const [selectedResult, setSelectedResult] = useState<AnalysisResultView | null>(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    // eslint-disable-next-line react-hooks/set-state-in-effect -- standard data-fetching pattern
    setLoading(true);
    Promise.all([api.getChapter(docId, chapterId), api.listAnalyses(chapterId)])
      .then(([ch, an]) => {
        if (cancelled) return;
        setChapter(ch);
        setAnalyses(an);
      })
      .catch((e) => {
        if (cancelled) return;
        setError(e instanceof Error ? e.message : "加载失败");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [docId, chapterId]);

  const handleAnalyze = async () => {
    setAnalyzing(true);
    setError(null);
    try {
      await api.triggerAnalysis(chapterId);
      // Reload data
      const [ch, an] = await Promise.all([api.getChapter(docId, chapterId), api.listAnalyses(chapterId)]);
      setChapter(ch);
      setAnalyses(an);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "分析失败");
    }
    setAnalyzing(false);
  };

  const handleViewResult = async (analysisId: string) => {
    try {
      const result = await api.getAnalysisResult(chapterId, analysisId);
      setSelectedResult(result);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "获取结果失败");
    }
  };

  if (loading) return <p className="text-gray-400 p-6">加载中...</p>;
  if (error && !chapter) return <p className="text-red-500 p-6">{error}</p>;

  return (
    <div className="space-y-6 max-w-4xl">
      <Link href={`/library/${docId}/chapters`} className="text-blue-600 hover:underline text-sm">
        &larr; 返回章节列表
      </Link>

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{chapter?.title || "章节分析"}</h1>
          <p className="text-sm text-gray-500">{chapter?.word_count} 字</p>
        </div>
        <button
          onClick={handleAnalyze}
          disabled={analyzing}
          className="bg-purple-600 text-white px-4 py-2 rounded text-sm hover:bg-purple-700 disabled:opacity-50"
        >
          {analyzing ? "分析中..." : "🔍 重新分析"}
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded p-3 text-sm text-red-700">{error}</div>
      )}

      {/* Analysis History */}
      <Section title="分析历史">
        {analyses.length === 0 ? (
          <p className="text-sm text-gray-400">暂无分析记录。点击「重新分析」开始。</p>
        ) : (
          <div className="space-y-2">
            {analyses.map((a) => (
              <div key={a.id} className="flex items-center justify-between border rounded p-3">
                <div className="flex items-center gap-3">
                  <span className={`w-2 h-2 rounded-full ${a.status === "completed" ? "bg-green-500" : a.status === "failed" ? "bg-red-500" : "bg-yellow-500"}`} />
                  <div>
                    <span className="text-sm font-medium">{a.status}</span>
                    <span className="text-xs text-gray-400 ml-2">
                      {a.provider} · {a.model} · {new Date(a.created_at).toLocaleString("zh-CN")}
                    </span>
                    {a.chapter_function && (
                      <span className="text-xs bg-blue-100 text-blue-800 px-1.5 py-0.5 rounded ml-2">
                        {FUNCTION_LABELS[a.chapter_function] || a.chapter_function}
                      </span>
                    )}
                    {a.confidence > 0 && (
                      <span className="text-xs text-gray-400 ml-2">置信度 {Math.round(a.confidence * 100)}%</span>
                    )}
                  </div>
                </div>
                {a.status === "completed" && (
                  <button onClick={() => handleViewResult(a.id)} className="text-blue-600 text-sm hover:underline">
                    查看结果
                  </button>
                )}
                {a.status === "failed" && a.error_message && (
                  <span className="text-xs text-red-500 max-w-xs truncate">{a.error_message}</span>
                )}
              </div>
            ))}
          </div>
        )}
      </Section>

      {/* Analysis Result */}
      {selectedResult && (
        <>
          <Section title="章节摘要">
            <p className="text-sm leading-relaxed">{selectedResult.chapter_summary}</p>
            <div className="flex gap-4 mt-3 text-xs text-gray-500">
              <span>置信度: <strong>{Math.round(selectedResult.confidence * 100)}%</strong></span>
              <span>题材: <strong>{selectedResult.genre}</strong></span>
              {selectedResult.subgenre && <span>子题材: <strong>{selectedResult.subgenre}</strong></span>}
              <span>视角: <strong>{selectedResult.point_of_view}</strong></span>
            </div>
            {selectedResult.ambiguities.length > 0 && (
              <div className="mt-2">
                <span className="text-xs text-orange-500">歧义: {selectedResult.ambiguities.join("；")}</span>
              </div>
            )}
          </Section>

          <Section title="章节功能与节奏">
            <div className="grid grid-cols-3 gap-4">
              <div>
                <span className="text-xs text-gray-500">章节功能</span>
                <p className="text-sm font-medium">{FUNCTION_LABELS[selectedResult.chapter_function] || selectedResult.chapter_function}</p>
              </div>
              <div>
                <span className="text-xs text-gray-500">节奏</span>
                <p className="text-sm font-medium">{selectedResult.pacing}</p>
              </div>
              <div>
                <span className="text-xs text-gray-500">场景数</span>
                <p className="text-sm font-medium">{selectedResult.scene_count}</p>
              </div>
            </div>
          </Section>

          <Section title="冲突">
            <dl className="grid grid-cols-2 gap-3">
              {Object.entries(selectedResult.conflict).map(([k, v]) => v ? (
                <div key={k}>
                  <dt className="text-xs text-gray-500">{k}</dt>
                  <dd className="text-sm">{String(v)}</dd>
                </div>
              ) : null)}
            </dl>
          </Section>

          <Section title="情绪与回报">
            <dl className="grid grid-cols-2 gap-3">
              {Object.entries(selectedResult.emotion).map(([k, v]) => v ? (
                <div key={k}>
                  <dt className="text-xs text-gray-500">{k}</dt>
                  <dd className="text-sm">
                    {EMOTION_LABELS[String(v)] || String(v)}
                    {typeof v === "number" && <IntensityBar value={v} color="bg-yellow-500" />}
                  </dd>
                </div>
              ) : null)}
            </dl>
          </Section>

          <Section title="悬念与钩子">
            <dl className="grid grid-cols-2 gap-3">
              {Object.entries(selectedResult.suspense).map(([k, v]) => v ? (
                <div key={k}>
                  <dt className="text-xs text-gray-500">{k}</dt>
                  <dd className="text-sm">
                    {Array.isArray(v) ? (v as string[]).join("；") : String(v)}
                    {typeof v === "number" && <IntensityBar value={v} color="bg-orange-500" />}
                  </dd>
                </div>
              ) : null)}
            </dl>
          </Section>

          <Section title="状态变化">
            {Object.entries(selectedResult.state_changes).map(([k, v]) => {
              if (!Array.isArray(v) || v.length === 0) return null;
              return (
                <div key={k} className="mb-3">
                  <h4 className="text-sm font-medium text-gray-700 mb-1">{k}</h4>
                  {(v as Record<string, unknown>[]).map((item, i) => (
                    <div key={i} className="text-xs text-gray-600 border-l-2 border-gray-300 pl-2 mb-1">
                      {Object.entries(item).map(([sk, sv]) => sv ? (
                        <span key={sk} className="mr-3"><strong>{sk}:</strong> {String(sv)}</span>
                      ) : null)}
                    </div>
                  ))}
                </div>
              );
            })}
          </Section>

          <Section title="伏笔">
            {selectedResult.foreshadowing && Object.entries(selectedResult.foreshadowing).map(([k, v]) => {
              if (!Array.isArray(v) || v.length === 0) return null;
              return (
                <div key={k} className="mb-3">
                  <h4 className="text-sm font-medium text-gray-700 mb-1">{k}</h4>
                  {(v as Record<string, unknown>[]).map((item, i) => (
                    <div key={i} className="text-xs text-gray-600 border-l-2 border-gray-300 pl-2 mb-1">
                      {Object.entries(item).map(([sk, sv]) => sv ? (
                        <span key={sk} className="mr-3"><strong>{sk}:</strong> {String(sv)}</span>
                      ) : null)}
                    </div>
                  ))}
                </div>
              );
            })}
          </Section>

          <Section title="文本统计">
            <div className="grid grid-cols-3 gap-4">
              {Object.entries(selectedResult.text_stats).map(([k, v]) => (
                <div key={k}>
                  <span className="text-xs text-gray-500">{k}</span>
                  <p className="text-sm font-medium">{typeof v === "number" ? (v < 1 ? `${Math.round(v * 100)}%` : v) : String(v)}</p>
                </div>
              ))}
            </div>
          </Section>
        </>
      )}
    </div>
  );
}
