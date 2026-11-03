"""Append historical timing diagnostics to the existing CCTV90 results report.

Read small logs/metadata only. Never load a model, image, mask or checkpoint.
Keep monotonic adapter timers separate from UTC event intervals.
"""
import argparse
import csv
from datetime import datetime, timezone
import json
import math
from pathlib import Path
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


def group_image_times(frames, durations):
    """Private per-image rows plus a public aggregate, never infer missing time."""
    image_ids = [frame['image_id'] for frame in frames]
    jobs = [job for frame in frames for job in frame['jobs']]
    if len(set(image_ids)) != len(image_ids) or len(set(jobs)) != len(jobs):
        raise ValueError('Duplicate frame/ROI membership')
    if not set(durations) <= set(jobs):
        raise ValueError('Timed ROI outside frozen image population')
    output = []
    for frame in frames:
        expected = frame['jobs']
        measured = [durations[job] for job in expected if job in durations]
        if any(r['clock'] not in ('MONOTONIC', 'UTC_EVENT') or
               not math.isfinite(r['seconds']) or r['seconds'] < 0 for r in measured):
            raise ValueError('Invalid image timing observation')
        count = len(measured)
        if not expected:
            status, total = 'NO_PARSER_ROIS', 0.
        elif count == len(expected):
            status, total = 'COMPLETE_TIMING', math.fsum(r['seconds'] for r in measured)
        else:
            status = 'PARTIAL_TIMING' if count else 'NO_CURRENT_TIMER'
            total = None
        clock_counts = {clock: sum(r['clock'] == clock for r in measured)
                        for clock in ('MONOTONIC', 'UTC_EVENT')}
        observed = math.fsum(r['seconds'] for r in measured) if measured else 0. if not expected else None
        output.append(dict(image_id=frame['image_id'], ROI_count=len(expected),
                           timed_ROIs=count, untimed_ROIs=len(expected)-count, status=status,
                           monotonic_ROIs=clock_counts['MONOTONIC'], UTC_event_ROIs=clock_counts['UTC_EVENT'],
                           observed_interval_ms=None if observed is None else observed*1000,
                           image_parsing_work_ms=None if total is None else total*1000))
    complete = [row for row in output if row['image_parsing_work_ms'] is not None]
    nonempty = [row for row in complete if row['ROI_count']]
    full = len(complete) == len(output)
    known = math.fsum(row['observed_interval_ms']/1000 for row in output
                     if row['observed_interval_ms'] is not None)
    public = dict(expected_images=len(output), images_with_complete_timing=len(complete),
                  no_parser_ROI_images=sum(row['ROI_count'] == 0 for row in output),
                  complete_nonempty_images=len(nonempty),
                  partial_timing_images=sum(row['status'] == 'PARTIAL_TIMING' for row in output),
                  images_without_current_timer=sum(row['status'] == 'NO_CURRENT_TIMER' for row in output),
                  full_population_timing_complete=full,
                  full_population_parsing_work_seconds=known if full else None,
                  full_population_mean_ms_per_image=known*1000/len(output) if full and output else None,
                  complete_images_statistics=describe_seconds([row['image_parsing_work_ms']/1000 for row in complete]),
                  complete_nonempty_statistics=describe_seconds([row['image_parsing_work_ms']/1000 for row in nonempty]),
                  recorded_interval_sum_seconds=known, end_to_end_latency=False)
    return output, public


def collect(per_image_rows=None):
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
    source_config = load(W/config['parent_config'])
    assert sha(W/config['parent_config']) == config['parent_config_sha256']
    source_images = {member['id']: str(Path(source_config['dataset_root'])/'Images'/(member['stem']+'.jpg'))
                     for member in source_config['members']}
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
        durations = {}
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
                    seconds = row['adapter_elapsed_seconds']
                    mono.append(seconds)
                else:
                    assert 'adapter_elapsed_seconds' not in row
                    seconds = pairs[key]['UTC_interval_seconds']
                    wall_events.append(seconds)
                assert key not in durations
                durations[key] = dict(seconds=seconds, clock=clock)
            assert all(r['purpose'] != 'TRAIN_WARMUP' for r in incomplete.values())
            unfinished += len(incomplete)
            elapsed = (datetime.fromisoformat(state['ended_utc']) - datetime.fromisoformat(state['started_utc'])).total_seconds()
            assert elapsed >= 0
            segments.append(dict(run_id=root.name, worker_elapsed_seconds=elapsed, status=state['status']))
        reused = set(config['reuse'][mid])
        assert not committed & reused and committed | reused == expected
        private_frames, image_summary = group_image_times(manifest['frames'], durations)
        if per_image_rows is not None:
            per_image_rows.extend(dict(model_id=mid, source_image=source_images[row['image_id']], **row)
                                  for row in private_frames)
        result.append(dict(model_id=mid, frames=90, ROI_population=130,
                           monotonic_adapter=describe_seconds(mono), UTC_event_interval=describe_seconds(wall_events),
                           prior_diagnostic_ROIs_without_current_timing=len(reused), warmup_calls_excluded=warmups,
                           unfinished_forward_starts=unfinished, segments=segments,
                           worker_elapsed_seconds=sum(s['worker_elapsed_seconds'] for s in segments),
                           parent_environment=environment, per_image_summary=image_summary))
    assert sum(r['monotonic_adapter']['n'] + r['UTC_event_interval']['n'] for r in result) == closure['successful_new_unique_ROI_observations']
    assert sum(r['warmup_calls_excluded'] for r in result) == closure['TRAIN_warmup_calls']
    assert sum(r['unfinished_forward_starts'] for r in result) == closure['retained_failed_RPR_learned_calls']
    for row in result:
        row['time_accounting'] = time_accounting(row)
        assert math.isclose(row['per_image_summary']['recorded_interval_sum_seconds'],
                            row['time_accounting']['logged_interval_sum_seconds'], rel_tol=0, abs_tol=1e-10)
    return result, inputs


def image_section(rows):
    def number(value):
        return 'null' if value is None else f'{value:.3f}'
    lines = ['### E. เวลาต่อหนึ่งภาพ และรวมทั้ง 90 ภาพ', '',
        '**เวลาประมวลผลต่อภาพในขั้น parsing คือผลรวมเวลาของทุก ROI ในภาพนั้น** โดย ROI คือภาพย่อยของบุคคลที่ได้จาก YOLO ตัวอย่างเช่น หากภาพหนึ่งมีสอง ROI ที่ใช้เวลา 70 และ 90 ms เวลารวมของภาพนั้นจะเท่ากับ 160 ms คำนวณจากเวลาที่บันทึกจริงของแต่ละ ROI ไม่ได้นำเวลาเฉลี่ยต่อ ROI มาคูณจำนวนคน และยังไม่รวมเวลาของ pipeline ทั้งหมด', '',
        '| โมเดล | ภาพที่มีข้อมูลเวลาครบ / 90 | เฉลี่ยต่อภาพที่มีข้อมูลครบ (ms) | เฉลี่ยต่อภาพทั้งชุด 90 ภาพ (ms) | เวลารวมทั้งชุด 90 ภาพ (s) | ผลรวมเวลาที่บันทึกได้ (s) |',
        '|---|---:|---:|---:|---:|---:|']
    for row in rows:
        s = row['per_image_summary']
        lines.append(f"| {SHORT[row['model_id']]} | {s['images_with_complete_timing']}/90 | {number(s['complete_images_statistics']['mean_ms'])} | {number(s['full_population_mean_ms_per_image'])} | {number(s['full_population_parsing_work_seconds'])} | {number(s['recorded_interval_sum_seconds'])} |")
    complete_pairs = sum(row['per_image_summary']['images_with_complete_timing'] for row in rows)
    population = sum(row['per_image_summary']['expected_images'] for row in rows)
    observed = math.fsum(row['per_image_summary']['recorded_interval_sum_seconds'] for row in rows)
    lines += ['', f'ตารางรายภาพมี **{population} รายการ จาก 9 โมเดลที่ประเมินภาพชุดเดิม 90 ภาพ** มีข้อมูลเวลาครบ {complete_pairs}/{population} รายการ ผลรวมเวลาที่บันทึกได้คือ {observed:.3f} s แต่ยังใช้แทนเวลารวมครบ 90 ภาพของทุกโมเดลไม่ได้ หากโมเดลนั้นมีช่อง null', '',
        '**null หมายถึงข้อมูลเวลาไม่เพียงพอ ไม่ใช่ใช้เวลาเป็นศูนย์** มี 8 ภาพที่ YOLO ไม่พบ ROI จึงไม่มีการเรียก parser และเวลาเฉพาะขั้น parsing เป็น 0 จริง ค่าเฉลี่ยรวมภาพเหล่านี้ด้วย แต่การอ่านภาพและการทำงานของ YOLO ยังมีต้นทุน ส่วนภาพที่มี ROI แต่ขาดข้อมูลเวลาจะคงเป็น null โดยไม่เติมศูนย์หรือประมาณจากภาพอื่น', '',
        'Sapiens แต่ละขนาดนำผลเดิม 15 ROIs จาก 6 ภาพกลับมาใช้ จึงมีข้อมูลเวลาของรอบนี้ครบ 84/90 ภาพ คอลัมน์เฉลี่ยเฉพาะภาพที่มีข้อมูลครบใช้ตัวหาร 84 ส่วนค่าเฉลี่ยและเวลารวมของทั้งชุด 90 ภาพเป็น null ผลทำนายยังครบ 90 ภาพ/130 ROIs และคะแนนคุณภาพไม่ได้ขาดตามไปด้วย เวลาของการทดลองเดิมจับเฉพาะ model forward โดยไม่รวม preprocessing และ map-back จึงนำมาเติมช่วงเวลาของ adapter ที่ขาดไม่ได้', '',
        'ดูเวลารายภาพได้จากไฟล์ส่วนตัว `outputs/<runtime-report-id>/PER_IMAGE_TIMING.csv` ที่สร้างโดย report_runtime.py มีรหัสโมเดล ชื่อภาพต้นทาง จำนวน ROI จำนวน ROI ที่มีเวลา สถานะ และเวลารวมของภาพนั้น หากข้อมูลไม่ครบจะเป็น null ไฟล์นี้มีข้อมูลอ้างอิงภาพ CCTV จึงไม่เผยแพร่บน public Git ดูตำแหน่ง จำนวนรายการ และ hash ได้ใน STUDY_STATE.json → per_image_timing_reporting', '',
        '| ตัวชี้วัด | สูตร / ตัวหาร | ความหมาย |', '|---|---|---|',
        '| เวลาต่อภาพในขั้น parsing (image_parsing_work_ms) | บวกเวลา ROI ทุกคนของภาพนั้น แล้วแปลงเป็น ms; ต้องมีข้อมูลครบทุก ROI | ผลรวมเวลาที่บันทึกของภาพนั้น หน่วย ms; ขอบเขตการจับเวลา A/B ยังต่างกันตามที่ระบุ |',
        '| เวลาเฉลี่ยต่อภาพที่มีข้อมูลครบ | ผลรวมเวลาต่อภาพที่มีข้อมูลครบ ÷ จำนวนภาพที่มีข้อมูลครบ; หน่วย ms ต่อภาพ | รวมเฉพาะภาพที่มีข้อมูลเวลาครบ รวมภาพที่ไม่มี ROI; Sapiens ใช้ 84 ภาพ โมเดลอื่นใช้ 90 ภาพ จึงไม่ใช้จัดอันดับความเร็วบนชุดภาพเดียวกัน |',
        '| เวลาเฉลี่ยต่อภาพทั้งชุด 90 ภาพ | ผลรวมเวลาของทั้งชุด ÷ 90; หน่วย ms ต่อภาพ คำนวณได้เมื่อครบทั้ง 90 ภาพ | หากภาพใดขาดข้อมูลเวลา ค่านี้จะเป็น null |',
        '| เวลารวมทั้งชุด 90 ภาพ | บวกเวลาต่อภาพทั้ง 90 ภาพ แล้วหาร 1,000 เพื่อแปลง ms เป็นวินาที | รวมเวลาเฉพาะขั้น parsing หน่วย s ไม่รวม YOLO การส่งออกไฟล์ scorer สี หรือฐานข้อมูล |',
        '| ผลรวมเวลาที่บันทึกได้ | รวมเฉพาะช่วงเวลาที่มี log | อาจรวมบาง ROI ของภาพที่ข้อมูลยังไม่ครบ จึงใช้แทนเวลารวมของทั้งชุดไม่ได้ |', '',
        'ส่วน A–D รายงานเวลาต่อ ROI และเวลาของ worker ส่วน E จัดกลุ่ม ROI ตามภาพใน input manifest เดิม ไม่ได้จับเวลา inference ใหม่ ไม่ใช้เวลา worker หาร 90 และไม่ลบ timestamp ของ FRAME_COMMITTED เพื่อแทนเวลาต่อภาพ เพราะการทำงานอาจสลับภาพและมีขั้นตอนเตรียมหรือประกอบผลคั่นอยู่ ไม่มีการรันเพิ่มเพื่อเติมช่อง null', '']
    return lines


def accounting_section(rows):
    lines = ['<a id="d-ตารางสรุปรวม--บวกค่าที่มี-log-แล้ว"></a>', '',
        '### D. สรุปเวลาที่บันทึกได้และเวลารวมของ worker', '',
        '**ไม่ได้จับเวลาแยกรายคลาส:** โมเดลทำนายทุกคลาสเดิมพร้อมกันในหนึ่ง forward (CIHP 20 / Sapiens 29 คลาส) แล้วจึงแปลงผลเป็น Hair / Face / Upper / Lower เพื่อประเมินภายหลัง จึงแบ่งเวลารวมเป็นเวลาของแต่ละคลาสไม่ได้ ส่วน IoU/Recall/Precision/Dice รายคลาสดูได้ในตารางคุณภาพและ confusion matrix ข้างต้น', '',
        '| โมเดล | ROI ที่มีข้อมูลเวลา / 130 | รวม A (s) | รวม B (s) | รวมช่วงเวลาที่บันทึก A+B (s) | เวลารวมของ worker C (s) |',
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
    lines += [f'| **รวม 9 ระบบ** | **{measured}/{population}** | **{sums[0]:.3f}** | **{sums[1]:.3f}** | **{combined:.3f}** | **{workers:.3f}** |', '',
        '**A+B รวมช่วงเวลาของ ROI ที่สำเร็จและไม่ซ้ำกัน** แต่ A/B ใช้นาฬิกาและขอบเขตการจับเวลาต่างกัน จึงไม่ใช่ latency ที่วัดด้วยวิธีเดียวกัน อีกทั้ง Sapiens มีเวลาบันทึกเพียง 115 จาก 130 ROIs เครื่องหมาย — หมายถึงไม่มีช่วงเวลาจาก continuation ให้รวม ไม่ใช่ประมวลผลโดยใช้เวลาเป็นศูนย์ ไม่ประมาณเวลาอีก 15 ROIs จากค่าเฉลี่ย ยอดรวมใช้ค่าก่อนปัดเศษ จึงอาจต่างจากผลบวกของเลข 3 ตำแหน่งที่แสดงเล็กน้อย', '',
        '**ไม่บวก A+B+C เพราะจะนับเวลาซ้ำ:** C ครอบช่วง A/B อยู่แล้ว หากต้องการเวลารวมของ worker ให้ใช้ C ซึ่งบวกรอบหลักและรอบ continuation แล้ว ผลรวม 9 ระบบเป็นเวลารวมของงานทั้งเก้า ไม่ใช่เวลาต่อภาพ ระยะเวลาทั้ง batch ที่รวมช่วงรอ หรือเวลาเต็มเส้นทาง YOLO → parsing → สี → ฐานข้อมูล', '',
        '### นิยามตัวชี้วัดเวลาและจำนวนตัวอย่าง\n\n**หน่วยเวลา:** 1 วินาที (s) = 1,000 มิลลิวินาที (ms) คำว่า ms/ROI หมายถึงเวลาต่อภาพย่อยของบุคคลหนึ่งรายการ ไม่ใช่ต่อภาพต้นฉบับ ส่วน ms/ภาพหมายถึงผลรวมเวลาของทุก ROI ในภาพนั้นตามตาราง E\n\n**ตัวอย่างสมมติของ A:** เริ่มอ่านนาฬิกาที่ 100.000 s หลังรอ GPU ก่อนหน้าเสร็จ เรียก adapter แล้วรอ GPU ของงานนี้เสร็จ อ่านได้ 100.070 s จึงใช้เวลา 0.070 s หรือ 70 ms ต่อ ROI ชื่อนาฬิกาเป็นตัวนับระยะเวลา ไม่ใช่เวลาเกิดเหตุในภาพ\n\n**ตัวอย่างสมมติของสถิติ:** ROI ห้ารายการใช้เวลา 10, 20, 30, 40, 50 ms ผลรวมคือ 150 ms; Mean=150÷5=30 ms; Median=30 ms; P95=48 ms จากการคั่นค่าระหว่าง 40 กับ 50 ตามตำแหน่งร้อยละ 95 ทั้งหมดเป็นตัวอย่างอธิบายวิธีคิด ไม่ใช่ผลของโมเดลใดในตาราง', '',
        '| ตัวชี้วัด | สูตรและหน่วย | ความหมายและข้อจำกัด | ที่มา |',
        '|---|---|---|---|',
        '| A: เวลาเรียกตัวเชื่อมโมเดล หรือ adapter | เวลาหลัง adapter และ GPU ทำงานเสร็จ − เวลาเริ่มเรียก adapter; หน่วยวินาทีต่อ ROI | จับหลังรอ GPU ก่อนเริ่มแล้ว และหยุดหลังรอ GPU ของงานนี้เสร็จ รวมการเตรียมข้อมูล การส่งข้อมูล และการคืนผลภายใน adapter ไม่ใช่เวลาเฉพาะ neural network | [จุดจับเวลาในรอบหลัก](../scripts/controlled_roi.py); ฟิลด์ `adapter_elapsed_seconds` |',
        '| B: ช่วงเวลาระหว่างบันทึกเริ่มและจบในรอบทำต่อ | เวลาของบันทึกจบ − เวลาของบันทึกเริ่ม; หน่วยวินาทีต่อ ROI | เริ่มก่อนรอ GPU และจบหลังบันทึกข้อมูลทรัพยากร จึงรวมงานมากกว่า A และใช้นาฬิกาวันเวลาของระบบ | [บันทึกเวลาในรอบทำต่อ](../scripts/controlled_roi_continuation.py) |',
        '| Mean: เวลาเฉลี่ยต่อ ROI (ms) | ผลรวมเวลาที่บันทึกเป็นวินาที ÷ จำนวน ROI ที่มีเวลา แล้วคูณ 1,000 | เฉลี่ยเฉพาะ ROI ที่มีข้อมูลเวลาในกลุ่มนั้น แม้ถ่วงด้วยจำนวน ROI ก็ยังทำให้ขอบเขต A/B เหมือนกันไม่ได้ | [โค้ดคำนวณสถิติเวลา](../scripts/report_runtime.py) จากข้อมูลที่ตรวจรับแล้ว |',
        '| Median: เวลาค่ากลางต่อ ROI (ms) | เรียงเวลาแต่ละ ROI จากน้อยไปมาก ใช้ค่ากลาง; ถ้ามีจำนวนคู่ให้เฉลี่ยสองค่ากลาง | แสดงเวลาของข้อมูลลำดับกลาง ได้รับผลจากค่าสุดขั้วน้อยกว่าค่าเฉลี่ย | สถิติเชิงพรรณนาของแต่ละกลุ่ม log |',
        '| P95: เวลาบริเวณเปอร์เซ็นไทล์ที่ 95 ต่อ ROI (ms) | เรียงเวลาแล้วหาตำแหน่งร้อยละ 95; ถ้าอยู่ระหว่างสองค่า ให้คั่นค่าตามสัดส่วนระยะห่าง | แสดงค่าบริเวณปลายด้านช้าของข้อมูลที่วัด ไม่ใช่ช่วงความเชื่อมั่นหรือคำรับประกัน 95% ของภาพใหม่ | [โค้ดคำนวณสถิติเวลา](../scripts/report_runtime.py); เมื่อมีเวลาเพียงหนึ่ง ROI ค่า P95 จะเท่ากับเวลาของ ROI นั้น |',
        '| ผลรวม A+B | ผลรวมเวลา ROI ใน A + ผลรวมเวลา ROI ใน B; หน่วยวินาที | รวมช่วงเวลาที่มี log ของ ROI ที่ไม่ซ้ำกัน โดยยังคงความต่างของวิธีจับเวลา ไม่ใช่เวลารวมทั้ง pipeline | [โค้ดรวมบัญชีเวลา](../scripts/report_runtime.py) |',
        '| C: เวลารวมของ worker | นำเวลาจบ worker ลบเวลาเริ่มของแต่ละรอบ แล้วบวกรอบที่นำมารายงาน; หน่วยวินาที | รวมการโหลด warmup การตรวจไฟล์ การส่งออกผล และงานใน attempt ที่ล้มเหลว ไม่รวมช่วงรอระหว่าง attempts หรืองานนอก worker | `STATE.json` ของรอบหลักและรอบทำต่อ; ตาราง C |',
        '| สัดส่วน ROI ที่มีข้อมูลเวลา | จำนวน ROI ที่มีเวลาจาก A และ B ÷ 130; คูณ 100 เมื่อต้องการเปอร์เซ็นต์ | บอกว่ามีเวลาให้คำนวณกี่ ROI ไม่ใช่ความครบถ้วนของผลทำนายหรือความแม่นยำ | จับคู่ log กับ ROI ที่ตรวจรับแล้ว; Sapiens มีเวลา 115/130=88.462% แต่ผลทำนายครบ 130 ROIs |', '',
        'Mean/Median/P95 เป็นสถิติสรุปเวลา ส่วน IoU/Recall/Precision/Dice เป็นตัวชี้วัดคุณภาพการแบ่งส่วนภาพ ซึ่งอธิบายแยกไว้ในส่วน confusion matrix รายงานนี้ไม่รวมคุณภาพกับความเร็วเป็นคะแนนใหม่ และไม่ใช้ตารางเวลาเปลี่ยนผู้ชนะตามเกณฑ์คุณภาพเดิม', '']
    return lines


def section(rows):
    lines = ['<!-- RUNTIME_DIAGNOSTICS_START -->', '## ความเร็วและเวลาประมวลผลจาก log เดิม', '',
        '**ตารางนี้สรุปเวลาจาก log เดิมบน Tesla T4 ภายใต้นโยบายใช้ GPU ร่วม** ไม่ใช่ benchmark ความเร็วของ model forward เพียงอย่างเดียวหรือ pipeline ทั้งระบบ ไม่มีการรันโมเดลเพิ่ม หน่วยหลักคือหนึ่ง ROI หรือภาพย่อยของบุคคลที่ YOLO ตรวจพบ ชุด 90 ภาพมี 130 ROIs และมี 8 ภาพที่ไม่มี detection แต่ละ call ทำนายทุกคลาสเดิมพร้อมกัน จึงไม่มีเวลาราย Hair / Face / Upper / Lower', '',
        '### A. เวลาของ adapter ในรอบหลัก — จับด้วยนาฬิกาวัดระยะเวลา', '',
        '| โมเดล | ROI ที่มีข้อมูลเวลา / 130 | เฉลี่ยต่อ ROI (ms) | ค่ากลางต่อ ROI (ms) | P95 ต่อ ROI (ms) | เวลารวมที่บันทึกได้ (s) |',
        '|---|---:|---:|---:|---:|---:|']
    for row in rows:
        s = row['monotonic_adapter']
        lines.append(f"| {SHORT[row['model_id']]} | {s['n']}/130 | {s['mean_ms']:.3f} | {s['median_ms']:.3f} | {s['p95_ms']:.3f} | {s['total_seconds']:.3f} |")
    lines += ['', 'รวม ROI_READINESS ที่อยู่ในชุดประเมินจริง แต่ไม่นับ TRAIN warmup ไม่มีการรันซ้ำเพื่อจับเวลาและไม่คัดภาพตามคะแนน RP-R-CNN มีเวลารอบหลักเพียง 1 ROI ส่วน CPI มี 28/27 ROIs จึงยังไม่แทนทั้งชุด Sapiens แต่ละขนาดมีเวลาของ 115 ROIs อีก 15 ROIs นำผลจากการทดลองเดิมมาใช้ จึงไม่มีเวลาของรอบนี้ ไม่เติมศูนย์หรือนำเวลาจาก pilot ที่จับคนละขอบเขตมารวม', '',
        '### B. เวลาของรอบทำต่อ — คำนวณจากบันทึกเริ่มและจบ', '',
        '| โมเดล | ROI ที่มีเวลาเริ่มและจบ | เฉลี่ยต่อ ROI (ms) | ค่ากลางต่อ ROI (ms) | P95 ต่อ ROI (ms) | ผลรวมช่วงเวลา (s) |',
        '|---|---:|---:|---:|---:|---:|']
    for row in rows:
        s = row['UTC_event_interval']
        if s['n']:
            lines.append(f"| {SHORT[row['model_id']]} | {s['n']} | {s['mean_ms']:.3f} | {s['median_ms']:.3f} | {s['p95_ms']:.3f} | {s['total_seconds']:.3f} |")
    lines += ['', 'รอบทำต่อไม่ได้เก็บค่าจากตัวจับเวลาแบบ A จึงใช้เวลาของบันทึกจบลบเวลาของบันทึกเริ่ม โดยบันทึกจบใช้ชื่อ `FORWARD_END` และบันทึกเริ่มใช้ชื่อ `FORWARD_START` ช่วงนี้รวมการรอ GPU ก่อนเรียกโมเดลและการเขียนข้อมูลทรัพยากรลงดิสก์ ต่างจาก A และอาจได้รับผลจากการปรับนาฬิการะบบ จึงไม่เฉลี่ย A/B รวมเป็นค่าความเร็วที่มีขอบเขตเดียวกัน RP-R-CNN มี 1 ครั้งที่เริ่มแล้วไม่มีบันทึกจบ จึงไม่มีเวลาที่คำนวณได้สำหรับครั้งนั้น ส่วน CPI รอบหลักหยุดเพราะ guard พื้นที่หน่วยความจำก่อนเรียกโมเดล ไม่ใช่หลักฐาน CUDA OOM ของรอบนี้', '',
        '### C. เวลาที่ worker ทำงานในแต่ละรอบ', '',
        '| โมเดล | จำนวนรอบที่รัน | รอบหลัก (s) | รอบทำต่อ (s) | เวลารวมของ worker (s) |',
        '|---|---:|---:|---:|---:|']
    for row in rows:
        times = row['segments']
        cont = f"{times[1]['worker_elapsed_seconds']:.3f}" if len(times) == 2 else '—'
        lines.append(f"| {SHORT[row['model_id']]} | {len(times)} | {times[0]['worker_elapsed_seconds']:.3f} | {cont} | {row['worker_elapsed_seconds']:.3f} |")
    lines += ['', 'Worker คือโปรแกรมเบื้องหลังที่ประมวลผลโมเดล เวลาของแต่ละรอบคำนวณจากเวลาจบลบเวลาเริ่มที่เก็บใน `STATE.json` แล้วบวกรอบหลักกับรอบทำต่อ ค่านี้รวมการเตรียมงาน โหลดโมเดล ตรวจไฟล์ อุ่นเครื่อง (warmup) งานใน attempt ที่ล้มเหลว การประกอบ/บันทึกผล และการบันทึกสถานะ ภายในรอบเหล่านั้น แต่ไม่รวมช่วงรอระหว่างรอบ ต้นทุนการทดลองเก่าที่นำผลกลับมาใช้ การสร้าง YOLO cache การตรวจ GT หรือการให้คะแนนบน CPU ภายหลัง จึงเป็นบัญชีเวลา worker ของรอบที่นำมารายงาน ไม่ใช่เวลาเฉพาะการคำนวณบน GPU หรือเวลาเริ่มใหม่ครบทุกภาพโดยไม่ reuse', '']
    lines += accounting_section(rows)
    lines += image_section(rows)
    lines += ['### ขอบเขตที่รวมและไม่รวม', '',
        '| ขั้นตอน | รวมอยู่ในเวลา A/B หรือไม่ |', '|---|---|',
        '| YOLO26x แยกคน การสร้าง crop และการอ่าน/ตรวจ crop PNG ก่อนเข้า adapter | ไม่รวม จึงยังคำนวณ FPS ของ pipeline ทั้งหมดไม่ได้ |',
        '| Preprocessing ภายใน adapter, CPU→GPU, parser, GPU→CPU, การคืน labels สู่พิกัด crop และการเลือก native instance | รวมตามขั้นตอนที่แต่ละ adapter ใช้จริง |',
        '| Internal proposals/detector ของโมเดลที่ทำนาย instances | รวมเมื่อโมเดลนั้นมีขั้นตอนนี้; QANet/Sapiens ไม่ได้ทำงานส่วนเดียวกัน |',
        '| การอ่านและเขียนไฟล์ native ของ CPI | รวมการเปิด crop ผ่าน MMCV การส่งออก/อ่าน native PNG และการเลือก instance ภายใน infer จึงไม่ใช่เวลา forward อย่างเดียว |',
        '| การวางผลบนภาพต้นฉบับ การตัดด้วย YOLO mask/กำหนด ownership และการเขียน/อ่าน atomic packet | ไม่รวมใน A/B แม้ B จะรวมการเขียน resource JSON ก่อน event end |',
        '| การโหลดโมเดล TRAIN warmup การให้คะแนนกับ GT และการสกัดสี | ไม่รวมในค่าเฉลี่ย A/B; C รวมการโหลดและ warmup แต่ไม่รวม GT scoring หรือสี |', '',
        'ตรวจจุดเริ่ม/จบจาก [ตัวจับเวลารอบหลัก](../scripts/controlled_roi.py), [บันทึกในรอบทำต่อ](../scripts/controlled_roi_continuation.py) และ [ตัวเชื่อมโมเดลสำหรับ ROI](../scripts/controlled_roi_models.py) รอบ A ใช้ [time.monotonic](https://docs.python.org/3/library/time.html#time.monotonic) ซึ่งเหมาะกับวัดระยะเวลา และรอ GPU ให้ทำงานเสร็จด้วย [torch.cuda.synchronize](https://docs.pytorch.org/docs/stable/generated/torch.cuda.synchronize.html) ไม่อ่านเพียงเวลาที่ CPU ส่งคำสั่งเสร็จ สถิติใช้ ROI ที่ประมวลผลสำเร็จและตรวจรับแล้ว รวมผลทำนายว่างที่ถูกต้องตาม contract ไม่คัดจากคะแนนคุณภาพ', '',
        '**ขอบเขตการตีความ:** ใช้อธิบายเวลาที่บันทึกได้ของแต่ละ configuration ในสภาพเครื่องรอบนั้น พร้อมจำนวนตัวอย่างที่มีข้อมูลเวลา ยังใช้จัดอันดับความเร็ว/FPS/ประสิทธิภาพ VRAM ข้ามระบบไม่ได้ เพราะการใช้ GPU ร่วม ขั้นตอนใน adapter ความละเอียด input รุ่น PyTorch/CUDA วิธีจับเวลา และความครบถ้วนของข้อมูลต่างกัน ทุกคลาสถูกทำนายใน forward เดียว จึงหารเวลาด้วยสี่เพื่ออ้างเวลารายคลาสไม่ได้ คะแนนคุณภาพและคำแนะนำเดิมคงอยู่', '',
        'ค่าก่อนปัดเศษและหลักฐานอ้างอิงอยู่ใน [STUDY_STATE.json](../STUDY_STATE.json) → runtime_reporting ระบุ run IDs จำนวนตัวอย่าง environments เวลาของแต่ละ segment และ hash ของ inputs ส่วน raw ATTEMPTS.jsonl / RESOURCE_OBSERVATIONS.json / STATE.json เก็บใน private outputs ของรอบหลัก/continuation สร้างรายงานส่วนนี้ซ้ำได้ด้วย `python CCTV_Human_Parsing_Benchmark/scripts/report_runtime.py --audit-dir CCTV_Human_Parsing_Benchmark/outputs/<fresh-audit-id>` โดยไม่อ่านภาพ masks หรือ weights และไม่เริ่ม inference', '<!-- RUNTIME_DIAGNOSTICS_END -->']
    return '\n'.join(lines)+'\n'


def main(audit_dir):
    audit_dir.mkdir(parents=True, exist_ok=False)
    private_rows = []
    rows, inputs = collect(per_image_rows=private_rows)
    private_csv = audit_dir/'PER_IMAGE_TIMING.csv'
    with private_csv.open('w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=list(private_rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows({k: 'null' if value is None else value for k, value in row.items()} for row in private_rows)
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
                 models=rows, source_hashes=inputs, script_sha256=sha(__file__), report_sha256=sha(report),
                 private_per_image_CSV=dict(filename=private_csv.name, rows=len(private_rows), sha256=sha(private_csv)))
    (audit_dir/'VERIFICATION.json').write_text(json.dumps(audit, indent=2)+'\n')
    print(json.dumps(dict(status=audit['status'], models=len(rows),
                         monotonic_ROIs=sum(r['monotonic_adapter']['n'] for r in rows),
                         UTC_event_ROIs=sum(r['UTC_event_interval']['n'] for r in rows)), indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit-dir', type=Path, required=True)
    main(parser.parse_args().audit_dir)
