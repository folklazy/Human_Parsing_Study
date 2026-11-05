def worker(cp, mid):
    import torch
    CropModel = model_factory
    from sapiens_input_variants import detector_crop
    from controlled_ci_hp.measurement import Measurements
    from controlled_ci_hp.scoring import evaluate
    from common_view.core import load_spec
    from common_view.full import Accumulator
    import shutil
    config = verify_config(cp)
    root = W/config['artifact_root']
    output = root/mid
    output.mkdir(exist_ok=False)
    lock = (H/'outputs/CONTROLLED_CIHP_GPU.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    started = time.monotonic()
    state = dict(model_id=mid, status='INITIALIZING', pid=os.getpid(), started_utc=utc(),
                 completed=0, expected=5000, ROI_calls=0, warmup_calls=0, failed=0, invalid=0,
                 primary=None, speed_ranking_allowed=False)
    spec = config['models'][mid]
    manifest = read(W/config['manifest'])
    accumulator = Accumulator(manifest['expected_ids'])
    part_sums = {str(c): dict(count=0, IoU_sum=0., TP=0, FP=0, FN=0, unmatched=0) for c in range(1,5)}
    bytes_written = 0
    measured_storage = [0, -1]
    ledger = (output/'ATTEMPTS.jsonl').open('x', buffering=1)

    def save():
        atomic(output/'STATE.json', state)

    def guard():
        if shutil.disk_usage(root).free < config['minimum_free_gib']*2**30:
            raise RuntimeError('RESOURCE_DISK_FREE_GUARD')
        if state['completed']//25 != measured_storage[1]:
            measured_storage[0] = sum(p.stat().st_size for p in output.rglob('*') if p.is_file())
            measured_storage[1] = state['completed']//25
        if max(bytes_written, measured_storage[0])+config['prior_stream_bytes'].get(mid,0) > config['max_stream_gib']*2**30:
            raise RuntimeError('RESOURCE_STREAM_DISK_GUARD')
        if time.monotonic()-started+config['prior_execution_seconds'].get(mid,0) > config['max_hours']*3600:
            raise RuntimeError('RESOURCE_TIME_GUARD')
        if torch.cuda.mem_get_info()[0] < config['min_forward_free_MiB']*2**20:
            raise RuntimeError('RESOURCE_VRAM_HEADROOM_GUARD')

    def infer(rgb, path, box, purpose):
        guard()
        calls = state['ROI_calls']+state['warmup_calls']
        if calls >= config['pending_call_limits'][mid]:
            raise RuntimeError('MODEL_CALL_BUDGET')
        key = 'warmup_calls' if purpose.startswith('TRAIN') else 'ROI_calls'
        state[key] += 1
        save()
        emit(ledger, event='MODEL_CALL_START', purpose=purpose, image=state.get('current_id'), calls=calls+1)
        measure = Measurements(torch.cuda.synchronize)
        torch.cuda.reset_peak_memory_stats()
        if purpose == 'TRAIN_BASELINE':
            from controlled_roi_models import CropModel as OriginalModel
            result = OriginalModel.infer(model, rgb, path, box)
            torch.cuda.synchronize()
        else:
            result = measure.infer(model, rgb, path, box)
        emit(ledger, event='MODEL_CALL_END', purpose=purpose, measurements=measure.report(),
             allocated_MiB=torch.cuda.max_memory_allocated()/2**20,
             reserved_MiB=torch.cuda.max_memory_reserved()/2**20)
        return result, measure.report()

    save()
    try:
        free = torch.cuda.mem_get_info()[0]/2**20
        if free < config['required_free_MiB'][mid]:
            raise RuntimeError('RESOURCE_PRELOAD_FREE_VRAM_GUARD')
        checked(spec['checkpoint'], spec['checkpoint_sha256'])
        checked(spec['native_config'], spec['native_config_sha256'])
        source_commit = subprocess.check_output(['git','-C',str(W/spec['source']),'rev-parse','HEAD'], text=True).strip()
        if source_commit != spec['source_commit']:
            raise ValueError('Source git revision mismatch')
        torch.set_num_threads(2)
        torch.manual_seed(config['seed'])
        np.random.seed(config['seed'])
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        atomic(output/'RESOURCE_AT_LOAD.json', telemetry())
        before_load = time.monotonic()
        model = CropModel(W, spec, output)
        torch.cuda.synchronize()
        state['model_load_seconds'] = time.monotonic()-before_load
        atomic(output/'ENVIRONMENT.json', dict(python=sys.version, executable=sys.executable,
            torch=torch.__version__, CUDA=torch.version.cuda, GPU=torch.cuda.get_device_name(0),
            CUDA_VISIBLE_DEVICES=os.environ.get('CUDA_VISIBLE_DEVICES'), numpy=np.__version__,
            config_sha256=sha(cp), source_commit=source_commit, FP32=True, AMP=False, TF32=False))
        warm = config['warmup']
        path = checked(warm['image'], warm['png_sha256'])
        rgb = np.asarray(Image.open(path).convert('RGB'))
        state['status'] = 'TRAIN_READINESS'
        baseline, _ = infer(rgb, path, warm['designated_box'], 'TRAIN_BASELINE')
        result, timing = infer(rgb, path, warm['designated_box'], 'TRAIN_TIMED_PARITY')
        if not np.array_equal(baseline[0], result[0]) or not np.array_equal(baseline[1], result[1]):
            raise ValueError('INSTRUMENTATION_HARD_MASK_PARITY_FAILURE')
        validate_native(result[0], model.classes, rgb.shape[:2])
        probe = write_packet(output/'readiness', 'TRAIN0000930',
            dict(native_crop_mask=result[0], native_candidate_masks=result[1]),
            dict(config_sha256=sha(cp), checkpoint_sha256=spec['checkpoint_sha256'], timing=timing,
                 geometry=result[2], purpose='TRAIN_NOT_VALIDATION'), {})
        read_packet(probe)
        readiness_bytes = sum(p.stat().st_size for p in probe.iterdir() if p.is_file())
        estimate = (readiness_bytes*config['ROI_count']+config['storage']['final_arrays_uncompressed_per_model_bytes'])*1.25
        if estimate > config['max_stream_gib']*2**30:
            raise RuntimeError('RESOURCE_TRAIN_STORAGE_ESTIMATE_EXCEEDS_STREAM_CAP')
        if shutil.disk_usage(root).free-estimate < config['minimum_free_gib']*2**30:
            raise RuntimeError('RESOURCE_TRAIN_STORAGE_ESTIMATE_EXCEEDS_FREE_DISK')
        atomic(output/'READINESS.json',dict(status='PASS', TRAIN_calls=2,
            original_vs_instrumented_native_hard_masks='IDENTICAL_ON_TRAIN_ROI',
            resource_observation=telemetry(),
            projected_storage_bytes=estimate, estimate_limitation='One TRAIN ROI, larger candidate sets remain guarded',
            native_classes=model.classes, model_details_sha256=sha(output/'MODEL_DETAILS.json')))
        del baseline, result
        space = 'SAPIENS2_DOME29_PRED' if model.classes == 29 else 'CIHP_GT_AND_NATIVE_PRED'
        protocol = load_spec(W/config['protocol'])
        gtroot = W/config['GT_binding_root']
        checked(rel(gtroot/'BINDINGS.jsonl'), config['GT_binding_manifest_sha256'])
        bindings = {b['image_id']: b for b in map(json.loads, (gtroot/'BINDINGS.jsonl').read_text().splitlines())}
        state['status'] = 'VALIDATION_RUNNING'
        save()
        for frame in manifest['frames']:
            guard()
            m, d = frame['member'], frame['detector']
            iid = m['id']
            reused_frame = config['reuse_frames'].get(mid, {}).get(iid)
            if reused_frame:
                verify_reuse(reused_frame)
                score_path = W/reused_frame['score_path']
                if sha(score_path) != reused_frame['score_sha256']:
                    raise ValueError('Parent saved scores changed')
                evaluation = read(score_path)
                accumulate(evaluation, iid, accumulator, part_sums)
                state['completed'] += 1
                state['reused_frames'] = state.get('reused_frames',0)+1
                emit(ledger, event='PARENT_FRAME_REUSED', image_id=iid,
                     parent_packet=reused_frame['packet'], parent_score_sha256=sha(score_path))
                save()
                continue
            state['current_id'] = iid
            if state['completed'] % 100 == 0:
                emit(ledger, event='RESOURCE_SNAPSHOT', observations=telemetry())
                verify_config(cp)
            save()
            before_frame = time.monotonic()
            before_input = time.monotonic()
            image, rgb, extents, scores = load_frame(frame)
            input_seconds = time.monotonic()-before_input
            raw, owned, geometry, observations = [], [], [], []
            for j, opportunity in enumerate(d['opportunities']):
                before_crop = time.monotonic()
                crop, box = detector_crop(rgb, opportunity['bbox'], extents[j], .1)
                path = root/'crops'/(iid+'_%03d.png'%j)
                path.parent.mkdir(exist_ok=True)
                if not path.exists():
                    Image.fromarray(crop).save(path)
                if not np.array_equal(np.asarray(Image.open(path).convert('RGB')), crop):
                    raise ValueError('Shared crop RGB mismatch')
                crop_seconds = time.monotonic()-before_crop
                designated = [opportunity['bbox'][k]-box[k%2] for k in range(4)]
                key = iid+'_%03d'%j
                reference = config['reuse_ROIs'].get(mid, {}).get(key)
                if reference:
                    reused_meta, reused_arrays = verify_reuse(reference)
                    native = reused_arrays['native_crop_mask']
                    candidates = reused_arrays['native_candidate_masks']
                    details = dict(reused_meta['geometry'])
                    details['parent_reuse_reference'] = reference['packet']
                    timing = dict(reused_meta['timing'], origin='PARENT_OBSERVATION',
                                  current_frame_wall_includes_this_forward=False)
                    state['reused_partial_ROIs'] = state.get('reused_partial_ROIs',0)+1
                else:
                    (native, candidates, details), timing = infer(crop, path, designated, 'VAL')
                before_ownership = time.monotonic()
                r, o = place(native, box, extents[j], model.classes)
                ownership_seconds = time.monotonic()-before_ownership
                raw.append(r)
                owned.append(o)
                details.update(opportunity_id=opportunity['id'], crop_xyxy=box,
                               crop_pixel_sha256=pixel_sha(crop), crop_png_sha256=sha(path))
                geometry.append(details)
                before_roi_commit = time.monotonic()
                roi = (W/reference['packet']) if reference else write_packet(output/'roi_packets', iid+'_%03d'%j,
                    dict(native_crop_mask=native, native_candidate_masks=candidates),
                    dict(config_sha256=sha(cp), model_id=mid, input_sha256=m['RGB_sha256'],
                         checkpoint_sha256=spec['checkpoint_sha256'], geometry=details, timing=timing), {})
                read_packet(roi)
                if not reference:
                    bytes_written += sum(p.stat().st_size for p in roi.iterdir() if p.is_file())
                observations.append(dict(opportunity_id=opportunity['id'], crop_prepare_seconds=crop_seconds,
                    association_ownership_seconds=ownership_seconds, measurements=timing,
                    roi_export_commit_readback_seconds=time.monotonic()-before_roi_commit))
            h, w = rgb.shape[:2]
            arrays = dict(native_roi_unowned_semantic_masks=np.asarray(raw,np.uint8).reshape(-1,h,w),
                person_semantic_masks=np.asarray(owned,np.uint8).reshape(-1,h,w),
                person_extents=extents, person_scores=scores,
                bboxes_xyxy=np.asarray([op['bbox'] for op in d['opportunities']],np.float32).reshape(-1,4))
            before_export = time.monotonic()
            packet = write_packet(output/'packets', iid, arrays,
                dict(image_id=iid, model_id=mid, original_wh=m['wh'], route=config['route'], label_space=space,
                     checkpoint_sha256=spec['checkpoint_sha256'], input_sha256=m['RGB_sha256'],
                     config_sha256=sha(cp), protocol_sha256=config['protocol_sha256'],
                     detector_sha256=d['artifact_sha256'], geometry=geometry,
                     model_details_sha256=sha(output/'MODEL_DETAILS.json'), environment_sha256=sha(output/'ENVIRONMENT.json'),
                     confidence_kind='FROZEN_YOLO_DETECTION_NOT_PARSING_CONFIDENCE', GT_used_in_prediction=False), {})
            meta, saved = read_packet(packet)
            export_seconds = time.monotonic()-before_export
            frame_wall = time.monotonic()-before_frame
            bytes_written += sum(p.stat().st_size for p in packet.iterdir() if p.is_file())
            before_scoring = time.monotonic()
            category_path = W/'datasets/CIHP/Validation/Category_ids'/(iid+'.png')
            human_path = W/'datasets/CIHP/Validation/Human_ids'/(iid+'.png')
            checked(rel(category_path), m['GT_sha256']['Category_ids'])
            checked(rel(human_path), m['GT_sha256']['Human_ids'])
            evaluation = evaluate(np.asarray(Image.open(category_path)), np.asarray(Image.open(human_path)),
                                  saved, space, protocol)
            binding = bindings[iid]
            checked(rel(gtroot/(iid+'.npz')), binding['derived_sha256'])
            actual = evaluation['scores']['0.5']['GT_binding']
            for key in ['projected_sha256', 'valid_sha256', 'person_valid_sha256', 'G_loc', 'G_sem_C4', 'persons']:
                if actual[key] != binding[key]:
                    raise ValueError('GT-only eligibility/domain binding differs: '+key)
            accumulator.add(iid, evaluation['scores'])
            accumulator.hist += np.asarray(evaluation['scores']['0.5']['histogram'],np.int64)
            for part in evaluation['parts']:
                target = part_sums[str(part['target'])]
                target['count'] += 1
                target['IoU_sum'] += part['IoU']
                for k in ['TP','FP','FN']:
                    target[k] += part[k]
                target['unmatched'] += int(part['unmatched'])
            scorepath = output/'scores'/(iid+'.json')
            atomic(scorepath, dict(image_id=iid, source_packet_sha256=meta['packet_sha256'], **evaluation))
            emit(ledger, event='FRAME_COMMITTED', image_id=iid, packet_sha256=meta['packet_sha256'],
                score_sha256=sha(scorepath), ROI_count=len(extents), input_decode_and_cache_seconds=input_seconds,
                cached_route_wall_seconds=frame_wall, frame_export_commit_readback_seconds=export_seconds,
                scoring_seconds=time.monotonic()-before_scoring, ROI_timings=observations,
                bytes_written=bytes_written)
            state['completed'] += 1
            state['bytes_written'] = bytes_written
            save()
        verify_config(cp)
        result = accumulator.report()
        actual_ids = {p.name for p in (output/'packets').iterdir() if p.is_dir() and not p.name.startswith('.')}
        actual_ids |= set(config['reuse_frames'].get(mid,{}))
        reused_ROI_count = len(config['reuse_ROIs'].get(mid,{}))
        if actual_ids != set(manifest['expected_ids']) or state['ROI_calls']+reused_ROI_count != config['ROI_count']:
            raise ValueError('Closure exact image/ROI membership mismatch')
        for key, count in config['GT_expected_sums'].items():
            if result['person_metrics']['0.5'][key] != count:
                raise ValueError('Closure GT person denominator mismatch')
        for target, count in config['GT_expected_part_counts'].items():
            if part_sums[target]['count'] != count:
                raise ValueError('Closure GT part denominator mismatch')
        hist = np.asarray(result['histogram'], np.int64)
        denominator = hist.sum(0)+hist.sum(1)
        result['primary']['F1_Dice'] = [2*int(hist[c,c])/int(denominator[c]) if denominator[c] else None for c in range(6)]
        for values in part_sums.values():
            values['mean_part_IoU'] = values['IoU_sum']/values['count'] if values['count'] else None
            union = values['TP']+values['FP']+values['FN']
            values['pooled_IoU'] = values['TP']/union if union else None
        result.update(scope=config['protocol_id'], parts=part_sums,
            source_config_sha256=sha(cp), source_route=config['route'],
            interpretation='CIHP reference Face proxy; mean GT-person-part uses mask matching0.50',
            timing='Cached route diagnostics, transfer/internal API stages may be inclusive')
        atomic(output/'METRICS.json',result)
        assembled = dict(parent_config=config['parent_config'], config_sha256=sha(cp),
                         expected_ids=manifest['expected_ids'],
                         parent_frames=config['reuse_frames'].get(mid,{}),
                         new_packet_root=rel(output/'packets'),
                         effective_implementation='RPR_ROI_EMPTY_OUTPUT_1' if mid=='RPR_CIHP' else 'PARENT_MODEL_BEHAVIOR',
                         accepted_ROIs_by_revision={'PARENT':len(config['reuse_ROIs'].get(mid,{})),
                                                    'CONTINUATION':state['ROI_calls']})
        atomic(output/'ASSEMBLED_INDEX.json', assembled)
        state.update(status='COMPLETE', primary=result['primary'], ended_utc=utc())
        atomic(output/'COMPLETION.json',dict(state, missing=0, duplicate=0, packets=5000,
            metrics_sha256=sha(output/'METRICS.json'), strict_complete=True))
    except BaseException as exc:
        error_kind = 'MODEL_OOM' if 'CUDA out of memory' in str(exc) else 'REQUIRES_RECONCILIATION'
        state.update(status='STOPPED_INCOMPLETE', failed=int(state['ROI_calls']>0),
                     setup_failed=int(state['ROI_calls']==0), invalid=int(isinstance(exc, ValueError)),
                     error_kind=error_kind, error=repr(exc), ended_utc=utc())
        atomic(output/'FAILURE.json',dict(state, traceback=traceback.format_exc(), current_id=state.get('current_id')))
        atomic(output/'COMPLETION.json',dict(state, missing=5000-state['completed'], strict_complete=False))
        raise
    finally:
        state['execution_wall_seconds'] = time.monotonic()-started
        save()
        ledger.close()
