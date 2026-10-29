# Human Parsing Benchmark — current status

**CPI_CONVNEXT_CHUNKED_RUNNING** · 2026-10-29T23:08:11.945471+07:00 (Asia/Bangkok)

[Current attempt/report](reports/cpi-convnext-chunked-20261029T160327964412Z.md) / [segment plan](runs/convnext-20261029T160359716460Z/SEGMENT_PLAN.json) / [first packet proof](runs/cpi-convnext-chunked-20261029T160327964412Z/FIRST_PACKET_CHECK.json). Segment `convnext-20261029T160359716460Z`. Controller640227, worker640842, detachedSID640227/PPID1 verified.

Reconciled337 old canonical IDs; pending4663 atlaunch; diagnosticpackets excluded. Snapshot new204/total541/5000, failed0; use viewer for live counts. TRAINwarmup passed. Firstcanonicalpatched0003218 passed originalgeometry/native20/NPZ/hash/GT/scores0.50/0.75/effectiveimplementationbinding; NPZ byteidenticaltoseparatediagnostic but independently inferred forcanonical.

ImplementationCPI_PERSON_CHUNK_RESTORATION_1; allfrozenweights/FP32/resolution/TTA/thresholds/YOLO/ownership/GT/scorer retained. Additionaldiagnosticclockandretainedbytes included in unchanged24h/80GiB/free50GiB. STRICT_COMPLETE primarynulluntilall5000artifactsverified. NoautomaticOOM/modelretry/fallback/nextmodel.

```bash
.venvs/parser-legacy-cu113/bin/python Human_Parsing_Benchmark/scripts/run_cpi_chunked_continuation.py --model convnext --status --watch
```

ControllerwritesCOMPLETIONafterworkerexit/reconciliation. Detachedread-onlyobserver will report/publishterminalcanonicalresults andupdateSTATUS if itsguardstillmatches; itneverstarts/retriesinference. Ifinterrupted/missingCOMPLETION,reconciliationrequired. R50paused;Sapiens04/08 COMPLETE5000/native/commonresultsunchanged;no1B/training/color/CCTV.
