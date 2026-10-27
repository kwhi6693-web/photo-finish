"""Keyword discovery/cache tests using explicit anonymous collection consent."""
from pathlib import Path
import sys,tempfile,unittest
from unittest.mock import patch
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'runtime/10_SYSTEM_CONFIG/scripts'))
import style_library as s

class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name)
        self.root=self.base/'private';self.photo=self.base/'photo.png';Image.new('RGB',(20,20),(80,90,100)).save(self.photo)
        self.item=s.add(self.photo,'宁静旅行',consent=True,labels=['柔光','低对比'],library_root=self.root)

    def test_natural_phrase_expands_known_synonyms_but_keeps_unknown_constraints(self):
        result=s.list_references(self.root,query='找那种安静、柔和、适合旅行的参考')
        self.assertEqual(result['total'],1)
        self.assertEqual(result['search_method'],'expanded_keywords')
        self.assertEqual(s.list_references(self.root,query='安静 火星风暴')['total'],0)

    def test_only_affected_metadata_cache_entry_is_rebuilt(self):
        s._decoded.cache_clear();s.records(self.root);first=s._decoded.cache_info()
        s.records(self.root);second=s._decoded.cache_info();self.assertGreater(second.hits,first.hits)
        s.update(self.item['reference_id'],title='更新的参考',consent=True,library_root=self.root)
        self.assertEqual(s.list_references(self.root,query='更新')['total'],1)
        self.assertEqual(s.list_references(self.root,query='宁静')['total'],0)
        s.remove(self.item['reference_id'],self.root)
        self.assertEqual(s.list_references(self.root)['total'],0)

    def test_usage_is_idempotent_and_recent_frequent_are_metadata_only(self):
        rid=self.item['reference_id']
        s.record_use(self.root,rid,'synthetic-job-1',100)
        s.record_use(self.root,rid,'synthetic-job-1',100)
        s.record_use(self.root,rid,'synthetic-job-2',200)
        with patch.object(Image,'open',side_effect=AssertionError('metadata query decoded photo')):
            result=s.list_references(self.root,sort='frequent')
            self.assertEqual(result['references'][0]['use_count'],2)
            self.assertEqual(s.list_references(self.root,sort='recent')['references'][0]['last_used_unix_ns'],200)
        s.remove(rid,self.root)
        self.assertEqual(s.list_references(self.root,sort='recent')['total'],0)

    def test_unrequested_photo_does_not_create_collection(self):
        other=self.base/'not-created'
        with self.assertRaises(ValueError):s.add(self.photo,'No consent',library_root=other)
        self.assertFalse(other.exists())
