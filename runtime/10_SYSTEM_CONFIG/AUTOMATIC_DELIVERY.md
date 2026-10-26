# 实际交付与恢复

当前编排2026-10-26.2。新任务统一使用[工具与交付接口](DELIVERY_ADAPTER.md)，完整字段仅在该处维护。助手实际看图、调用工具、逐目标复核；控制器不自动作审美结论。

1. prepare核验现行来源、政策和总规范；同任务复用上下文，变化新建任务复核，不静默放宽保护。
2. photo_edit.prepare合并接入/意图/候选；实际参考取舍后submit合并protect/select/问题与begin；实际调用两侧计时，returned合并finish与正式文件检查；实际看图后review合并明确证据/验收/可选快照。平台正式本地文件直接接入，不重传生成图。
3. working只轮询原taskId；unknown/error保持调查，不自动重发。下载失败最多一次有界重试，不重渲染。精修next-step仅从最新已取得且已实际复核输出续接。
4. 展示、用途验收及保存确认分开。platform_auto无真实保存回执时为pending_confirmation，保存内部待确认snapshot后结束回合，不等待、重传或伪造完成；未安装后台回调。后续独立可得的真实权威证据才confirm-platform-save。
5. manual保留save-intent及真实成功回执；confirmed平台或manual均用complete生成/复用最终记录，再record-intent/record-saved保存。DELIVER代表两项真实归档确认，display_needed=false不重复展示先前自动显示的图片。

plan只读，失败/取消历史不重开，已完成历史回执不改写。普通EDIT不跑系统回归、报告、全库导出或82项研究。默认逐张交付最终成片及简短版本/保存状态，新成片首次交付一行可选返工提示（批量末尾统一一次），不附原片、对比或说明。
