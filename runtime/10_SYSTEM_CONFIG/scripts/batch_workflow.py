"""Batch metadata and recovery around independent actual jobs. No renderer/concurrency."""
from pathlib import Path
import json,uuid
import workflow_session as w
import delivery_automation as a
import experience
import task_history as h


def create(session_root, paths):
    if not isinstance(paths,list) or not paths or len(paths)>500:raise ValueError('Provide 1 through 500 ordered job paths')
    jobs=[str(Path(p).resolve(strict=True)) for p in paths]
    if len(set(jobs))!=len(jobs):raise ValueError('Duplicate batch job')
    sources=[w._load(p)['source'] for p in jobs]
    batch_id=uuid.uuid4().hex
    with h._index(session_root,True) as db:
        db.execute('CREATE TABLE IF NOT EXISTS batches (id TEXT PRIMARY KEY, entries TEXT, hint_claimed INTEGER DEFAULT 0)')
        db.execute('INSERT INTO batches(id,entries) VALUES(?,?)',(batch_id,json.dumps([dict(path=p,source=s) for p,s in zip(jobs,sources)])))
    return {'batch_id':batch_id,'total':len(jobs),'message':'本批 '+str(len(jobs))+' 张，按上传顺序逐张处理。'}


def _entries(db,batch_id):
    row=db.execute('SELECT entries FROM batches WHERE id=?',(batch_id,)).fetchone()
    if row is None:raise ValueError('Unknown batch in this conversation')
    return json.loads(row[0])


def _item(entry):
    path=entry['path']
    try:
        state=w._load(path);render=state.get('render_result') or {}
        if state['source']!=entry['source']:raise ValueError('Batch source binding changed')
        if w._file(state['source']['path'])!=entry['source']:raise ValueError('Batch source file changed')
        retryable=False
        if state['status']=='accepted':
            if w._file(state['output']['path'])!=state['output']:raise ValueError('Accepted batch output changed')
            label='已完成';reason='成片已接受；'+('已保存' if state.get('delivery_receipt') else '保存待确认')
        elif render.get('status')=='unknown':label='需确认';reason='原提交结果尚未确认，请查询原任务，不重复生成'
        elif render.get('status')=='working':label='处理中';reason='继续查询原任务'
        elif state['status']=='failed':
            # A closed ledger alone cannot prove that an external invocation failed.
            retryable=not render
            label='失败' if retryable else '需确认'
            reason='未发生渲染提交，可创建新任务恢复' if retryable else '原提交需调查，不能自动重试'
        elif state['status']=='cancelled':label='需确认';reason='用户取消的任务，等待明确选择'
        elif render.get('status')=='ready':label='处理中';reason='原结果待取回或待实际检查，不重新生成'
        else:label='待处理';reason='任务已准备'
        return dict(path=path,status=label,reason=reason,retryable=retryable,save_confirmed=bool(state.get('delivery_receipt')))
    except (OSError,ValueError,KeyError) as error:
        return dict(path=path,status='需确认',reason='文件或任务状态需要核对：'+str(error),retryable=False,save_confirmed=False)


def summary(session_root,batch_id):
    with h._index(session_root) as db:entries=_entries(db,batch_id)
    items=[_item(entry) for entry in entries]
    counts={key:sum(x['status']==key for x in items) for key in ('待处理','处理中','已完成','需确认','失败')}
    return {'batch_id':batch_id,'total':len(items),'counts':counts,'items':items,
            'message':f"本批 {len(items)} 张：{counts['已完成']} 张已完成，{counts['失败']} 张失败，{counts['需确认']} 张需确认。",
            'recovery':'只重试已确认失败项；未知结果先查询原任务，已完成照片不重新生成。'}


def retry_failed(session_root,batch_id,consent=False):
    """Prepare separate replacements only for tasks proven never submitted.

    Existing working/unknown/ready calls are excluded. External failures require
    investigation and explicit source-bound evidence before a new task is considered.
    """
    import photo_edit
    if consent is not True:raise ValueError('Explicit request to retry failed batch items required')
    prepared=[];errors=[]
    with h._index(session_root,True) as db:
        entries=_entries(db,batch_id)
        for entry in entries:
            if not _item(entry)['retryable']:continue
            old=w._load(entry['path']);target=Path(entry['path']).with_name('retry-'+uuid.uuid4().hex+'.json')
            try:
                result=photo_edit.prepare(old['context']['project_root'],old['source']['path'],target,
                      evaluation_kind=old.get('evaluation',{}).get('kind','unclassified'),
                      scenario=old.get('evaluation',{}).get('scenario'),
                      style_library_root=old.get('reference_query',{}).get('personal_library',{}).get('root'),
                      observed_profile_sha256=(old.get('user_customization') or {}).get('profile_sha256'),
                      task_instructions=(old.get('user_customization') or {}).get('task_instructions'))
                state=w._load(target);state['retry_of']={'path':entry['path'],'source':old['source'],'reason':'Explicit retry of a failed task with no external submission'}
                w._save(target,state)
                prepared.append(dict(path=str(target),retry_of=entry['path'],next=result['next']))
                entry['previous_paths']=entry.get('previous_paths',[])+[entry['path']];entry['path']=str(target)
            except (OSError,ValueError,KeyError,TypeError) as error:errors.append({'path':entry['path'],'error':str(error)})
        db.execute('UPDATE batches SET entries=? WHERE id=?',(json.dumps(entries),batch_id))
    return {'prepared':prepared,'errors':errors,'render_calls':0,'next':'Apply original protections and current applicable rules, then execute each prepared task normally'}


def completed(session_root,batch_id):
    result=summary(session_root,batch_id)
    if result['counts']['待处理'] or result['counts']['处理中']:
        return dict(result,hint='')
    with h._index(session_root,True) as db:
        enabled=db.execute('SELECT value FROM session WHERE key=?',('hints',)).fetchone()
        changed=db.execute('UPDATE batches SET hint_claimed=1 WHERE id=? AND hint_claimed=0',(batch_id,)).rowcount
    return dict(result,hint=experience.HINT if changed and result['counts']['已完成'] and (enabled is None or json.loads(enabled[0])) else '')
