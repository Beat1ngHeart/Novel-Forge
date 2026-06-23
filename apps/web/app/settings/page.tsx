"use client";

import { useCallback, useEffect, useState } from "react";
import { api, type CallLog, type MockTestResult, type ProviderHealth, type ProviderInfo } from "@/lib/api";

function StatusDot({ status }: { status: string }) {
  const color = status === "ok" || status === "available" ? "bg-green-500" : "bg-red-500";
  return <span className={`inline-block w-2 h-2 rounded-full ${color}`} />;
}

export default function SettingsPage() {
  const [info, setInfo] = useState<Record<string, unknown> | null>(null);
  const [providers, setProviders] = useState<ProviderInfo[]>([]);
  const [health, setHealth] = useState<ProviderHealth | null>(null);
  const [logs, setLogs] = useState<CallLog[]>([]);
  const [testResult, setTestResult] = useState<MockTestResult | null>(null);
  const [testing, setTesting] = useState<string | null>(null);

  const load = useCallback(() => {
    api.systemInfo().then(setInfo).catch(() => {});
    api.listProviders().then(setProviders).catch(() => {});
    api.providerHealth().then(setHealth).catch(() => {});
    api.listCallLogs(10).then(setLogs).catch(() => {});
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleTest = async (testType: string) => {
    setTesting(testType);
    setTestResult(null);
    try {
      const result = await api.mockTest(testType);
      setTestResult(result);
      // Refresh logs after test
      api.listCallLogs(10).then(setLogs).catch(() => {});
    } catch (e: unknown) {
      setTestResult({
        success: false,
        test_type: testType,
        error: e instanceof Error ? e.message : "测试失败",
        latency_ms: 0,
      });
    }
    setTesting(null);
  };

  return (
    <div className="space-y-6 max-w-3xl">
      <h1 className="text-2xl font-bold">设置</h1>

      {/* System Info */}
      <div className="bg-white border rounded-lg p-5 space-y-3">
        <h2 className="font-semibold">系统信息</h2>
        {info ? (
          <dl className="space-y-2">
            {Object.entries(info).map(([k, v]) => (
              <div key={k} className="flex justify-between text-sm">
                <dt className="text-gray-500">{k}</dt>
                <dd className="font-mono">{String(v)}</dd>
              </div>
            ))}
          </dl>
        ) : (
          <p className="text-sm text-gray-400">加载中...</p>
        )}
      </div>

      {/* Provider Status */}
      <div className="bg-white border rounded-lg p-5 space-y-3">
        <h2 className="font-semibold">LLM Provider</h2>
        {providers.length > 0 && (
          <div className="space-y-2">
            {providers.map((p) => (
              <div key={p.name} className="flex items-center gap-2 text-sm">
                <StatusDot status={p.status} />
                <span className="font-medium">{p.name}</span>
                <span className="text-gray-400">({p.model})</span>
                <span className={p.status === "available" ? "text-green-600" : "text-red-600"}>
                  {p.status}
                </span>
              </div>
            ))}
          </div>
        )}
        {health && (
          <div className="text-sm text-gray-500">
            延迟: {health.latency_ms}ms {health.error && <span className="text-red-500">— {health.error}</span>}
          </div>
        )}

        {/* Mock Test Buttons */}
        <div className="border-t pt-3">
          <h3 className="text-sm font-medium mb-2">模拟测试</h3>
          <div className="flex gap-2 flex-wrap">
            {(["success", "failure", "timeout", "rate_limit"] as const).map((type) => (
              <button
                key={type}
                onClick={() => handleTest(type)}
                disabled={testing !== null}
                className="px-3 py-1.5 text-sm border rounded hover:bg-gray-50 disabled:opacity-50"
              >
                {testing === type ? "测试中..." : type === "success" ? "正常" : type === "failure" ? "失败" : type === "timeout" ? "超时" : "限流"}
              </button>
            ))}
          </div>
        </div>

        {/* Test Result */}
        {testResult && (
          <div
            className={`border rounded p-3 text-sm ${testResult.success ? "bg-green-50 border-green-200" : "bg-red-50 border-red-200"}`}
          >
            <div className="font-medium mb-1">{testResult.success ? "测试成功" : "测试失败"}</div>
            {testResult.response && (
              <div className="text-gray-600 font-mono text-xs break-all">{testResult.response}</div>
            )}
            {testResult.error && <div className="text-red-600">{testResult.error}</div>}
            <div className="text-gray-400 mt-1">延迟: {testResult.latency_ms}ms</div>
          </div>
        )}
      </div>

      {/* Call Logs */}
      <div className="bg-white border rounded-lg p-5 space-y-3">
        <h2 className="font-semibold">最近调用日志</h2>
        {logs.length === 0 ? (
          <p className="text-sm text-gray-400">暂无调用记录。点击上方测试按钮产生日志。</p>
        ) : (
          <div className="space-y-1">
            {logs.map((log) => (
              <div key={log.id} className="flex items-center gap-3 text-xs font-mono py-1 border-b last:border-0">
                <StatusDot status={log.status === "success" ? "ok" : "error"} />
                <span className="w-16">{log.task_type}</span>
                <span className={log.status === "success" ? "text-green-600" : "text-red-600"}>{log.status}</span>
                <span className="text-gray-400">{log.latency_ms}ms</span>
                <span className="text-gray-400">
                  {log.input_tokens}→{log.output_tokens} tokens
                </span>
                {log.error_message && (
                  <span className="text-red-400 truncate max-w-48">{log.error_message}</span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
