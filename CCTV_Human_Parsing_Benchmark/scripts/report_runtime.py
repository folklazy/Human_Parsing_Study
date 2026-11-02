"""Append historical timing diagnostics to the existing CCTV90 results report.

Read small logs/metadata only. Never load a model, image, mask or checkpoint.
Keep monotonic adapter timers separate from UTC event intervals.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from statistics import median

from report_target_confusion import P, W, SHORT, read, sha


def describe_seconds(values):
    values = sorted(values)
    if not values:
        return dict(n=0, mean_ms=None, median_ms=None, p95_ms=None, total_seconds=None)
    if any(not math.isfinite(v) or v < 0 for v in values):
        raise ValueError('Invalid duration')
    position = (len(values) - 1) * .95
    lo, hi = math.floor(position), math.ceil(position)
    p95 = values[lo] + (values[hi] - values[lo]) * (position - lo)
    return dict(n=len(values), mean_ms=sum(values)/len(values)*1000,
                median_ms=median(values)*1000, p95_ms=p95*1000,
                total_seconds=sum(values))


def time_accounting(row):
    """Add disjoint logged observations, keeping nested worker time separate.

    This is accounting over two different timing boundaries, not a homogeneous
    latency metric. Unmeasured ROI execution time is never imputed as zero.
    """
    groups = [row['monotonic_adapter'], row['UTC_event_interval']]
    measured = sum(group['n'] for group in groups)
    population = row['ROI_population']
    if population <= 0 or not 0 <= measured <= population:
        raise ValueError('Invalid timing coverage')
    terms = []
    for group in groups:
        if group['n']:
            value = group['total_seconds']
            if value is None or not math.isfinite(value) or value < 0:
                raise ValueError('Missing/invalid duration for observed calls')
            terms.append(value)
        elif group['total_seconds'] is not None:
            raise ValueError('Empty observation group must remain null')
    return dict(timed_ROIs=measured, untimed_ROIs=population-measured,
                timing_coverage=measured/population,
                logged_interval_sum_seconds=math.fsum(terms) if terms else None,
                worker_elapsed_sum_seconds=math.fsum(
                    segment['worker_elapsed_seconds'] for segment in row['segments']),
                homogeneous_latency_metric=False, end_to_end=False)


def forward_pairs(events):
    pending, complete = {}, {}
    for event in events:
        key = event.get('job_id')
        if event['event'] == 'FORWARD_START':
            if key in pending or key in complete:
                raise ValueError('Duplicate forward; do not choose a fastest attempt')
            pending[key] = event
        elif event['event'] == 'FORWARD_END':
            if key not in pending:
                raise ValueError('End without start')
            start = pending.pop(key)
            if start['purpose'] != event['purpose']:
                raise ValueError('Purpose mismatch')
            seconds = (datetime.fromisoformat(event['utc']) - datetime.fromisoformat(start['utc'])).total_seconds()
            if seconds < 0:
                raise ValueError('Negative UTC interval')
            complete[key] = dict(event, UTC_interval_seconds=seconds)
    return complete, pending


def collect():
    inputs = {}

    def load(path, lines=False):
        path = path if path.is_absolute() else W/path
        inputs[str(path.relative_to(W))] = sha(path)
        return [json.loads(line) for line in path.read_text().splitlines()] if lines else read(path)

    closure = load(P/'reports/CONTROLLED_ROI_COMPLETION.json')
    index = load(P/'reports/CONTROLLED_ROI_FOUR_TARGET_INDEX.json')
    parent = P/'outputs'/closure['parent_run']
    continuation = P/'outputs'/closure['continuation_run']
    config = load(parent/'CONFIG.json')
    cont_config = load(continuation/'CONFIG.json')
    assert sha(parent/'CONFIG.json') == cont_config['parent_config_sha256']
    manifest = load(W/config['manifest'])
    assert sha(W/config['manifest']) == config['manifest_sha256']
    expected = {j['job_id'] for j in manifest['jobs']}
    assert len(expected) == len(manifest['jobs']) == 130
    assert len(manifest['frames']) == 90 and list(index['models']) == list(SHORT)
    # Verify the bounded source references that define the historical timers.
    for path in ['CCTV_Human_Parsing_Benchmark/scripts/controlled_roi.py',
                 'CCTV_Human_Parsing_Benchmark/scripts/controlled_roi_models.py',
                 'Human_Parsing_Benchmark/src/cihp_benchmark/adapters.py',
                 'CCTV_Human_Parsing_Benchmark/scripts/controlled_roi_continuation.py']:
        digest = config['source_hashes'].get(path) or cont_config['source_hashes'][path]
        assert sha(W/path) == digest, 'Timing source drift'
        inputs[path] = digest
    by_model = {r['model_id']: r for r in closure['models']}
    result = []
    for mid in SHORT:
        accepted = by_model[mid]
        assert accepted['frames'] == 90 and accepted['ROIs'] == 130 and accepted['accepted_membership'] == 'EXACT'
        final_path = W/accepted['completion_reference']
        final = load(final_path)
        assert sha(final_path) == accepted['completion_sha256'] and final['strict_complete']
        mono, wall_events, committed, warmups, unfinished, segments = [], [], set(), 0, 0, []
        environment = None
        for root, clock in [(parent, 'MONOTONIC'), (continuation, 'UTC_EVENT')]:
            model_root = root/mid
            if not model_root.exists():
                continue
            events = load(model_root/'ATTEMPTS.jsonl', lines=True)
            observations = load(model_root/'RESOURCE_OBSERVATIONS.json')
            state = load(model_root/'STATE.json')
            env = load(model_root/'ENVIRONMENT.json')
            if environment is None:
                environment = {k: env.get(k) for k in ['GPU', 'torch', 'CUDA_runtime', 'FP32', 'AMP', 'TF32']}
                assert environment['GPU'] == 'Tesla T4'
            pairs, incomplete = forward_pairs(events)
            observed = {r['job_id']: r for r in observations}
            assert len(observed) == len(observations) and set(observed) == set(pairs)
            packet_ids = [r['job_id'] for r in events if r['event'] == 'ROI_COMMITTED']
            assert len(packet_ids) == len(set(packet_ids))
            if clock == 'MONOTONIC':
                new_ids = set(observed) - {'TRAIN0000930'}
                reused = set(config['reuse'][mid])
                assert new_ids | reused == set(packet_ids) and not new_ids & reused
            else:
                new_ids = set(observed) - {'TRAIN0000930'}
                assert new_ids == set(packet_ids)
            assert not committed & new_ids and new_ids <= expected
            committed |= new_ids
            for key, row in observed.items():
                assert row['purpose'] == pairs[key]['purpose']
                if row['purpose'] == 'TRAIN_WARMUP':
                    assert key == 'TRAIN0000930'
                    warmups += 1
                    continue
                assert row['purpose'] in ('ROI_READINESS', 'ROI_INFERENCE')
                if clock == 'MONOTONIC':
                    assert row['adapter_elapsed_seconds'] == pairs[key]['adapter_elapsed_seconds']
                    mono.append(row['adapter_elapsed_seconds'])
                else:
                    assert 'adapter_elapsed_seconds' not in row
                    wall_events.append(pairs[key]['UTC_interval_seconds'])
            assert all(r['purpose'] != 'TRAIN_WARMUP' for r in incomplete.values())
            unfinished += len(incomplete)
            elapsed = (datetime.fromisoformat(state['ended_utc']) - datetime.fromisoformat(state['started_utc'])).total_seconds()
            assert elapsed >= 0
            segments.append(dict(run_id=root.name, worker_elapsed_seconds=elapsed, status=state['status']))
        reused = set(config['reuse'][mid])
        assert not committed & reused and committed | reused == expected
        result.append(dict(model_id=mid, frames=90, ROI_population=130,
                           monotonic_adapter=describe_seconds(mono), UTC_event_interval=describe_seconds(wall_events),
                           prior_diagnostic_ROIs_without_current_timing=len(reused), warmup_calls_excluded=warmups,
                           unfinished_forward_starts=unfinished, segments=segments,
                           worker_elapsed_seconds=sum(s['worker_elapsed_seconds'] for s in segments),
                           parent_environment=environment))
    assert sum(r['monotonic_adapter']['n'] + r['UTC_event_interval']['n'] for r in result) == closure['successful_new_unique_ROI_observations']
    assert sum(r['warmup_calls_excluded'] for r in result) == closure['TRAIN_warmup_calls']
    assert sum(r['unfinished_forward_starts'] for r in result) == closure['retained_failed_RPR_learned_calls']
    for row in result:
        row['time_accounting'] = time_accounting(row)
    return result, inputs


def accounting_section(rows):
    lines = ['### D. ตารางสรุปรวม — บวกค่าที่มี log แล้ว', '',
        '**ไม่มีเวลารายคลาส:** หนึ่ง forward ทำนาย native classes ทั้งหมดร่วมกัน (CIHP 20 / Sapiens 29) แล้วใช้ Hair/Face/Upper/Lower จาก output นั้น การ map/ให้คะแนนสี่ targets เป็นงานภายหลัง ไม่ได้จับเวลาแยกรายคลาส จึงแบ่งเวลารวมออกเป็น 4 ค่าไม่ได้ ส่วน IoU/Recall/Precision/Dice รายคลาสยังอยู่ในตารางคุณภาพและ confusion matrix ข้างต้น', '',
        '| Model | ROI มีเวลา / 130 | A รวม s | B รวม s | A+B ช่วงเวลาที่มี log รวม s | C รวม worker s |',
        '|---|---:|---:|---:|---:|---:|']
    for row in rows:
        a, b = row['monotonic_adapter'], row['UTC_event_interval']
        b_display = f"{b['total_seconds']:.3f}" if b['n'] else '—'
        total = row['time_accounting']
        lines.append(f"| {SHORT[row['model_id']]} | {total['timed_ROIs']}/130 | {a['total_seconds']:.3f} | {b_display} | {total['logged_interval_sum_seconds']:.3f} | {total['worker_elapsed_sum_seconds']:.3f} |")
    sums = [math.fsum(row[key]['total_seconds'] or 0 for row in rows)
            for key in ['monotonic_adapter', 'UTC_event_interval']]
    measured = sum(row['time_accounting']['timed_ROIs'] for row in rows)
    population = sum(row['ROI_population'] for row in rows)
    combined = math.fsum(row['time_accounting']['logged_interval_sum_seconds'] for row in rows)
    workers = math.fsum(row['time_accounting']['worker_elapsed_sum_seconds'] for row in rows)
    lines += [f'| **รวมบัญชี 9 ระบบ** | **{measured}/{population}** | **{sums[0]:.3f}** | **{sums[1]:.3f}** | **{combined:.3f}** | **{workers:.3f}** |', '',
        '**A+B เป็นผลบวกเชิงบัญชีของคนละ ROI ที่สำเร็จและไม่ซ้ำกัน** แต่ clock/ขอบเขตต่างกันตาม A/B จึงไม่ใช่ latency มาตรฐานเดียวกัน และไม่ใช่เวลา parsing ทั้ง 130 ROI ของ Sapiens ที่มี timer เพียง 115 ROI เครื่องหมาย — หมายถึงไม่มี continuation intervals ให้รวม ไม่ใช่ทำนายโดยใช้เวลาเป็นศูนย์ ไม่ประมาณเวลาอีก 15 ROI ของแต่ละ Sapiens จากค่าเฉลี่ยหรือแทนด้วยศูนย์ ยอดรวมคำนวณจาก full precision ก่อนปัดเศษ จึงอาจต่างจากการบวกเลข 3 ตำแหน่งที่แสดงเล็กน้อย', '',
        '**ห้ามบวก A+B+C:** C ครอบช่วงทำงาน A/B อยู่แล้ว จึงจะนับเวลาซ้ำ หากถามเวลารวมของ worker ให้ใช้ C ที่บวก parent+continuation แล้วโดยตรง ส่วนผลรวม 9 ระบบคือบัญชีเวลาของงานทั้งเก้า ไม่ใช่ latency ของหนึ่งภาพ ไม่ใช่ elapsed ของ batch ตั้งแต่ต้นถึงจบรวมช่วงรอ และไม่ใช่เวลา YOLO→parsing→สี→ฐานข้อมูล', '',
        '### นิยาม metrics ของเวลาและจำนวนตัวอย่าง', '',
        '| Metric / ค่าที่แสดง | สูตรและหน่วย | บอกอะไร / ข้อจำกัด | ที่มา |',
        '|---|---|---|---|',
        '| A: Monotonic adapter duration | t_after_sync − t_before_infer; วินาทีต่อ ROI | preprocess/transfer/model/native decode ภายใน adapter ไม่ใช่ model forward ล้วน; ขอบเขตต่างรายโมเดล | [parent forward](../scripts/controlled_roi.py) → adapter_elapsed_seconds |',
        '| B: UTC event interval | FORWARD_END.utc − FORWARD_START.utc; วินาทีต่อ ROI | รวม synchronization และ log/resource-writing overhead เพิ่ม; เป็น system-clock interval | [continuation forward/events](../scripts/controlled_roi_continuation.py) |',
        '| Mean ms/ROI | 1,000 × Σt/n แยกใน A หรือ B | เวลาต่อ ROI โดยเฉลี่ยเฉพาะกลุ่มที่มี timer; แม้ถ่วง n ก็ยังไม่แก้ขอบเขต A/B ที่ต่างกัน จึงไม่รวมเป็น latency มาตรฐานเดียว | [describe_seconds](../scripts/report_runtime.py) จาก accepted observations |',
        '| Median ms/ROI | ค่ากลางของ sorted t × 1,000 | เวลาของ sample กลาง; ไวต่อค่าสุดขั้วน้อยกว่า mean | สถิติเชิงพรรณนาของแต่ละกลุ่ม log |',
        '| P95 ms/ROI | linear percentile ตำแหน่ง 0.95×(n−1) × 1,000 | ประมาณค่าช่วงช้าของ sample ที่วัด ไม่ใช่ confidence interval หรือรับประกัน 95% ของภาพใหม่ | [describe_seconds](../scripts/report_runtime.py); n=1 ให้ค่าเดียวกับ sample นั้น |',
        '| ผลรวม A+B | Σt_A + Σt_B; วินาที | รวมช่วงเวลาที่มี log ไม่ซ้ำ ROI; เป็น derived accounting ไม่ใช่ pure-parsing/end-to-end metric | [time_accounting](../scripts/report_runtime.py); ไม่แก้ clock ให้เป็นชนิดเดียวกัน |',
        '| C: รวม worker elapsed | Σ_segments(STATE.ended_utc − STATE.started_utc); วินาที | รวม loading/warmup/checks/export และ failed work ภายในแต่ละ attempt; ไม่รวม queue gap และงานนอก worker | STATE.json ของ parent/continuation; ตาราง C |',
        '| Timing coverage | (n_A+n_B)/130; ROI และ % | มี duration กี่ ROI ในประชากรที่มีผล; ไม่ใช่ prediction completeness, detection recall หรือความแม่นยำ | จับคู่ accepted ROI membership กับ log; Sapiens 115/130=88.462% แต่ predictions ครบ130 |', '',
        'สูตร Mean/Median/P95 เป็นสถิติเชิงพรรณนาของเวลาที่บันทึก ไม่ใช่ metric การแยกส่วนภาพ มาตรวัดคุณภาพ IoU/Recall/Precision/Dice มีสูตร ตัวหาร และแหล่งอ้างอิงแยกอยู่ในส่วน confusion matrix ไม่มีการสร้างคะแนนผสม quality×speed หรือเลือกผู้ชนะใหม่จากตารางเวลานี้', '']
    return lines


def section(rows):
    lines = ['<!-- RUNTIME_DIAGNOSTICS_START -->', '## ความเร็วและเวลาประมวลผลจาก log เดิม', '',
        '**เป็น historical shared-GPU adapter diagnostics บน Tesla T4 ที่บันทึกไว้ ไม่ใช่ clean parser-only หรือ end-to-end speed benchmark** ไม่มีการรันโมเดลใหม่เพื่อเพิ่มตารางนี้ หน่วยหลักเป็นหนึ่ง shared person ROI ไม่ใช่หนึ่งภาพ; 90 ภาพมี 130 YOLO opportunities และ 8 ภาพไม่มี detection แต่ละ call คืนทุก native class ร่วมกัน จึงไม่มีเวลาราย Hair/Face/Upper/Lower แยกต่างหาก', '',
        '### A. เวลา adapter จาก monotonic timer — parent segment', '',
        '| Model | ROI ที่มี timer / 130 | Mean ms/ROI | Median ms/ROI | P95 ms/ROI | ผลรวมเวลาที่จับ s |',
        '|---|---:|---:|---:|---:|---:|']
    for row in rows:
        s = row['monotonic_adapter']
        lines.append(f"| {SHORT[row['model_id']]} | {s['n']}/130 | {s['mean_ms']:.3f} | {s['median_ms']:.3f} | {s['p95_ms']:.3f} | {s['total_seconds']:.3f} |")
    lines += ['', 'นับ ROI_READINESS ที่เป็นสมาชิกจริงด้วย ไม่มี inference ซ้ำเฉพาะ timing และไม่คัดจากคะแนน แยก TRAIN warmup ออกทั้งหมด RP-R-CNN มี timer เพียง 1 ROI; CPI เป็น parent subset 28/27 ROI จึงใช้เป็นตัวแทนเต็มชุดไม่ได้ Sapiens แต่ละขนาดมี 115 ROI; อีก 15 เป็น prior diagnostic predictions ที่ reuse จึงไม่มี timer ของรอบนี้ ไม่เติมศูนย์หรือรวม timer คนละขอบเขตจาก pilot', '',
        '### B. Continuation — ช่วงเวลาระหว่าง UTC events', '',
        '| Model | ROI ที่มี start–end | Mean ms/ROI | Median ms/ROI | P95 ms/ROI | ผลรวม interval s |',
        '|---|---:|---:|---:|---:|---:|']
    for row in rows:
        s = row['UTC_event_interval']
        if s['n']:
            lines.append(f"| {SHORT[row['model_id']]} | {s['n']} | {s['mean_ms']:.3f} | {s['median_ms']:.3f} | {s['p95_ms']:.3f} | {s['total_seconds']:.3f} |")
    lines += ['', 'Continuation ไม่ได้เก็บ adapter_elapsed_seconds จึงใช้ FORWARD_END.utc − FORWARD_START.utc เป็น **event interval** ที่มี pre-synchronization และการบันทึก resource JSON/flush/fsync เพิ่มด้วย ไม่เท่ากับ monotonic adapter timer ของ A และอาจได้รับผลจากการปรับ system clock จึงไม่เฉลี่ยสองตารางเข้าด้วยกัน ไม่ทิ้ง historical failed call: RP-R-CNN มี start ที่ไม่มี end 1 ครั้ง เก็บประวัติไว้แต่ไม่มี duration ที่วัดจบสำหรับ sample นั้น ส่วน CPI parent หยุดที่ pre-forward headroom guard ไม่ใช่หลักฐาน CUDA OOM ในรอบนี้', '',
        '### C. เวลา worker ที่ผ่านไปจริง — บัญชีการทำงาน', '',
        '| Model | จำนวน attempts/segments | Parent s | Continuation s | รวม worker elapsed s |',
        '|---|---:|---:|---:|---:|']
    for row in rows:
        times = row['segments']
        cont = f"{times[1]['worker_elapsed_seconds']:.3f}" if len(times) == 2 else '—'
        lines.append(f"| {SHORT[row['model_id']]} | {len(times)} | {times[0]['worker_elapsed_seconds']:.3f} | {cont} | {row['worker_elapsed_seconds']:.3f} |")
    lines += ['', 'Worker elapsed = STATE.ended_utc − STATE.started_utc รวม setup/model loading, binding/hash checks, warmup, failed-attempt work, packet readback/assembly/I/O และงานบันทึกสถานะที่เกิดใน worker แต่ไม่รวม controller queue/gap ระหว่าง attempts, prior diagnostic run, YOLO cache preparation, GT review หรือ CPU scoring ภายหลัง เป็นเวลาที่ใช้ทำงานในรอบที่ระบุ ไม่ใช่เวลาทำนายใหม่ครบ 90 ภาพจากศูนย์ และไม่ใช่ผลรวม GPU kernel time', '']
    lines += accounting_section(rows)
    lines += ['### ขอบเขตที่รวมและไม่รวม', '',
        '| ขั้นตอน | อยู่ใน A/B หรือไม่ |', '|---|---|',
        '| Frozen YOLO26x segmentation, สร้าง crop และอ่าน/ตรวจ crop PNG รอบนอก | ไม่รวม; เกิดก่อนเข้า forward timer จึงใช้สร้าง end-to-end FPS ไม่ได้ |',
        '| Preprocessing ภายใน adapter, CPU→GPU, parser, GPU→CPU, restore labels สู่ crop grid และ native-instance selection | รวมตาม implementation ของแต่ละ adapter |',
        '| Internal proposals/detector ของ native instance parsers | รวมเมื่อโมเดลนั้นมีอยู่; QANet/Sapiens ไม่ได้ทำงานส่วนเดียวกัน |',
        '| CPI native file I/O | รวมการเปิด crop ผ่าน MMCV, native PNG export/readback และ selected-instance decoding ภายใน infer; จึงไม่ใช่เวลา forward ล้วน |',
        '| Final placement บน original image, YOLO mask clipping/ownership และ atomic packet write/readback | ไม่รวม A; B รวม resource JSON ก่อน event end แต่ยังไม่รวม final packet write/placement เหล่านี้ |',
        '| Model loading, TRAIN warmup, GT scorer, color extraction | ไม่รวมในค่าเฉลี่ย A/B; worker C รวม loading/warmup แต่ไม่รวม GT scoring/color |', '',
        'ขอบเขตตรวจจาก [parent forward timer](../scripts/controlled_roi.py), [continuation event boundaries](../scripts/controlled_roi_continuation.py) และ [crop adapters](../scripts/controlled_roi_models.py) ใช้ [time.monotonic](https://docs.python.org/3/library/time.html#time.monotonic) และ [torch.cuda.synchronize](https://docs.pytorch.org/docs/stable/generated/torch.cuda.synchronize.html) รอบ inference ตาม source จริง Mean = Σt/n; Median คือค่ากลาง; P95 เรียง t แล้ว interpolate ตำแหน่ง 0.95×(n−1) แบบ linear ทุกค่าใช้ successful accepted ROI observations รวม valid empty predictions ไม่เลือกภาพตามคุณภาพ', '',
        '**ข้อสรุปที่ใช้ได้:** ตารางบอกเวลาที่สังเกตได้ของ configuration และสภาพเครื่องในรอบนั้น รวมทั้งจำนวนตัวอย่างที่มีเวลาจริง ไม่เพียงพอจัดอันดับความเร็ว/FPS/VRAM efficiency ข้ามระบบ เพราะมี shared-GPU policy, adapter work, input resolution, PyTorch/CUDA environments และ clock/coverage ต่างกัน การแยกสี่ targets ใช้ forward เดียวกัน ไม่ควรเอาเวลาไปหารสี่เพื่ออ้าง latency ต่อคลาส คะแนนคุณภาพและคำแนะนำเดิมไม่เปลี่ยน', '',
        'Provenance และค่าก่อนปัดเศษ: [STUDY_STATE.json](../STUDY_STATE.json) → runtime_reporting รวม run IDs, sample counts, environments, segment elapsed และ input-hash digest; raw ATTEMPTS.jsonl / RESOURCE_OBSERVATIONS.json / STATE.json อยู่ใน private outputs ของ parent/continuation สร้างซ้ำเฉพาะส่วนนี้ด้วย `python CCTV_Human_Parsing_Benchmark/scripts/report_runtime.py --audit-dir CCTV_Human_Parsing_Benchmark/outputs/<fresh-audit-id>` โดยไม่อ่านภาพ/masks/weights และไม่เริ่ม inference', '<!-- RUNTIME_DIAGNOSTICS_END -->']
    return '\n'.join(lines)+'\n'


def main(audit_dir):
    audit_dir.mkdir(parents=True, exist_ok=False)
    rows, inputs = collect()
    report = P/'reports/CONTROLLED_ROI_FOUR_TARGET_RESULTS_TH.md'
    start, end = '<!-- RUNTIME_DIAGNOSTICS_START -->', '<!-- RUNTIME_DIAGNOSTICS_END -->'
    previous = report.read_text()
    if start in previous:
        prefix, tail = previous.split(start, 1)
        _, suffix = tail.split(end, 1)
        updated = prefix+section(rows)+suffix.lstrip('\n')
    else:
        updated = previous.rstrip()+'\n\n'+section(rows)
    report.write_text(updated)
    assert all(sha(W/path) == digest for path, digest in inputs.items())
    audit = dict(status='HISTORICAL_TIMING_DIAGNOSTICS_COMPLETE', created_utc=datetime.now(timezone.utc).isoformat(),
                 model_calls=0, masks_read=0, quality_scores_changed=False, speed_ranking_eligible=False,
                 models=rows, source_hashes=inputs, script_sha256=sha(__file__), report_sha256=sha(report))
    (audit_dir/'VERIFICATION.json').write_text(json.dumps(audit, indent=2)+'\n')
    print(json.dumps(dict(status=audit['status'], models=len(rows),
                         monotonic_ROIs=sum(r['monotonic_adapter']['n'] for r in rows),
                         UTC_event_ROIs=sum(r['UTC_event_interval']['n'] for r in rows)), indent=2))


if __name__ == '__main__':
    from pathlib import Path
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit-dir', type=Path, required=True)
    main(parser.parse_args().audit_dir)
