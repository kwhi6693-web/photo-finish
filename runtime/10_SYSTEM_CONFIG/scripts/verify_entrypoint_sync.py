"""Maintenance mirror generation and restored adapter availability."""
from pathlib import Path
import json,re,shutil,tempfile,unittest
from PIL import Image
import photo_workflow
from export_workflow_runtime import FILES
from sync_entrypoints import synchronize
from workflow_integrity import validate

ROOT=Path(__file__).resolve().parents[2]

class EntrypointTests(unittest.TestCase):
    def test_documented_compatibility_prepare_binds_current_revision(self):
        guide=(ROOT/'10_SYSTEM_CONFIG/FAST_EDIT_WORKFLOW.md').read_text(encoding='utf-8')
        example=json.loads(re.search(r'```json\n([^`]+)```',guide).group(1))
        with tempfile.TemporaryDirectory() as t:
            source=Path(t)/'source.png';Image.new('RGB',(16,16),(128,128,128)).save(source)
            example.update(project_root=str(ROOT),source_path=str(source),path=str(Path(t)/'job.json'))
            result=photo_workflow.prepare(**example)
            policy=json.loads((ROOT/'10_SYSTEM_CONFIG/runtime_policy.json').read_text(encoding='utf-8'))
            self.assertEqual(result['context']['workflow_revision'],policy['fast_edit_workflow']['revision'])
    def test_generated_entrypoints_and_mirrors_are_idempotent_and_drift_checked(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)/'project'
            for name in FILES:
                p=root/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,p)
            synchronize(root);tracked=[root/'10_SYSTEM_CONFIG'/name for name in ('runtime_policy.json','BEAUTIFICATION_POLICY.json','SESSION_BRIEF.json','QUICK_START.md','NEW_PHOTO_WORKFLOW.md')]
            before={str(p):p.read_bytes() for p in tracked};synchronize(root)
            self.assertEqual(before,{str(p):p.read_bytes() for p in tracked});self.assertEqual(validate(root)['status'],'passed')
            policy=root/'10_SYSTEM_CONFIG/runtime_policy.json';data=json.loads(policy.read_text(encoding='utf-8'));data['beautification_defaults']['execution_adapter_policy']['revision']='drift';policy.write_text(json.dumps(data), encoding='utf-8', newline='\n')
            with self.assertRaises(ValueError):validate(root)
    def test_runtime_bundle_contains_current_adapter_and_semantic_methods(self):
        for name in ('delivery_adapter.py','reference_semantics.py','sync_entrypoints.py'):
            self.assertIn('10_SYSTEM_CONFIG/scripts/'+name,FILES)
        self.assertIn('10_SYSTEM_CONFIG/DELIVERY_ADAPTER.md',FILES)

if __name__=='__main__':unittest.main()
