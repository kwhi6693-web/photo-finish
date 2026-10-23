"""Read-only local capability and policy checks; never install dependencies."""
from pathlib import Path
import argparse,io,json,re,sys,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
def check(root=ROOT):
    root=Path(root);runtime=root/'runtime';scripts=runtime/'10_SYSTEM_CONFIG/scripts';sys.path.insert(0,str(scripts))
    from PIL import Image,ImageCms
    from workflow_integrity import validate
    if sys.version_info<(3,10):raise ValueError('Python 3.10+ required')
    data=io.BytesIO();Image.new('RGB',(8,6),(70,90,110)).save(data,format='PNG');data.seek(0)
    with Image.open(data) as image:image.load();assert image.size==(8,6)
    assert (root/'LICENSE').read_text().startswith('MIT License')
    assert re.search(r'^name: photo-finish$',(root/'SKILL.md').read_text(),re.M)
    index=json.loads((runtime/'10_SYSTEM_CONFIG/reference_index.json').read_text())
    if index:raise ValueError('Public distribution must not ship private reference records')
    links=0
    for doc in list(root.glob('*.md'))+list((root/'docs').glob('*.md')):
        for link in re.findall(r'\]\(([^)]+)\)',doc.read_text()):
            if '://' in link or link.startswith(('#','mailto:')):continue
            target=doc.parent/link.split('#')[0]
            if not target.exists():raise ValueError('Missing local documentation link: '+doc.name)
            links+=1
    for preset in (runtime/'06_SCENE_PRESETS/xmp').glob('*.xmp'):ET.parse(preset)
    return {'status':'passed','python':sys.version.split()[0],'integrity':validate(runtime,root),'public_reference_count':len(index),'documentation_links':links,'host_image_editor':'must be supplied by the agent; not tested by this command'}
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,default=ROOT);args=parser.parse_args()
    try:print(json.dumps(check(args.root),ensure_ascii=False,indent=2))
    except Exception as error:print(json.dumps({'status':'failed','error':str(error)},ensure_ascii=False));sys.exit(1)
