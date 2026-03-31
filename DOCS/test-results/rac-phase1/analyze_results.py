import json, re

# Load test items and batch metadata
with open('DOCS/test-results/rac-phase1/rac_test_items.json', encoding='utf-8') as f:
    all_test_items = json.load(f)

with open('DOCS/test-results/rac-phase1/batches_metadata.json', encoding='utf-8') as f:
    batches_meta = json.load(f)

# Parse all 5 batch responses
all_haiku_results = []
token_usage = []

for batch_num in range(1, 6):
    with open(f'DOCS/test-results/rac-phase1/batch{batch_num}_response.json', encoding='utf-8') as f:
        resp = json.load(f)

    token_usage.append({
        'batch': batch_num,
        'input_tokens': resp['input_tokens'],
        'output_tokens': resp['output_tokens'],
        'total': resp['input_tokens'] + resp['output_tokens']
    })

    # Parse JSON from response (strip markdown code blocks)
    text = resp['response'].strip()
    # Remove ```json ... ``` wrapping
    text = re.sub(r'^```[a-z]*\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'```\s*$', '', text, flags=re.MULTILINE)
    text = text.strip()

    predictions = json.loads(text)
    batch_items = batches_meta[batch_num - 1]['items']

    for pred in predictions:
        pos = pred['item_index'] - 1  # 0-indexed
        item_meta = batch_items[pos]

        all_haiku_results.append({
            'batch': batch_num,
            'position': pred['item_index'],
            'bcipl_index': item_meta['bcipl_index'],
            'raw_text': item_meta['raw_text'],
            'sheet_name': item_meta['sheet_name'],
            'section': item_meta['section'],
            'true_cma_row': item_meta['true_cma_row'],
            'true_cma_field': item_meta['true_cma_field'],
            'group': item_meta['group'],
            'true_in_candidates': item_meta['true_in_candidates'],
            'haiku_cma_row': pred['classified_cma_row'],
            'haiku_cma_field': pred['classified_cma_field'],
            'haiku_confidence': pred['confidence'],
            'haiku_correct': pred['classified_cma_row'] == item_meta['true_cma_row']
        })

print(f'Total results: {len(all_haiku_results)}')

# Group A analysis
group_a = [r for r in all_haiku_results if r['group'] == 'A']
group_b = [r for r in all_haiku_results if r['group'] == 'B']

ga_correct = sum(1 for r in group_a if r['haiku_correct'])
gb_correct = sum(1 for r in group_b if r['haiku_correct'])

print(f'Group A (hard/wrong): {ga_correct}/{len(group_a)} = {ga_correct/len(group_a)*100:.1f}%')
print(f'Group B (sanity check): {gb_correct}/{len(group_b)} = {gb_correct/len(group_b)*100:.1f}%')

print()
print('Token usage per batch:')
total_in = total_out = 0
for t in token_usage:
    print(f'  Batch {t["batch"]}: in={t["input_tokens"]}, out={t["output_tokens"]}, total={t["total"]}')
    total_in += t['input_tokens']
    total_out += t['output_tokens']
print(f'  TOTAL: in={total_in}, out={total_out}, total={total_in+total_out}')

print()
print('Group A item-by-item:')
for r in group_a:
    status = 'OK' if r['haiku_correct'] else 'WRONG'
    print(f'  [{status}] {r["raw_text"][:40]:40s} true:{r["true_cma_row"]:3d} haiku:{r["haiku_cma_row"]:3d} conf:{r["haiku_confidence"]:.2f}')

print()
print('Group B item-by-item:')
for r in group_b:
    status = 'OK' if r['haiku_correct'] else 'WRONG'
    print(f'  [{status}] {r["raw_text"][:40]:40s} true:{r["true_cma_row"]:3d} haiku:{r["haiku_cma_row"]:3d} conf:{r["haiku_confidence"]:.2f}')

# Save full results
with open('DOCS/test-results/rac-phase1/rac_haiku_results.json', 'w', encoding='utf-8') as f:
    json.dump({
        'metadata': {
            'method': 'RAC (Retrieve-and-Classify)',
            'classifier': 'claude-haiku-4-5 via OpenRouter',
            'retrieval': 'sentence-transformers all-MiniLM-L6-v2',
            'database': 'SR Papers (216 items)',
            'test_set': 'BCIPL (448 items)',
            'test_sample': '50 items (30 Group A + 20 Group B)',
            'haiku_calls': 5,
            'items_per_call': 10
        },
        'group_a_summary': {
            'description': 'Items embedding got WRONG (hard cases)',
            'total': len(group_a),
            'haiku_correct': ga_correct,
            'accuracy_pct': round(ga_correct/len(group_a)*100, 1)
        },
        'group_b_summary': {
            'description': 'Items embedding got RIGHT (sanity check)',
            'total': len(group_b),
            'haiku_correct': gb_correct,
            'accuracy_pct': round(gb_correct/len(group_b)*100, 1)
        },
        'token_usage': token_usage,
        'total_tokens': {'input': total_in, 'output': total_out, 'total': total_in+total_out},
        'all_results': all_haiku_results
    }, f, indent=2, ensure_ascii=False)

print()
print('Saved rac_haiku_results.json')
