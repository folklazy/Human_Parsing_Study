"""Per-system/per-image scoring bindings; no real-data acceptance is implied."""
from .policy import digest
import copy


def validate_context_registry(config):
    registry = config['scoring_contexts']
    population = config.get('scoring_population')
    if not isinstance(population, list) or not population:
        raise ValueError('Context registry requires an accepted predeclared scoring population')
    images = []
    for frame in population:
        image = frame.get('image_id')
        if not isinstance(image, str) or not image or image in images:
            raise ValueError('Scoring population requires unique image IDs')
        if any(type(frame.get(k)) is not int or frame[k] < 0 for k in ['G_loc', 'G_sem']) or frame['G_sem'] > frame['G_loc']:
            raise ValueError('Invalid predeclared GT denominators')
        images.append(image)
    systems = config['first_cohort']['models']
    if not isinstance(registry, dict) or not registry or set(registry) != set(systems):
        raise ValueError('Scoring context systems must equal the predeclared cohort')
    shared = None
    input_bindings, image_domains = {}, {}
    expected = {frame['image_id']: frame for frame in population}
    for system, contexts in registry.items():
        if not isinstance(contexts, dict) or set(contexts) != set(images):
            raise ValueError('Every system requires contexts for the complete population')
        model = None
        for image, context in contexts.items():
            if context.get('status') != 'ACCEPTED' or context.get('input_binding', {}).get('image_id') != image:
                raise ValueError('Accepted context must bind the declared input image ID')
            # The mapping digest identifies the complete bundle, which may contain
            # distinct native projections. Only the domain POLICY is comparison-wide;
            # GT/mask provenance and denominators are specific to each image.
            common = {key: context[key] for key in ['mapping_sha256', 'target_support_policy',
                                                    'failure_policy', 'evaluation_bbox_source', 'threshold']}
            common['domain'] = {k: v for k, v in context['domain'].items() if k != 'image_binding'}
            if shared is None:
                shared = common
            elif common != shared:
                raise ValueError('A comparison must share mapping, GT domain and evaluation policy')
            if context['threshold'] != config['evaluation']['threshold'] or context['failure_policy'] != config['primary_reporting_policy']['main_score']:
                raise ValueError('Scoring context conflicts with executable evaluation/reporting policy')
            if config.get('cohort_policy', {}).get('support_binding_required') and context.get('require_checkpoint_specific_support') is not True:
                raise ValueError('Every context requires checkpoint-specific support evidence')
            binding = context['model_binding']
            if model is None:
                model = binding
            elif binding != model:
                raise ValueError('One system cannot change checkpoint/config across images')
            if image in input_bindings and context['input_binding'] != input_bindings[image]:
                raise ValueError('Systems must use the same verified source input for each image')
            input_bindings[image] = context['input_binding']
            domain = context['domain'].get('image_binding')
            if config.get('first_cohort', {}).get('require_per_image_GT_domain_binding') and not isinstance(domain, dict):
                raise ValueError('Per-image GT/domain binding is required for this cohort')
            if domain is not None:
                if domain.get('image_id') != image or any(domain.get(k) != expected[image][k] for k in ['G_loc', 'G_sem']):
                    raise ValueError('GT/domain binding differs from the predeclared image population')
                recipe = domain.get('GT_domain_recipe_sha256')
                if not isinstance(recipe, str) or len(recipe) != 64 or any(c not in '0123456789abcdef' for c in recipe):
                    raise ValueError('Explicit GT/domain recipe fingerprint required')
            if image in image_domains and domain != image_domains[image]:
                raise ValueError('The same image must have the same GT/domain binding across systems')
            image_domains[image] = domain
    return True


def select_context(config, system_id=None, image_id=None, *, matching_view='primary'):
    if config.get('scoring_contexts') is not None:
        try:
            context = config['scoring_contexts'][system_id][image_id]
        except (KeyError, TypeError) as exc:
            raise ValueError('An exact registered system_id/image_id is required for scoring') from exc
    else:
        context = config.get('scoring_context')
    if context is None:
        raise ValueError('No accepted scoring context: production scoring remains disabled')
    if matching_view == 'primary':
        return context
    if matching_view != 'secondary':
        raise ValueError('Only configured primary/secondary matching views are supported')
    result = copy.deepcopy(context)
    result['threshold'] = config['evaluation']['secondary_threshold']
    return result


def check_report_binding(config, population, frames, *, matching_view='primary'):
    registered = config.get('scoring_contexts') is not None
    if registered and digest(population) != digest(config['scoring_population']):
        raise ValueError('Report population differs from accepted predeclared scoring population')
    for frame in frames:
        score = frame.get('score_result')
        if not score or not score.get('score_eligible'):
            continue
        if not registered and (len(config['first_cohort']['models']) != 1 or len(population) != 1):
            raise ValueError('Multiple systems/images require accepted, bound context registry')
        try:
            context = select_context(config, frame['system_id'], frame['image_id'], matching_view=matching_view)
        except ValueError as exc:
            raise ValueError('Primary reporting requires an accepted, bound scoring result') from exc
        if score.get('scoring_context_sha256') != digest(context):
            raise ValueError('Primary reporting requires an accepted, bound scoring result')
        if registered and (score.get('system_id'), score.get('image_id')) != (frame['system_id'], frame['image_id']):
            raise ValueError('Score identity differs from its system/image report row')
