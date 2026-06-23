# Novel Forge — 当前状态

最后更新：2026-06-23

## 已完成阶段

- 阶段一～十八：（见 development-roadmap.md）
- 阶段十九：正文状态变化提取与人工确认 ✅ ← 本阶段

## 状态变化提取与确认功能

### 后端
- StateChangeCandidate 模型（14 种变化类型）
- AI 提取候选（mock 数据含 8 种不同变化）
- 接受：自动更新小说圣经（位置/伤势/目标/知情范围→人物表，新增人物/伏笔/规则→对应表，剧情推进→剧情线表）
- 拒绝：记录原因，避免重复提示
- 撤销：删除圣经条目，重置为 pending
- 事务保护（部分成功/失败明确）
- 记录来源章节和版本

### 前端
- /projects/[id]/drafts/[draftId]/changes：状态变化页面
  - 从正文提取按钮
  - 按状态筛选
  - 每项显示变化类型、实体、前后值、原因
  - 接受/拒绝/撤销按钮
  - 颜色标签区分状态

### 测试
- 12 个新测试

## API 端点
| 方法 | 路径 | 说明 |
|---|---|---|
| POST | /api/v1/projects/:id/state-changes/generate | 提取候选 |
| GET | /api/v1/projects/:id/state-changes | 候选列表 |
| POST | /api/v1/projects/:id/state-changes/:cid/accept | 接受 |
| POST | /api/v1/projects/:id/state-changes/:cid/reject | 拒绝 |
| POST | /api/v1/projects/:id/state-changes/:cid/undo | 撤销 |
