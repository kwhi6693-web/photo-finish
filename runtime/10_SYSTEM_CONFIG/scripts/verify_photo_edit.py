"""Fused execution and hash-bound reuse tests, using synthetic images/judgments only."""
from pathlib import Path
import json,shutil,tempfile,time,unittest
from unittest.mock import patch
from PIL import Image,PngImagePlugin
import photo_edit as e,photo_workflow as p,workflow_session as w,delivery_adapter as d
from export_workflow_runtime import FILES
from session_brief import SOURCES

ROOT=Path(__file__).resolve().parents[2]

class LeanEditTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name);self.root=self.base/'project'
        for rel in FILES:
            dest=self.root/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/rel,dest)
        self.source=self.base/'source.png';self.output=self.base/'output.png';self.job=self.base/'job.json'
        Image.new('RGB',(32,48),(70,90,100)).save(self.source);Image.new('RGB',(32,48),(80,100,110)).save(self.output)
        self.direction={'intent':'Synthetic fixture','hierarchy':'flat shape','light_material':'synthetic color',
          'output_use':'screen','route':'creative','qa_focus':['fixture']}
        self.prepared=e.prepare(self.root,self.source,self.job,self.direction,[])
    def submit(self,issues=None,arguments=None):
        return e.submit(self.job,{'requirements':[],'reason':'Synthetic blank image'},
          {'branch':'PROFESSIONAL_FALLBACK','decisions':[],'reason':'Synthetic fixture'},
          'SYNTHETIC_TOOL',arguments if arguments is not None else {'prompt':'Synthetic exact prompt'}, {},issues=issues)
    def returned(self,ticket,presented=True):
        now=time.time_ns();return e.returned(self.job,ticket['submission_id'],'ready',now,now+10,output_path=self.output,presented=presented)
    def events(self):
        return [{'action':'review','arguments':{'output_path':str(self.output),'input_sha256':w._file(self.source)['sha256'],
          'visual_passed':True,'profile_passed':False,'color_scope':'screen_srgb_assumed',
          'color_assumption_reason':'Synthetic ordinary screen fixture, not source color certification','note':'Synthetic visual judgment for protocol testing only'}}]
    def test_compact_preparation_does_not_emit_full_policy_or_histograms(self):
        self.assertIn('master_sha256',self.prepared);self.assertIn('candidates',self.prepared)
        raw=json.dumps(self.prepared);self.assertNotIn('luma_histogram32',raw);self.assertNotIn('runtime_policy',raw)
        self.assertEqual(w._load(self.job)['professional_direction']['intent'],'Synthetic fixture')
    def test_submit_failure_rolls_back_locked_decisions(self):
        before=self.job.read_bytes()
        with self.assertRaises(ValueError):self.submit(arguments=['not an argument object'])
        self.assertEqual(before,self.job.read_bytes());self.assertIsNone(w._load(self.job)['protection_plan'])
    def test_same_formal_bytes_are_decoded_once_across_return_check_review(self):
        ticket=self.submit()
        with patch.object(p,'inspect_image',wraps=p.inspect_image) as decode:
            self.returned(ticket);result=e.review(self.job,self.events(),self.output,self.base/'pending.json')
            self.assertEqual(decode.call_count,1)
        self.assertEqual(result['record']['record_status'],'pending_platform_confirmation')
        self.assertEqual(result['next']['action'],'AWAIT_PLATFORM_SAVE_CONFIRMATION')
        state=w._load(self.job);self.assertFalse(state['reviews'][-1]['profile_passed']);self.assertNotIn('save_completed',state['milestones'])
    def test_changed_bytes_invalidate_inspection_and_cannot_reuse_acceptance(self):
        self.returned(self.submit());Image.new('RGB',(32,48),(200,50,20)).save(self.output)
        before=self.job.read_bytes()
        with patch.object(p,'inspect_image',wraps=p.inspect_image) as decode:
            with self.assertRaises(ValueError):e.review(self.job,self.events(),self.output)
            self.assertEqual(decode.call_count,1)
        self.assertEqual(before,self.job.read_bytes())
    def test_metadata_only_change_invalidates_color_proof(self):
        self.returned(self.submit());meta=PngImagePlugin.PngInfo();meta.add(b'cICP',bytes((12,13,0,1)))
        with Image.open(self.output) as image:image.save(self.base/'changed.png',pnginfo=meta)
        (self.base/'changed.png').replace(self.output)
        with self.assertRaises(ValueError):e.review(self.job,self.events(),self.output)
    def test_inspector_version_change_forces_fresh_decode(self):
        self.returned(self.submit());state=w._load(self.job);state['render_result']['inspection']['inspection_version']=1;w._save(self.job,state)
        with patch.object(p,'inspect_image',wraps=p.inspect_image) as decode:p.check(self.job,self.output);self.assertEqual(decode.call_count,1)
    def test_open_issue_still_blocks_fused_review(self):
        self.returned(self.submit(issues=[{'issue_id':'quality','targets':['texture'],'observation':'Synthetic unresolved target'}]))
        with self.assertRaises(ValueError):e.review(self.job,self.events(),self.output)
        self.assertEqual(w._load(self.job)['status'],'in_progress')
    def test_missing_actual_review_is_not_invented(self):
        self.returned(self.submit())
        with self.assertRaises(ValueError):e.review(self.job,[],self.output)
        self.assertEqual(w._load(self.job)['reviews'],[])
    def test_unobserved_platform_display_is_not_claimed_observed_or_redisplayed(self):
        self.returned(self.submit(),presented=False);result=e.review(self.job,self.events(),self.output)
        self.assertIn('presentation is unobserved',result['next']['reason'])
        self.assertFalse(result['next']['display_needed'])
        self.assertEqual(d.status(self.job)['display'],'unobserved')
    def test_bootstrap_reads_each_canonical_source_once(self):
        counts={};original=Path.read_bytes
        def read(path):
            key=str(path.resolve());counts[key]=counts.get(key,0)+1;return original(path)
        with patch.object(Path,'read_bytes',read):w.bootstrap(self.root)
        for rel in SOURCES:self.assertEqual(counts.get(str((self.root/rel).resolve())),1,rel)

if __name__ == '__main__':
    import sys
    for _photo_finish_stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(_photo_finish_stream, 'reconfigure'):
            _photo_finish_stream.reconfigure(encoding='utf-8')
    unittest.main()
