"""Optional exact execution images. No inferred or replayed intermediate states."""
from pathlib import Path
import os,shutil,tempfile,time
from editorial_pipeline import hash_file


class ExecutionArtifacts:
    def __init__(self,directory):
        self.target=None;self.staging=None;self.zones=[];self.committed=False;self.published=False
        if directory is not None:
            raw=Path(directory).absolute()
            if any(p.is_symlink() for p in (raw,*raw.parents)) or os.path.lexists(raw):
                raise FileExistsError('execution artifact directory exists or traverses a symlink')
            parent=raw.parent.resolve(strict=True)
            self.target=parent/raw.name
            self.staging=Path(tempfile.mkdtemp(prefix='.native-artifacts-',dir=parent))

    def __enter__(self):return self

    def capture(self,name,alpha,output):
        if self.staging is None:return
        start=time.perf_counter();index=len(self.zones)+1
        files={}
        for kind,image in (('alpha',alpha),('output',output)):
            file=self.staging/f'zone_{index}_{kind}.png'
            kwargs={'icc_profile':image.info['icc_profile']} if kind=='output' else {}
            image.save(file,format='PNG',**kwargs)
            files[kind]={'file':file.name,'sha256':hash_file(file),'bytes':file.stat().st_size}
        self.zones.append({'name':name,'order':index,**files,'write_seconds':time.perf_counter()-start})

    def publish(self):
        if self.target is None:return {'status':'NOT_REQUESTED','render_calls':1,'zones':[]}
        if os.path.lexists(self.target):raise FileExistsError('artifact target appeared during rendering')
        os.rename(self.staging,self.target);self.published=True
        return {'status':'EXACT_EXECUTION_IMAGES','directory':str(self.target),
                'render_calls':1,'diagnostic_rerenders':0,'zones':self.zones}

    def commit(self):self.committed=True

    def __exit__(self,*error):
        if not self.committed:
            if self.staging is not None:shutil.rmtree(self.staging,ignore_errors=True)
            if self.published:shutil.rmtree(self.target,ignore_errors=True)
