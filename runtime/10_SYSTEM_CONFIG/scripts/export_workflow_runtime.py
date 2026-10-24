"""Export master policy and verified controller/context; no photos or numerical recomputation."""
from pathlib import Path
import hashlib,json,zipfile
from workflow_session import bootstrap
FILES=(
 '我的照片美化偏好与修图标准.md',
 '10_SYSTEM_CONFIG/scripts/workflow_session.py',
 '10_SYSTEM_CONFIG/scripts/photo_workflow.py',
 '10_SYSTEM_CONFIG/scripts/photo_edit.py',
 '10_SYSTEM_CONFIG/scripts/review_contract.py',
 '10_SYSTEM_CONFIG/scripts/delivery_metrics.py',
 '10_SYSTEM_CONFIG/scripts/style_match.py',
 '10_SYSTEM_CONFIG/scripts/style_library.py',
 '10_SYSTEM_CONFIG/scripts/user_preferences.py',
 '10_SYSTEM_CONFIG/scripts/personal_backup.py',
 '10_SYSTEM_CONFIG/scripts/reference_semantics.py',
 '10_SYSTEM_CONFIG/scripts/delivery_adapter.py',
 '10_SYSTEM_CONFIG/scripts/input_references.py',
 '10_SYSTEM_CONFIG/scripts/sync_entrypoints.py',
 '10_SYSTEM_CONFIG/scripts/delivery_automation.py',
 '10_SYSTEM_CONFIG/scripts/png_color.py',
 '10_SYSTEM_CONFIG/scripts/workflow_integrity.py',
 '10_SYSTEM_CONFIG/BEAUTIFICATION_POLICY.json',
 '10_SYSTEM_CONFIG/scripts/runtime_io.py',
 '10_SYSTEM_CONFIG/scripts/session_brief.py',
 '10_SYSTEM_CONFIG/style_config.json',
 '10_SYSTEM_CONFIG/reference_index.json',
 '05_STYLE_DNA/style_dna.json',
 '10_SYSTEM_CONFIG/runtime_policy.json',
 '10_SYSTEM_CONFIG/composition_policy.json',
 '10_SYSTEM_CONFIG/COMPOSITION_POLICY.md',
 '10_SYSTEM_CONFIG/CREATIVE_DIRECTION_POLICY.md',
 '10_SYSTEM_CONFIG/SESSION_BRIEF.json',
 '10_SYSTEM_CONFIG/FAST_EDIT_WORKFLOW.md',
 '10_SYSTEM_CONFIG/NATIVE_ADJUSTMENT_ROUTE.md',
 '10_SYSTEM_CONFIG/AUTOMATIC_DELIVERY.md',
 '10_SYSTEM_CONFIG/DELIVERY_ADAPTER.md',
 '10_SYSTEM_CONFIG/PROFESSIONAL_WORKFLOW.md',
 '10_SYSTEM_CONFIG/FAST_EDIT_WORKFLOW.json',
 '10_SYSTEM_CONFIG/QUICK_START.md',
 '10_SYSTEM_CONFIG/NEW_PHOTO_WORKFLOW.md',
 '10_SYSTEM_CONFIG/DEVELOPMENT_WORKFLOW.md',
 '10_SYSTEM_CONFIG/DEVELOPMENT_WORKFLOW.json',
)
def export(root,destination):
 root=Path(root).resolve();destination=Path(destination).resolve()
 if destination.is_relative_to(root):raise ValueError('Runtime export destination must be outside project')
 context=bootstrap(root)
 manifest={'workflow_revision':context['workflow_revision'],'scope':'Master policy, controller and verified configuration; no reference photographs or rendering engine','requirements':{'workflow_session':'Bootstrap/timing/ledger: standard library; review/accept/download: existing Pillow','photo_workflow':'Pillow in the current runtime; never install implicitly'},'files':{r:hashlib.sha256((root/r).read_bytes()).hexdigest() for r in FILES}}
 destination.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED) as z:
  for r in FILES:z.write(root/r,'PERSONAL_COLOR_SYSTEM/'+r)
  z.writestr('PERSONAL_COLOR_SYSTEM/workflow_runtime_manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 with zipfile.ZipFile(destination) as z:
  if z.testzip() is not None:raise ValueError('Runtime archive CRC failure')
 return {'path':str(destination),'bytes':destination.stat().st_size,'files':len(FILES)+1,'revision':context['workflow_revision']}
