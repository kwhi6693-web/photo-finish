import unittest,tempfile,zipfile,json,subprocess,sys
from pathlib import Path
from PIL import Image
from export_workflow_runtime import export,FILES
from workflow_session import bootstrap
ROOT=Path(__file__).resolve().parents[2]
class WorkflowRuntimeExportTests(unittest.TestCase):
 def test_extracted_bundle_bootstraps_without_full_project_or_media(self):
  with tempfile.TemporaryDirectory() as t:
   t=Path(t);out=t/'runtime.zip';export(ROOT,out)
   with zipfile.ZipFile(out) as z:
    self.assertEqual(len(z.namelist()),len(FILES)+1)
    self.assertFalse(any(n.lower().endswith(('.jpg','.jpeg','.png','.psd')) for n in z.namelist()))
    z.extractall(t/'extract')
   root=t/'extract/PERSONAL_COLOR_SYSTEM'
   self.assertEqual(bootstrap(root)['workflow_revision'],bootstrap(ROOT)['workflow_revision'])
   self.assertTrue((root/'10_SYSTEM_CONFIG/QUICK_START.md').is_file())
   integrity=subprocess.run([sys.executable,'-c',
       'import sys;sys.path.insert(0,sys.argv[1]);from workflow_integrity import validate;print(validate(sys.argv[2]))',
       str(root/'10_SYSTEM_CONFIG/scripts'),str(root)],capture_output=True,text=True,check=True, encoding='utf-8')
   self.assertIn('passed',integrity.stdout)
   source=t/'source.png';Image.new('RGB',(12,16),(80,90,100)).save(source)
   job=t/'job.json'
   command=[sys.executable,str(root/'10_SYSTEM_CONFIG/scripts/photo_workflow.py')]
   created=subprocess.run(command+['prepare'],input=json.dumps({'project_root':str(root),'source_path':str(source),'path':str(job)}),capture_output=True,text=True,check=True, encoding='utf-8')
   self.assertEqual(json.loads(created.stdout)['source']['dimensions'],[12,16])
   checked=subprocess.run(command+['check'],input=json.dumps({'path':str(job),'output_path':str(source)}),capture_output=True,text=True,check=True, encoding='utf-8')
   self.assertFalse(json.loads(checked.stdout)['accepted'])
   daily=subprocess.run([sys.executable,str(root/'10_SYSTEM_CONFIG/scripts/photo_edit.py'),'prepare'],
       input=json.dumps({'project_root':str(root),'source_path':str(source),'path':str(t/'daily.json'),'tags':[],
         'direction':{'intent':'Synthetic restore fixture','hierarchy':'flat field','light_material':'synthetic RGB',
           'output_use':'screen','route':'creative','qa_focus':['fixture']}}),capture_output=True,text=True,check=True, encoding='utf-8')
   self.assertEqual(json.loads(daily.stdout)['workflow_revision'],bootstrap(ROOT)['workflow_revision'])
   self.assertIn('master_sha256',json.loads(daily.stdout))
   with (root/'10_SYSTEM_CONFIG/runtime_policy.json').open('a', encoding='utf-8', newline='\n') as f:f.write(' ')
   with self.assertRaises(ValueError):bootstrap(root)
 def test_export_cannot_write_inside_canonical_project(self):
  with self.assertRaises(ValueError):export(ROOT,ROOT/'bad-runtime.zip')
