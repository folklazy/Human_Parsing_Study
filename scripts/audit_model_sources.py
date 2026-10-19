"""Pinned source and bounded metadata checks. Never downloads model weights."""
from pathlib import Path
from datetime import datetime,timezone
from hashlib import sha256
import json
import re
import urllib.request
import urllib.error


def inspect_url(url,head=False):
    started=datetime.now(timezone.utc).isoformat()
    try:
        request=urllib.request.Request(url,method='HEAD' if head else 'GET',headers={'User-Agent':'MHPv2-stage0-source-audit'})
        with urllib.request.urlopen(request,timeout=20) as response:
            headers=dict(response.headers);kind=headers.get('Content-Type','')
            text=b''
            if not head:
                if not any(value in kind for value in ['text','json','html']): raise RuntimeError('Refusing binary download in source audit')
                text=response.read(2*1024*1024+1)
                if len(text)>2*1024*1024: raise RuntimeError('Source metadata exceeds bound')
            return {'requested_url':url,'final_url':response.geturl(),'http_status':response.status,'headers':headers,
                    'retrieved_utc':started,'body_sha256':sha256(text).hexdigest() if text else None,
                    'body_text':text.decode('utf-8',errors='replace') if text else None,
                    'checkpoint_downloaded':False}
    except Exception as exc:
        return {'requested_url':url,'retrieved_utc':started,'error':f'{type(exc).__name__}: {exc}','checkpoint_downloaded':False}


def main():
    study=Path(__file__).resolve().parents[1];workspace=study.parent
    run_id=json.loads((study/'provenance/STAGE0_ACTIVE_RUN.json').read_text())['run_id'];run=study/'provenance/RUN_MANIFESTS'/run_id
    third=workspace/'third_party/human_parsing'
    evidence={}
    for model,directory in [('M2FP','M2FP'),('CPI-Parser','CPI-Parser'),('SCHP','SCHP')]:
        readme=(third/directory/'README.md').read_text()
        if model=='M2FP': urls=re.findall(r'https://drive.google.com/drive/folders/[^)\s]+',readme)[-1:]
        elif model=='CPI-Parser':
            section=readme.split('### MHP')[-1].split('## Evaluation')[0]
            urls=re.findall(r'https://drive.google.com/[^)\s]+',section)
        else: urls=re.findall(r'https://drive.google.com/file/d/[^)\s]+',readme)[:1]
        evidence[model]=[inspect_url(url) for url in urls]
        print(f'[SOURCE] {model}: {len(urls)} official checkpoint metadata links inspected',flush=True)
    releases=json.loads((run/'D2FP_RELEASES.json').read_text())
    evidence['D2FP']=[{**inspect_url(asset['browser_download_url'],head=True),'release_asset':asset['name'],
                       'release_asset_bytes':asset['size'],'checkpoint_kind':'Full parser release; not backbone R-103.pkl'}
                      for release in releases for asset in release['assets']]
    hf=json.loads((run/'FASHN_HF.json').read_text());revision=hf['sha'];hfroot=f'https://huggingface.co/fashn-ai/fashn-human-parser/resolve/{revision}'
    evidence['FASHN']=[inspect_url(hfroot+'/config.json'),inspect_url(hfroot+'/preprocessor_config.json'),inspect_url(hfroot+'/README.md'),
                       inspect_url(hfroot+'/model.safetensors',head=True)]
    for name in ['QANet','CDGNet','RP-R-CNN']:
        meta=json.loads((run/(name+'_METADATA.json')).read_text());evidence[name]={'source_metadata':meta,
                    'checkpoint_links_status':'OFFICIAL_README_LINKS_PRESENT_NOT_DOWNLOADED' if meta['checkpoint_links'] else 'NO_LINK_IN_INSPECTED_README',
                    'smoke_tested':False,'optional_environment_not_installed':True}
    path=study/'provenance/MODEL_SOURCE_AUDIT.json';assert not path.exists();path.write_text(json.dumps(evidence,indent=2)+'\n')
    print('[SOURCE] audit evidence saved; no weights downloaded',flush=True)


if __name__=='__main__':main()
