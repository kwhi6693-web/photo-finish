"""Truthful user copy over controller facts. Never invokes an editor or claims a review."""
MESSAGES = {
 'SELECT_REFERENCES_AND_DIRECTION':('已读取原片，正在确定处理方向。','按原任务继续确定方向'),
 'ASSESS_PROTECTION':('已读取原片，正在确定保护要求。','保留人物、文字及指定内容后继续'),
 'MATCH_REFERENCES':('已读取原片，正在查找适用参考。','继续匹配或按专业判断处理'),
 'SELECT_REFERENCES':('参考已找到，等待实际查看并确定方向。','查看适用参考后继续'),
 'RENDER':('正在准备修图。','登记任务后调用图像工具'),
 'POLL_RENDER':('修图仍在进行，我会继续查询原任务。','继续查询原任务'),
 'INVESTIGATE_RENDER':('修图结果暂未确认，已保留原任务，不会重复生成。','查询原任务结果'),
 'FETCH_OUTPUT':('工具已返回结果，正在准备取得正式成片。','取回原结果，不重新修图'),
 'WAIT_TRANSFER_RECOVERY':('正式成片尚未取回，已保留原结果入口。','恢复下载原结果，不重新修图'),
 'REVIEW_OUTPUT':('成片已取得，等待检查人物、文字和细节。','实际查看全幅及受影响细节'),
 'FIX_REVIEW':('成片检查尚未通过，已保留现有结果。','针对未通过项修正并复核'),
 'VERIFY_AND_ACCEPT':('已记录检查结果，正在核对交付条件。','核对保护要求和正式文件'),
 'AWAIT_PLATFORM_SAVE_CONFIRMATION':('成片已生成，保存状态待确认。','取得真实保存回执后核对，无需等待或重复上传'),
 'PREPARE_PHOTO_SAVE':('成片已生成，等待保存。','保存已有成片'),
 'SAVE_PHOTO':('成片已生成，等待保存。','按原保存任务继续'),
 'INVESTIGATE_PHOTO_SAVE':('成片已保留，保存结果待确认；不需要重新修图。','核对原保存结果后重新保存'),
 'COMPLETE_PHOTO_SAVE':('已取得保存回执，等待核对。','核对原成片与回执'),
 'BUILD_RECORD':('成片已保存，正在整理交付记录。','保留现有成片并完成记录'),
 'PREPARE_RECORD_SAVE':('成片已保存，等待保存交付记录。','保存已有记录'),
 'SAVE_RECORD':('成片已保存，等待保存交付记录。','继续原记录保存任务'),
 'INVESTIGATE_RECORD_SAVE':('成片已保存，交付记录保存尚未确认。','核对原记录保存结果'),
 'CONFIRM_RECORD_SAVE':('成片已保存，等待核对交付记录回执。','核对已有记录回执'),
 'DELIVER':('成片已保存。','可继续精修或查看历史版本'),
 'RESTART_CONTEXT':('任务上下文或参考文件发生变化，已保留原任务。','核对变化后创建关联的新任务，不重复提交原任务'),
 'STOP':('当前任务已停止或历史文件需要核对，已保留任务记录。','核对原文件和状态后选择恢复方式'),
}
HINT='可以继续回复：更自然｜氛围更强｜保持构图只调色｜局部修改｜看前后对比'


def describe(state, action, *, manual_presented=False):
    """Current explicit confirmation is response-scoped, never persisted or inferred."""
    if type(manual_presented) is not bool:
        raise ValueError('Manual presentation confirmation must be boolean')
    platform=state.get('platform_delivery') or {}
    platform_observed=platform.get('display',{}).get('status')=='observed'
    accepted=state['status']=='accepted'
    saved=accepted and bool(state.get('delivery_receipt'))
    generated=bool((state.get('render_result') or {}).get('acquired')) or accepted
    message,recovery=MESSAGES.get(action,('任务状态尚未确认，已保留记录。','查询原任务状态'))
    # Copy cannot upgrade missing evidence, even if an inconsistent caller supplies an action.
    if action in ('BUILD_RECORD','PREPARE_RECORD_SAVE','SAVE_RECORD','INVESTIGATE_RECORD_SAVE','CONFIRM_RECORD_SAVE','DELIVER') and not saved:
        message='成片已生成，保存状态待确认。' if generated else '任务状态尚未确认，已保留记录。'
    return {'message':message,'recovery':recovery,'render_retry_allowed':False,
            'generated':generated,'quality_accepted':accepted,
            'display_observed':manual_presented or platform_observed,
            'display_observation_source':'current_manual_confirmation' if manual_presented else ('platform_delivery' if platform_observed else 'unobserved'),
            'display_observation_scope':'current_delivery_response' if manual_presented else 'platform_ledger',
            'persistence_confirmed':saved,
            'save_message':'成片已保存。' if saved else ('成片已生成，保存状态待确认。' if generated else None)}


def hint(state, new_delivery=False, enabled=True):
    return HINT if state['status']=='accepted' and new_delivery and enabled else ''


def shortcut(text):
    if text=='局部修改':return {'action':'clarify_local','message':'请说要修改的区域和目标，例如“只改天空，让层次更明显”。'}
    if text=='看前后对比':return {'action':'compare_existing'}
    if text=='更自然':return {'action':'revise','instruction':'修正过度处理、涂抹和假纹理，保留真实材质及已认可方向。'}
    if text=='氛围更强':return {'action':'revise','instruction':'加强已选情绪的光影和层次，遵守原片事实与保护要求，不固定套用暖金、高饱和或HDR。'}
    if text=='保持构图只调色':return {'action':'revise','instruction':'保持构图，只调整光色。','protect':'构图、人物、文字及已认可方向保持不变；工具不能保证时如实说明。'}
    return {'action':'revise','instruction':text}


def failure(error):
    text=str(error).casefold()
    if any(word in text for word in ('changed','stale','hash','reference')):
        message='原片、参考或任务信息需要核对，已保留现有记录。'
        recovery='核对当前文件与原任务，不重复提交'
    elif any(word in text for word in ('save','snapshot','receipt')):
        message='保存或记录结果尚未确认，请核对原结果；不需要重新修图。'
        recovery='核对原回执或恢复已有文件保存'
    else:
        message='本次操作尚未完成，请核对任务状态和输入；不会据此重复生成。'
        recovery='查询原任务并修正提示的输入或文件问题'
    return {'message':message,'recovery':recovery,'render_retry_allowed':False}
