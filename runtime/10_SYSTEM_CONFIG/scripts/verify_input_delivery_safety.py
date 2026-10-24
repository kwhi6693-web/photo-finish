"""Synthetic regressions for non-destructive acquisition and bound edit references."""
from pathlib import Path
import hashlib,io,json,shutil,tempfile,time,unittest
from unittest.mock import patch
from PIL import Image
import photo_edit as e,workflow_session as w,delivery_automation as a,delivery_adapter as d
from export_workflow_runtime import FILES

ROOT=Path(__file__).resolve().parents[2]
def image_bytes(fmt='PNG',color=(40,70,110)):
    data=io.BytesIO();Image.new('RGB',(16,12),color).save(data,format=fmt);return data.getvalue()

class DownloadSafetyTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
    def test_existing_target_is_preserved_without_network(self):
        target=self.root/'existing.png';target.write_bytes(b'existing')
        with patch.object(w,'urlopen',return_value=io.BytesIO(image_bytes())) as network:
            with self.assertRaises(FileExistsError):w.download_image('https://example.com/image',target)
        self.assertEqual(target.read_bytes(),b'existing');network.assert_not_called()
    def test_racing_target_is_not_overwritten(self):
        target=self.root/'race.png'
        class Response(io.BytesIO):
            def __exit__(self,*args):target.write_bytes(b'other writer');return super().__exit__(*args)
        with patch.object(w,'urlopen',return_value=Response(image_bytes())):
            with self.assertRaises(FileExistsError):w.download_image('https://example.com/image',target)
        self.assertEqual(target.read_bytes(),b'other writer');self.assertEqual(list(self.root.iterdir()),[target])
    def test_suffix_mismatch_is_rejected_without_reencoding_or_partial_file(self):
        target=self.root/'wrong.jpg'
        with patch.object(w,'urlopen',return_value=io.BytesIO(image_bytes())):
            with self.assertRaisesRegex(ValueError,'extension'):w.download_image('https://example.com/image',target)
        self.assertEqual(list(self.root.iterdir()),[])
    def test_valid_formats_preserve_exact_provider_bytes(self):
        for fmt,suffix in [('PNG','.PNG'),('JPEG','.jpeg')]:
            body=image_bytes(fmt);target=self.root/('valid'+suffix)
            with patch.object(w,'urlopen',return_value=io.BytesIO(body)):
                receipt=w.download_image('https://example.com/image',target)
            self.assertEqual(target.read_bytes(),body);self.assertEqual(receipt['sha256'],hashlib.sha256(body).hexdigest())
    def test_dangling_symlink_is_an_existing_target(self):
        target=self.root/'link.png'
        try:target.symlink_to(self.root/'missing.png')
        except OSError:self.skipTest('Symlink creation unavailable')
        with patch.object(w,'urlopen') as network:
            with self.assertRaises(FileExistsError):w.download_image('https://example.com/image',target)
        self.assertTrue(target.is_symlink());network.assert_not_called()

class InputBindingTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name);self.root=self.base/'project'
        for rel in FILES:
            target=self.root/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/rel,target)
        self.source=self.base/'source.png';self.ref=self.base/'style.png';self.job=self.base/'job.json'
        self.source.write_bytes(image_bytes());self.ref.write_bytes(image_bytes(color=(110,70,40)))
        e.prepare(self.root,self.source,self.job,{'intent':'Synthetic safety fixture','hierarchy':'flat','light_material':'synthetic RGB','output_use':'screen','route':'creative','qa_focus':['fixture']},[],evaluation_kind='synthetic')
    def submit(self,roles=None):
        return e.submit(self.job,{'requirements':[],'reason':'Synthetic fixture'},
            {'branch':'PROFESSIONAL_FALLBACK','decisions':[],'reason':'Synthetic fixture'},
            'SYNTHETIC_TOOL',{'prompt':'Synthetic edit','referenced_image_paths':[str(self.source),str(self.ref)]},{},input_references=roles)
    def test_each_local_reference_has_actual_identity_and_explicit_role(self):
        self.submit([{'path':str(self.ref),'role':'style_reference'}])
        entries=w._load(self.job)['render_result']['recipe']['input_references']['files']
        item=next(x for x in entries if x['path']==str(self.ref.resolve()))
        self.assertEqual(item['sha256'],w._file(self.ref)['sha256']);self.assertEqual(item['role'],'style_reference')
        self.assertEqual(next(x for x in entries if x['path']==str(self.source.resolve()))['role'],'edit_target')
    def test_reference_change_is_detected_without_another_submission(self):
        self.submit();self.ref.write_bytes(image_bytes(color=(5,10,20)))
        with self.assertRaisesRegex(ValueError,'reference'):a._fresh(self.job)
        self.assertEqual(len(w._load(self.job).get('external_call_receipts',[])),0)
    def test_final_acceptance_rechecks_reference_bytes(self):
        output=self.base/'output.png';output.write_bytes(image_bytes(color=(70,100,130)))
        ticket=self.submit();now=time.time_ns()
        e.returned(self.job,ticket['submission_id'],'ready',now,now+10,output_path=output,presented=True)
        w.add_review(self.job,output,w._file(self.source)['sha256'],True,False,'Synthetic protocol judgment only',
            color_scope='screen_srgb_assumed',color_assumption_reason='Synthetic untagged RGB fixture')
        self.ref.write_bytes(image_bytes(color=(5,10,20)))
        with self.assertRaisesRegex(ValueError,'reference'):w.accept_job(self.job,output)
    def test_missing_reference_fails_atomically_before_tool_submission(self):
        self.ref.unlink();before=self.job.read_bytes()
        with self.assertRaises(OSError):self.submit()
        self.assertEqual(self.job.read_bytes(),before);self.assertIsNone(w._load(self.job).get('render_result'))
    def test_fabricated_reference_role_path_is_rejected(self):
        extra=self.base/'unused.png';extra.write_bytes(image_bytes())
        before=self.job.read_bytes()
        with self.assertRaises(ValueError):self.submit([{'path':str(extra),'role':'style_reference'}])
        self.assertEqual(self.job.read_bytes(),before)
    def reviewed_first_step(self):
        output=self.base/'output.png';output.write_bytes(image_bytes(color=(70,100,130)))
        ticket=self.submit();now=time.time_ns()
        e.returned(self.job,ticket['submission_id'],'ready',now,now+10,output_path=output,presented=True)
        w.add_review(self.job,output,w._file(self.source)['sha256'],True,False,'Synthetic protocol review only',
            color_scope='screen_srgb_assumed',color_assumption_reason='Synthetic RGB fixture')
        return output,ticket
    def test_reference_symlink_retarget_is_detected(self):
        alias=self.base/'alias.png';other=self.base/'other.png';other.write_bytes(image_bytes(color=(1,2,3)))
        try:alias.symlink_to(self.ref)
        except OSError:self.skipTest('Symlink creation unavailable')
        original=self.ref;self.ref=alias;self.submit();alias.unlink();alias.symlink_to(other)
        with self.assertRaisesRegex(ValueError,'reference'):a._fresh(self.job)
        self.assertTrue(original.exists())
    def test_next_step_local_inputs_must_include_reviewed_output(self):
        self.reviewed_first_step();before=self.job.read_bytes()
        with self.assertRaisesRegex(ValueError,'latest reviewed'):
            d.next_step(self.job,'SYNTHETIC_TOOL',{'referenced_image_paths':[str(self.source)]})
        self.assertEqual(before,self.job.read_bytes())
    def test_compatibility_result_cannot_erase_or_replace_bound_recipe(self):
        ticket=self.submit();state=w._load(self.job);recipe=state['render_result']['recipe']
        a.render_result(self.job,'SYNTHETIC_TOOL',state['source']['sha256'],'unknown',submission_id=ticket['submission_id'])
        self.assertEqual(w._load(self.job)['render_result']['recipe'],recipe)
        with self.assertRaisesRegex(ValueError,'cannot be replaced'):
            a.render_result(self.job,'SYNTHETIC_TOOL',state['source']['sha256'],'unknown',recipe={},submission_id=ticket['submission_id'])
    def test_prior_step_call_receipt_cannot_accept_next_step(self):
        first,_=self.reviewed_first_step();second=self.base/'second.png';second.write_bytes(image_bytes(color=(120,130,140)))
        ticket=d.next_step(self.job,'SYNTHETIC_TOOL',{'referenced_image_paths':[str(first)]})
        a.render_result(self.job,'SYNTHETIC_TOOL',w._file(first)['sha256'],'ready',submission_id=ticket['submission_id'],output_path=second)
        w.add_review(self.job,second,w._file(first)['sha256'],True,False,'Synthetic review only',
            color_scope='screen_srgb_assumed',color_assumption_reason='Synthetic fixture')
        with self.assertRaisesRegex(ValueError,'call receipt'):w.accept_job(self.job,second)
    def test_fetch_rejects_dangling_alias_before_network(self):
        ticket=self.submit();state=w._load(self.job)
        a.render_result(self.job,'SYNTHETIC_TOOL',state['source']['sha256'],'ready','https://example.com/image',submission_id=ticket['submission_id'])
        alias=self.base/'alias-output.png'
        try:alias.symlink_to(self.base/'missing-output.png')
        except OSError:self.skipTest('Symlink creation unavailable')
        with patch.object(w,'download_image') as network:
            with self.assertRaises(ValueError):a.fetch(self.job,alias)
        network.assert_not_called();self.assertFalse((self.base/'missing-output.png').exists())

if __name__=='__main__':unittest.main()
