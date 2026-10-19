"""Count-derived operational figure, never a semantic-quality or resource ranking."""
from pathlib import Path
import hashlib
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
R=ROOT/'provenance/RUN_MANIFESTS/first-cohort-benchmark-20261016T094257313856Z'
source=R/'FINAL_BENCHMARK_VALIDATION.json'
if (ROOT/'plots/first_cohort_completion.png').exists():
    raise SystemExit('Existing derived figure is preserved; archive and approve an explicit regeneration first.')
rows=json.loads(source.read_text())['components']
fig,ax=plt.subplots(figsize=(10,4.4),layout='constrained')
left=[0]*len(rows)
for key,color,label in [('complete','#167d8d','Complete'),('failed','#cc4c3e','Failed (CUDA OOM)'),('invalid','#b8860b','Invalid (interruption)')]:
    values=[x[key] for x in rows]
    ax.barh(range(len(rows)),values,left=left,color=color,label=label)
    left=[a+b for a,b in zip(left,values)]
for i,row in enumerate(rows):
    ax.text(5050,i,f"{row['complete']:,} complete / {row['failed']} failed / {row['invalid']} invalid",va='center',fontsize=8)
ax.set_yticks(range(len(rows)),['YOLO26x frozen','CPI R50 CIHP','CPI ConvNeXt-B CIHP'])
ax.invert_yaxis();ax.set_xlim(0,7300);ax.set_xticks([0,1000,2000,3000,4000,5000])
ax.set_xlabel('Reference image jobs (fixed denominator 5,000 per component)')
ax.set_title('Observed execution completeness — not an accuracy ranking')
ax.legend(loc='lower right',fontsize=8)
ax.spines[['top','right']].set_visible(False)
out=ROOT/'plots/first_cohort_completion.png';out.parent.mkdir(exist_ok=True)
fig.savefig(out,dpi=150);plt.close(fig)
record=dict(derivation='Existing canonical component counts only; no model inference',matplotlib=matplotlib.__version__,
    input=str(source.relative_to(ROOT)),input_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
    script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),plot=str(out.relative_to(ROOT)),
    plot_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),source_dataset_photos_used=False)
(ROOT/'publication/FIGURE_PROVENANCE.json').write_text(json.dumps(record,indent=2)+'\n')
