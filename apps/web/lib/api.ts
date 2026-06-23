const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail || body.error || `API error ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export interface HealthResponse {
  status: string;
  app: string;
  env: string;
  database: string;
  llm: { provider: string; status: string; [key: string]: unknown };
}

export interface Project {
  id: string;
  name: string;
  description: string;
  genre: string;
  subgenre: string;
  audience_type: string;
  target_platform: string;
  target_reader: string;
  target_word_count: number;
  chapter_word_count: number;
  update_frequency: string;
  language: string;
  status: string;
  current_volume: number;
  current_chapter: number;
  created_at: string;
  updated_at: string;
  archived_at: string | null;
  document_count: number;
  chapter_count: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ProjectStats {
  total_projects: number;
  active_projects: number;
  archived_projects: number;
  total_documents: number;
  total_chapters: number;
  by_genre: Record<string, number>;
  by_status: Record<string, number>;
}

export interface Document {
  id: string;
  project_id: string | null;
  title: string;
  original_filename: string;
  file_type: string;
  mime_type: string;
  file_size: number;
  sha256: string;
  source_name: string;
  author_name: string;
  rights_status: string;
  analysis_allowed: boolean;
  generation_reference_allowed: boolean;
  storage_path: string;
  parse_status: string;
  error_message: string;
  created_at: string;
  updated_at: string;
}

export interface Chapter {
  id: string;
  document_id: string;
  chapter_index: number;
  volume_name: string;
  title: string;
  word_count: number;
  parse_source: string;
  created_at: string;
  updated_at: string;
}

export interface ChapterDetail extends Chapter {
  content: string;
  content_hash: string;
}

export interface ParsePreview {
  encoding_detected: string;
  total_chapters: number;
  chapters: {
    index: number;
    title: string;
    volume_name: string;
    word_count: number;
    preview: string;
  }[];
}

export interface AnalysisOut {
  id: string;
  chapter_id: string;
  document_id: string;
  project_id: string;
  schema_version: number;
  prompt_version: string;
  provider: string;
  model: string;
  status: string;
  confidence: number;
  chapter_function: string;
  chapter_summary: string;
  hook_type: string;
  hook_intensity: number;
  error_message: string;
  llm_call_id: string;
  created_at: string;
  updated_at: string;
}

export interface AnalysisResultView {
  schema_version: number;
  confidence: number;
  ambiguities: string[];
  genre: string;
  subgenre: string;
  chapter_function: string;
  pacing: string;
  scene_count: number;
  point_of_view: string;
  conflict: Record<string, unknown>;
  emotion: Record<string, unknown>;
  suspense: Record<string, unknown>;
  state_changes: Record<string, unknown>;
  foreshadowing: Record<string, unknown>;
  text_stats: Record<string, unknown>;
  chapter_summary: string;
}

export interface AnalysisTaskItem {
  id: string;
  task_id: string;
  chapter_id: string;
  chapter_index: number;
  chapter_title: string;
  status: string;
  analysis_id: string;
  error_message: string;
  retry_count: number;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface AnalysisTask {
  id: string;
  document_id: string;
  project_id: string;
  status: string;
  total_items: number;
  completed_items: number;
  failed_items: number;
  skipped_items: number;
  prompt_version: string;
  error_message: string;
  summary: string;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
  progress_percent: number;
}

export interface AnalysisTaskDetail extends AnalysisTask {
  items: AnalysisTaskItem[];
}

export interface Character {
  id: string;
  project_id: string;
  name: string;
  aliases: string;
  age: string;
  identity: string;
  appearance: string;
  personality: string;
  desire: string;
  fear: string;
  current_goal: string;
  long_term_goal: string;
  abilities: string;
  weaknesses: string;
  current_location: string;
  physical_status: string;
  known_information: string;
  unknown_information: string;
  last_appeared_chapter: string;
  source_status: string;
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface WorldRule {
  id: string;
  project_id: string;
  name: string;
  category: string;
  description: string;
  scope: string;
  exceptions: string;
  examples: string;
  source_status: string;
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface PlotThread {
  id: string;
  project_id: string;
  title: string;
  thread_type: string;
  description: string;
  characters_involved: string;
  start_chapter: string;
  current_status: string;
  resolution: string;
  resolution_chapter: string;
  source_status: string;
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface Foreshadowing {
  id: string;
  project_id: string;
  content: string;
  planted_chapter: string;
  evidence: string;
  expected_payoff_range: string;
  actual_payoff_chapter: string;
  status: string;
  related_characters: string;
  related_plot_threads: string;
  source_status: string;
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface CreativeSession {
  id: string;
  project_id: string;
  one_line_idea: string;
  genre: string;
  target_platform: string;
  target_reader: string;
  expected_length: string;
  preferred_pacing: string;
  forbidden_content: string;
  gene_tags: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface CreativeDirection {
  id: string;
  session_id: string;
  project_id: string;
  direction_index: number;
  status: string;
  one_line_hook: string;
  core_reader_promise: string;
  protagonist_identity: string;
  protagonist_goal: string;
  core_ability: string;
  ability_cost: string;
  core_conflict: string;
  world_mystery: string;
  growth_cycle: string;
  resource_cycle: string;
  payoff_cycle: string;
  long_term_suspense: string;
  difference_from_tropes: string;
  homogenization_risk: string;
  sustainable_length: string;
  potential_collapse_point: string;
  rejection_reason: string;
  created_at: string;
  updated_at: string;
}

export interface VolumeOutline {
  id: string;
  project_id: string;
  synopsis_id: string;
  volume_index: number;
  volume_name: string;
  status: string;
  is_current: boolean;
  volume_goal: string;
  core_conflict: string;
  start_state: string;
  end_state: string;
  main_enemy: string;
  character_changes: string;
  new_world_settings: string;
  growth_milestone: string;
  payoff_climax: string;
  volume_twist: string;
  foreshadow_planted: string;
  foreshadow_resolved: string;
  reader_promise_fulfilled: string;
  estimated_chapters: number;
  estimated_words: number;
  ai_original_json: string;
  human_edits_json: string;
  created_at: string;
  updated_at: string;
}

export interface StateChangeCandidate {
  id: string;
  draft_id: string;
  project_id: string;
  change_type: string;
  entity_name: string;
  before_value: string;
  after_value: string;
  reason: string;
  source_chapter: string;
  source_version_id: string;
  status: string;
  rejection_reason: string;
  applied_bible_id: string;
  applied_bible_table: string;
  created_at: string;
  updated_at: string;
}

export interface DraftVersion {
  id: string;
  draft_id: string;
  project_id: string;
  version_index: number;
  version_type: string;
  body_text: string;
  source: string;
  model: string;
  prompt_version: string;
  word_count: number;
  is_final: boolean;
  parent_version_id: string | null;
  diff_summary: string;
  llm_call_id: string;
  created_at: string;
}

export interface ChapterDraft {
  id: string;
  project_id: string;
  plan_id: string;
  draft_type: string;
  target_words: number;
  person: string;
  pov: string;
  dialogue_density: string;
  description_density: string;
  pacing: string;
  emotion_intensity: string;
  paragraph_length: string;
  language_strictness: string;
  hook_strength: string;
  body_text: string;
  chapter_summary: string;
  actual_word_count: number;
  new_character_candidates_json: string;
  new_setting_candidates_json: string;
  state_change_candidates_json: string;
  foreshadow_candidates_json: string;
  facts_to_confirm_json: string;
  status: string;
  llm_call_id: string;
  created_at: string;
  updated_at: string;
}

export interface ChapterPlan {
  id: string;
  project_id: string;
  rhythm_id: string;
  plan_index: number;
  status: string;
  is_adopted: boolean;
  chapter_goal: string;
  characters: string;
  scenes: string;
  obstacle: string;
  turning_point: string;
  information_gain: string;
  emotion_curve: string;
  payoff: string;
  foreshadow_action: string;
  foreshadow_resolved: string;
  relationship_changes: string;
  end_state: string;
  chapter_hook: string;
  repetition_risk: string;
  logic_issues: string;
  ai_original_json: string;
  human_edits_json: string;
  locked_fields_json: string;
  created_at: string;
  updated_at: string;
}

export interface ChapterRhythmPlan {
  id: string;
  project_id: string;
  volume_id: string;
  chapter_index: number;
  status: string;
  is_current: boolean;
  temp_title: string;
  chapter_function: string;
  core_event: string;
  protagonist_goal: string;
  main_obstacle: string;
  conflict_type: string;
  information_gain: string;
  character_change: string;
  payoff_or_emotion: string;
  foreshadow_action: string;
  chapter_hook: string;
  volume_goal_connection: string;
  estimated_words: number;
  risk_notes: string;
  ai_original_json: string;
  human_edits_json: string;
  created_at: string;
  updated_at: string;
}

export interface NovelSynopsis {
  id: string;
  project_id: string;
  direction_id: string;
  version: number;
  is_current: boolean;
  status: string;
  one_liner: string;
  core_selling_point: string;
  protagonist_start: string;
  final_goal: string;
  core_conflict: string;
  story_phases: string;
  growth_arc: string;
  main_antagonist: string;
  relationship_changes: string;
  world_truth: string;
  key_foreshadowings: string;
  reader_promise_plan: string;
  ending: string;
  risk_warnings: string;
  ai_original_json: string;
  human_edits_json: string;
  created_at: string;
  updated_at: string;
}

export interface BibleCandidate {
  id: string;
  project_id: string;
  direction_id: string;
  category: string;
  title: string;
  content_json: string;
  source_status: string;
  status: string;
  confirmed_at: string | null;
  applied_bible_id: string;
  rejection_reason: string;
  created_at: string;
  updated_at: string;
}

export interface ProviderInfo {
  name: string;
  model: string;
  status: string;
  details?: Record<string, unknown>;
}

export interface ProviderHealth {
  status: string;
  provider: string;
  model: string;
  latency_ms: number;
  error?: string | null;
}

export interface MockTestResult {
  success: boolean;
  test_type: string;
  response?: string | null;
  error?: string | null;
  latency_ms: number;
  log_id?: string | null;
}

export interface CallLog {
  id: string;
  provider: string;
  model: string;
  task_type: string;
  status: string;
  input_tokens: number;
  output_tokens: number;
  estimated_cost: number;
  latency_ms: number;
  error_message: string;
}

export const api = {
  health: () => request<HealthResponse>("/health"),
  systemInfo: () => request<Record<string, unknown>>("/api/v1/system/info"),

  // Projects
  listProjects: (params?: {
    search?: string;
    genre?: string;
    status?: string;
    audience_type?: string;
    include_archived?: boolean;
    sort_by?: string;
    sort_order?: string;
    page?: number;
    page_size?: number;
  }) => {
    const qs = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== "") qs.set(k, String(v));
      });
    }
    const query = qs.toString();
    return request<PaginatedResponse<Project>>(`/api/v1/projects${query ? `?${query}` : ""}`);
  },
  getProject: (id: string) => request<Project>(`/api/v1/projects/${id}`),
  createProject: (data: Record<string, unknown>) =>
    request<Project>("/api/v1/projects", { method: "POST", body: JSON.stringify(data) }),
  updateProject: (id: string, data: Record<string, unknown>) =>
    request<Project>(`/api/v1/projects/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  archiveProject: (id: string) =>
    request<Project>(`/api/v1/projects/${id}/archive`, { method: "POST" }),
  restoreProject: (id: string) =>
    request<Project>(`/api/v1/projects/${id}/restore`, { method: "POST" }),
  deleteProject: (id: string) =>
    request<void>(`/api/v1/projects/${id}`, { method: "DELETE" }),
  projectStats: () => request<ProjectStats>("/api/v1/projects/stats"),

  // Documents
  uploadDocument: async (
    file: File,
    meta: {
      project_id?: string;
      title?: string;
      source_name?: string;
      author_name?: string;
      rights_status?: string;
    } = {},
  ) => {
    const form = new FormData();
    form.append("file", file);
    if (meta.project_id) form.append("project_id", meta.project_id);
    if (meta.title) form.append("title", meta.title);
    if (meta.source_name) form.append("source_name", meta.source_name);
    if (meta.author_name) form.append("author_name", meta.author_name);
    if (meta.rights_status) form.append("rights_status", meta.rights_status);

    const res = await fetch(`${API_BASE}/api/v1/documents`, { method: "POST", body: form });
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(body.detail || body.error || `Upload error ${res.status}`);
    }
    return res.json() as Promise<Document>;
  },

  listDocuments: (params?: { project_id?: string; rights_status?: string }) => {
    const qs = new URLSearchParams();
    if (params?.project_id) qs.set("project_id", params.project_id);
    if (params?.rights_status) qs.set("rights_status", params.rights_status);
    const query = qs.toString();
    return request<Document[]>(`/api/v1/documents${query ? `?${query}` : ""}`);
  },
  getDocument: (id: string) => request<Document>(`/api/v1/documents/${id}`),
  deleteDocument: (id: string) => request<void>(`/api/v1/documents/${id}`, { method: "DELETE" }),

  // Chapters
  parsePreview: (docId: string) =>
    request<ParsePreview>(`/api/v1/documents/${docId}/chapters/parse-preview`),
  parseDocument: (docId: string) =>
    request<Chapter[]>(`/api/v1/documents/${docId}/chapters/parse`, { method: "POST" }),
  listChapters: (docId: string) =>
    request<Chapter[]>(`/api/v1/documents/${docId}/chapters`),
  getChapter: (docId: string, chapterId: string) =>
    request<ChapterDetail>(`/api/v1/documents/${docId}/chapters/${chapterId}`),
  updateChapter: (docId: string, chapterId: string, data: Record<string, unknown>) =>
    request<Chapter>(`/api/v1/documents/${docId}/chapters/${chapterId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  mergeChapters: (docId: string, chapterIds: string[], newTitle?: string) =>
    request<Chapter>(`/api/v1/documents/${docId}/chapters/merge`, {
      method: "POST",
      body: JSON.stringify({ chapter_ids: chapterIds, new_title: newTitle }),
    }),
  splitChapter: (docId: string, chapterId: string, position: number, newTitle: string) =>
    request<Chapter[]>(`/api/v1/documents/${docId}/chapters/${chapterId}/split`, {
      method: "POST",
      body: JSON.stringify({ split_position: position, new_title: newTitle }),
    }),
  deleteChapter: (docId: string, chapterId: string) =>
    request<void>(`/api/v1/documents/${docId}/chapters/${chapterId}`, { method: "DELETE" }),

  // Analyses
  triggerAnalysis: (chapterId: string, promptVersion = "v1") =>
    request<AnalysisOut>(`/api/v1/chapters/${chapterId}/analyses`, {
      method: "POST",
      body: JSON.stringify({ prompt_version: promptVersion }),
    }),
  listAnalyses: (chapterId: string) =>
    request<AnalysisOut[]>(`/api/v1/chapters/${chapterId}/analyses`),
  getLatestAnalysis: (chapterId: string) =>
    request<AnalysisOut | null>(`/api/v1/chapters/${chapterId}/analyses/latest`),
  getAnalysisResult: (chapterId: string, analysisId: string) =>
    request<AnalysisResultView>(`/api/v1/chapters/${chapterId}/analyses/${analysisId}/result`),

  // Tasks (batch analysis)
  createTask: (chapterIds: string[], promptVersion = "v1") =>
    request<AnalysisTask>("/api/v1/tasks", {
      method: "POST",
      body: JSON.stringify({ chapter_ids: chapterIds, prompt_version: promptVersion }),
    }),
  listTasks: (documentId?: string) => {
    const qs = documentId ? `?document_id=${documentId}` : "";
    return request<AnalysisTask[]>(`/api/v1/tasks${qs}`);
  },
  getTask: (taskId: string) => request<AnalysisTaskDetail>(`/api/v1/tasks/${taskId}`),
  cancelTask: (taskId: string) =>
    request<AnalysisTask>(`/api/v1/tasks/${taskId}/cancel`, { method: "POST" }),
  retryTask: (taskId: string, itemIds: string[]) =>
    request<AnalysisTask>(`/api/v1/tasks/${taskId}/retry`, {
      method: "POST",
      body: JSON.stringify({ item_ids: itemIds }),
    }),

  // Providers
  listProviders: () => request<ProviderInfo[]>("/api/v1/providers"),
  providerHealth: () => request<ProviderHealth>("/api/v1/providers/health"),
  mockTest: (testType: string, message?: string) =>
    request<MockTestResult>("/api/v1/providers/mock/test", {
      method: "POST",
      body: JSON.stringify({ test_type: testType, message: message || "测试消息" }),
    }),
  listCallLogs: (limit = 20) => request<CallLog[]>(`/api/v1/providers/logs?limit=${limit}`),

  // Bible - Characters
  listCharacters: (projectId: string, params?: { source_status?: string; search?: string }) => {
    const qs = new URLSearchParams();
    if (params?.source_status) qs.set("source_status", params.source_status);
    if (params?.search) qs.set("search", params.search);
    const query = qs.toString();
    return request<Character[]>(`/api/v1/projects/${projectId}/characters${query ? `?${query}` : ""}`);
  },
  createCharacter: (projectId: string, data: Record<string, unknown>) =>
    request<Character>(`/api/v1/projects/${projectId}/characters`, { method: "POST", body: JSON.stringify(data) }),
  updateCharacter: (projectId: string, id: string, data: Record<string, unknown>) =>
    request<Character>(`/api/v1/projects/${projectId}/characters/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteCharacter: (projectId: string, id: string) =>
    request<void>(`/api/v1/projects/${projectId}/characters/${id}`, { method: "DELETE" }),

  // Bible - World Rules
  listWorldRules: (projectId: string, params?: { source_status?: string }) => {
    const qs = params?.source_status ? `?source_status=${params.source_status}` : "";
    return request<WorldRule[]>(`/api/v1/projects/${projectId}/world-rules${qs}`);
  },
  createWorldRule: (projectId: string, data: Record<string, unknown>) =>
    request<WorldRule>(`/api/v1/projects/${projectId}/world-rules`, { method: "POST", body: JSON.stringify(data) }),
  updateWorldRule: (projectId: string, id: string, data: Record<string, unknown>) =>
    request<WorldRule>(`/api/v1/projects/${projectId}/world-rules/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteWorldRule: (projectId: string, id: string) =>
    request<void>(`/api/v1/projects/${projectId}/world-rules/${id}`, { method: "DELETE" }),

  // Bible - Plot Threads
  listPlotThreads: (projectId: string) =>
    request<PlotThread[]>(`/api/v1/projects/${projectId}/plot-threads`),
  createPlotThread: (projectId: string, data: Record<string, unknown>) =>
    request<PlotThread>(`/api/v1/projects/${projectId}/plot-threads`, { method: "POST", body: JSON.stringify(data) }),
  updatePlotThread: (projectId: string, id: string, data: Record<string, unknown>) =>
    request<PlotThread>(`/api/v1/projects/${projectId}/plot-threads/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deletePlotThread: (projectId: string, id: string) =>
    request<void>(`/api/v1/projects/${projectId}/plot-threads/${id}`, { method: "DELETE" }),

  // Bible - Foreshadowings
  listForeshadowings: (projectId: string) =>
    request<Foreshadowing[]>(`/api/v1/projects/${projectId}/foreshadowings`),
  createForeshadowing: (projectId: string, data: Record<string, unknown>) =>
    request<Foreshadowing>(`/api/v1/projects/${projectId}/foreshadowings`, { method: "POST", body: JSON.stringify(data) }),
  updateForeshadowing: (projectId: string, id: string, data: Record<string, unknown>) =>
    request<Foreshadowing>(`/api/v1/projects/${projectId}/foreshadowings/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteForeshadowing: (projectId: string, id: string) =>
    request<void>(`/api/v1/projects/${projectId}/foreshadowings/${id}`, { method: "DELETE" }),

  // Creative Directions
  generateDirections: (projectId: string, data: Record<string, unknown>) =>
    request<CreativeDirection[]>(`/api/v1/projects/${projectId}/creative/generate`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  listCreativeSessions: (projectId: string) =>
    request<CreativeSession[]>(`/api/v1/projects/${projectId}/creative/sessions`),
  listSessionDirections: (projectId: string, sessionId: string) =>
    request<CreativeDirection[]>(`/api/v1/projects/${projectId}/creative/sessions/${sessionId}/directions`),
  editDirection: (projectId: string, directionId: string, data: Record<string, unknown>) =>
    request<CreativeDirection>(`/api/v1/projects/${projectId}/creative/directions/${directionId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  acceptDirection: (projectId: string, directionId: string) =>
    request<CreativeDirection>(`/api/v1/projects/${projectId}/creative/directions/${directionId}/accept`, {
      method: "POST",
    }),
  rejectDirection: (projectId: string, directionId: string) =>
    request<CreativeDirection>(`/api/v1/projects/${projectId}/creative/directions/${directionId}/reject`, {
      method: "POST",
    }),
  mergeDirections: (projectId: string, sourceIds: string[], fieldSources: Record<string, string>) =>
    request<CreativeDirection>(`/api/v1/projects/${projectId}/creative/merge`, {
      method: "POST",
      body: JSON.stringify({ source_ids: sourceIds, field_sources: fieldSources }),
    }),

  // Bible Candidates
  generateBibleCandidates: (projectId: string, directionId: string) =>
    request<BibleCandidate[]>(`/api/v1/projects/${projectId}/bible-candidates/generate`, {
      method: "POST",
      body: JSON.stringify({ direction_id: directionId }),
    }),
  listBibleCandidates: (projectId: string, params?: { category?: string; status?: string; direction_id?: string }) => {
    const qs = new URLSearchParams();
    if (params?.category) qs.set("category", params.category);
    if (params?.status) qs.set("status", params.status);
    if (params?.direction_id) qs.set("direction_id", params.direction_id);
    const query = qs.toString();
    return request<BibleCandidate[]>(`/api/v1/projects/${projectId}/bible-candidates${query ? `?${query}` : ""}`);
  },
  approveBibleCandidate: (projectId: string, candidateId: string) =>
    request<BibleCandidate>(`/api/v1/projects/${projectId}/bible-candidates/${candidateId}/approve`, { method: "POST" }),
  rejectBibleCandidate: (projectId: string, candidateId: string, reason = "") =>
    request<BibleCandidate>(`/api/v1/projects/${projectId}/bible-candidates/${candidateId}/reject`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    }),
  applyBibleCandidates: (projectId: string, candidateIds: string[]) =>
    request<{ applied: number; errors: string[] }>(`/api/v1/projects/${projectId}/bible-candidates/apply`, {
      method: "POST",
      body: JSON.stringify(candidateIds),
    }),
  undoBibleCandidate: (projectId: string, candidateId: string) =>
    request<BibleCandidate>(`/api/v1/projects/${projectId}/bible-candidates/${candidateId}/undo`, { method: "POST" }),

  // Synopses
  generateSynopsis: (projectId: string, directionId: string) =>
    request<NovelSynopsis>(`/api/v1/projects/${projectId}/synopses/generate`, {
      method: "POST",
      body: JSON.stringify({ direction_id: directionId }),
    }),
  listSynopses: (projectId: string) =>
    request<NovelSynopsis[]>(`/api/v1/projects/${projectId}/synopses`),
  getCurrentSynopsis: (projectId: string) =>
    request<NovelSynopsis | null>(`/api/v1/projects/${projectId}/synopses/current`),
  getSynopsis: (projectId: string, synopsisId: string) =>
    request<NovelSynopsis>(`/api/v1/projects/${projectId}/synopses/${synopsisId}`),
  updateSynopsis: (projectId: string, synopsisId: string, data: Record<string, unknown>) =>
    request<NovelSynopsis>(`/api/v1/projects/${projectId}/synopses/${synopsisId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  adoptSynopsis: (projectId: string, synopsisId: string) =>
    request<NovelSynopsis>(`/api/v1/projects/${projectId}/synopses/${synopsisId}/adopt`, { method: "POST" }),
  restoreSynopsis: (projectId: string, synopsisId: string) =>
    request<NovelSynopsis>(`/api/v1/projects/${projectId}/synopses/${synopsisId}/restore`, { method: "POST" }),
  diffSynopsis: (projectId: string, synopsisId: string, compareWith: string) =>
    request<Record<string, unknown>>(`/api/v1/projects/${projectId}/synopses/${synopsisId}/diff?compare_with=${compareWith}`),

  // Volumes
  generateVolumes: (projectId: string, synopsisId: string) =>
    request<VolumeOutline[]>(`/api/v1/projects/${projectId}/volumes/generate`, {
      method: "POST",
      body: JSON.stringify({ synopsis_id: synopsisId }),
    }),
  listVolumes: (projectId: string, synopsisId?: string) => {
    const qs = synopsisId ? `?synopsis_id=${synopsisId}` : "";
    return request<VolumeOutline[]>(`/api/v1/projects/${projectId}/volumes${qs}`);
  },
  getVolume: (projectId: string, volumeId: string) =>
    request<VolumeOutline>(`/api/v1/projects/${projectId}/volumes/${volumeId}`),
  updateVolume: (projectId: string, volumeId: string, data: Record<string, unknown>) =>
    request<VolumeOutline>(`/api/v1/projects/${projectId}/volumes/${volumeId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  adoptVolume: (projectId: string, volumeId: string) =>
    request<VolumeOutline>(`/api/v1/projects/${projectId}/volumes/${volumeId}/adopt`, { method: "POST" }),
  regenerateVolume: (projectId: string, volumeId: string) =>
    request<VolumeOutline>(`/api/v1/projects/${projectId}/volumes/${volumeId}/regenerate`, { method: "POST" }),
  reorderVolumes: (projectId: string, volumeIds: string[]) =>
    request<VolumeOutline[]>(`/api/v1/projects/${projectId}/volumes/reorder`, {
      method: "POST",
      body: JSON.stringify({ volume_ids: volumeIds }),
    }),

  // Rhythm Plans
  generateRhythm: (projectId: string, volumeId: string, chapterCount = 10) =>
    request<ChapterRhythmPlan[]>(`/api/v1/projects/${projectId}/rhythms/generate`, {
      method: "POST",
      body: JSON.stringify({ volume_id: volumeId, chapter_count: chapterCount }),
    }),
  listRhythms: (projectId: string, volumeId?: string) => {
    const qs = volumeId ? `?volume_id=${volumeId}` : "";
    return request<ChapterRhythmPlan[]>(`/api/v1/projects/${projectId}/rhythms${qs}`);
  },
  getRhythm: (projectId: string, planId: string) =>
    request<ChapterRhythmPlan>(`/api/v1/projects/${projectId}/rhythms/${planId}`),
  updateRhythm: (projectId: string, planId: string, data: Record<string, unknown>) =>
    request<ChapterRhythmPlan>(`/api/v1/projects/${projectId}/rhythms/${planId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  adoptRhythm: (projectId: string, planId: string) =>
    request<ChapterRhythmPlan>(`/api/v1/projects/${projectId}/rhythms/${planId}/adopt`, { method: "POST" }),
  regenerateRhythm: (projectId: string, planId: string) =>
    request<ChapterRhythmPlan>(`/api/v1/projects/${projectId}/rhythms/${planId}/regenerate`, { method: "POST" }),
  insertRhythm: (projectId: string, afterIndex: number, title: string) =>
    request<ChapterRhythmPlan[]>(`/api/v1/projects/${projectId}/rhythms/insert`, {
      method: "POST",
      body: JSON.stringify({ after_index: afterIndex, temp_title: title }),
    }),
  deleteRhythm: (projectId: string, planId: string) =>
    request<ChapterRhythmPlan[]>(`/api/v1/projects/${projectId}/rhythms/${planId}`, { method: "DELETE" }),
  reorderRhythms: (projectId: string, planIds: string[]) =>
    request<ChapterRhythmPlan[]>(`/api/v1/projects/${projectId}/rhythms/reorder`, {
      method: "POST",
      body: JSON.stringify({ chapter_ids: planIds }),
    }),

  // Chapter Plans
  generateChapterPlans: (projectId: string, rhythmId: string) =>
    request<ChapterPlan[]>(`/api/v1/projects/${projectId}/chapter-plans/generate`, {
      method: "POST",
      body: JSON.stringify({ rhythm_id: rhythmId }),
    }),
  listChapterPlans: (projectId: string, rhythmId?: string) => {
    const qs = rhythmId ? `?rhythm_id=${rhythmId}` : "";
    return request<ChapterPlan[]>(`/api/v1/projects/${projectId}/chapter-plans${qs}`);
  },
  getChapterPlan: (projectId: string, planId: string) =>
    request<ChapterPlan>(`/api/v1/projects/${projectId}/chapter-plans/${planId}`),
  updateChapterPlan: (projectId: string, planId: string, data: Record<string, unknown>) =>
    request<ChapterPlan>(`/api/v1/projects/${projectId}/chapter-plans/${planId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  adoptChapterPlan: (projectId: string, planId: string) =>
    request<ChapterPlan>(`/api/v1/projects/${projectId}/chapter-plans/${planId}/adopt`, { method: "POST" }),
  rejectChapterPlan: (projectId: string, planId: string) =>
    request<ChapterPlan>(`/api/v1/projects/${projectId}/chapter-plans/${planId}/reject`, { method: "POST" }),
  regenerateChapterPlan: (projectId: string, planId: string) =>
    request<ChapterPlan>(`/api/v1/projects/${projectId}/chapter-plans/${planId}/regenerate`, { method: "POST" }),
  mergeChapterPlans: (projectId: string, sourceIds: string[], fieldSources: Record<string, string>) =>
    request<ChapterPlan>(`/api/v1/projects/${projectId}/chapter-plans/merge`, {
      method: "POST",
      body: JSON.stringify({ source_ids: sourceIds, field_sources: fieldSources }),
    }),

  // Drafts
  generateDraft: (projectId: string, planId: string, params?: Record<string, unknown>) =>
    request<ChapterDraft>(`/api/v1/projects/${projectId}/drafts/generate`, {
      method: "POST",
      body: JSON.stringify({ plan_id: planId, parameters: params || {} }),
    }),
  listDrafts: (projectId: string, planId?: string) => {
    const qs = planId ? `?plan_id=${planId}` : "";
    return request<ChapterDraft[]>(`/api/v1/projects/${projectId}/drafts${qs}`);
  },
  getDraft: (projectId: string, draftId: string) =>
    request<ChapterDraft>(`/api/v1/projects/${projectId}/drafts/${draftId}`),
  updateDraft: (projectId: string, draftId: string, bodyText: string) =>
    request<ChapterDraft>(`/api/v1/projects/${projectId}/drafts/${draftId}`, {
      method: "PATCH",
      body: JSON.stringify({ body_text: bodyText }),
    }),
  deleteDraft: (projectId: string, draftId: string) =>
    request<void>(`/api/v1/projects/${projectId}/drafts/${draftId}`, { method: "DELETE" }),

  // Draft Versions
  saveDraftVersion: (projectId: string, draftId: string, bodyText: string, versionType = "user_edit") =>
    request<DraftVersion>(`/api/v1/projects/${projectId}/draft-versions/save`, {
      method: "POST",
      body: JSON.stringify({ draft_id: draftId, body_text: bodyText, version_type: versionType }),
    }),
  listDraftVersions: (projectId: string, draftId: string) =>
    request<DraftVersion[]>(`/api/v1/projects/${projectId}/draft-versions?draft_id=${draftId}`),
  getDraftVersion: (projectId: string, versionId: string) =>
    request<DraftVersion>(`/api/v1/projects/${projectId}/draft-versions/${versionId}`),
  restoreDraftVersion: (projectId: string, versionId: string) =>
    request<DraftVersion>(`/api/v1/projects/${projectId}/draft-versions/${versionId}/restore`, { method: "POST" }),
  markDraftFinal: (projectId: string, versionId: string) =>
    request<DraftVersion>(`/api/v1/projects/${projectId}/draft-versions/${versionId}/mark-final`, { method: "POST" }),
  diffDraftVersions: (projectId: string, versionAId: string, versionBId: string) =>
    request<Record<string, unknown>>(`/api/v1/projects/${projectId}/draft-versions/diff`, {
      method: "POST",
      body: JSON.stringify({ version_a_id: versionAId, version_b_id: versionBId }),
    }),
  aiRewrite: (projectId: string, draftId: string, selectedText: string, instruction: string, mode = "rewrite") =>
    request<DraftVersion>(`/api/v1/projects/${projectId}/draft-versions/rewrite`, {
      method: "POST",
      body: JSON.stringify({ draft_id: draftId, selected_text: selectedText, instruction, mode }),
    }),

  // State Changes
  generateStateChanges: (projectId: string, draftId: string) =>
    request<StateChangeCandidate[]>(`/api/v1/projects/${projectId}/state-changes/generate`, {
      method: "POST",
      body: JSON.stringify({ draft_id: draftId }),
    }),
  listStateChanges: (projectId: string, params?: { draft_id?: string; status?: string }) => {
    const qs = new URLSearchParams();
    if (params?.draft_id) qs.set("draft_id", params.draft_id);
    if (params?.status) qs.set("status", params.status);
    const query = qs.toString();
    return request<StateChangeCandidate[]>(
      `/api/v1/projects/${projectId}/state-changes${query ? `?${query}` : ""}`,
    );
  },
  acceptStateChange: (projectId: string, candidateId: string) =>
    request<StateChangeCandidate>(
      `/api/v1/projects/${projectId}/state-changes/${candidateId}/accept`,
      { method: "POST" },
    ),
  rejectStateChange: (projectId: string, candidateId: string, reason = "") =>
    request<StateChangeCandidate>(
      `/api/v1/projects/${projectId}/state-changes/${candidateId}/reject`,
      { method: "POST", body: JSON.stringify({ reason }) },
    ),
  undoStateChange: (projectId: string, candidateId: string) =>
    request<StateChangeCandidate>(
      `/api/v1/projects/${projectId}/state-changes/${candidateId}/undo`,
      { method: "POST" },
    ),
};
