from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from skills.skill_manager import list_skills, search_skills, load_constitution_for_prompt

required = [
    'authority-matrix','source-of-truth','infrastructure-map','account-prop-registry',
    'incident-playbooks','change-management','trading-safety-constitution','daily-ceo-routine',
    'memory-policy','communication-personality','personal-assistant-ops','boss-learning-mode',
    'confidence-unknown-policy','cross-system-reasoning','disaster-recovery','cost-optimizer',
    'security-operations','goal-strategy-memory'
]
names = {s['name'] for s in list_skills()}
missing = [x for x in required if x not in names]
print('SKILLS_TOTAL', len(names))
print('MISSING', missing)
print('CONSTITUTION', 'JARVIS Constitution v1' in load_constitution_for_prompt())
queries = {
    'authority permission mutation': 'authority-matrix',
    'current source of truth': 'source-of-truth',
    'signal no trade trace chain': 'cross-system-reasoning',
    'daily CEO health routine': 'daily-ceo-routine',
    'api cost credits polling': 'cost-optimizer',
    'secret token security': 'security-operations',
    'prop account registry rules': 'account-prop-registry',
}
for query, wanted in queries.items():
    result = [x['name'] for x in search_skills(query, 5)]
    print('SEARCH', query, '=>', result, 'PASS', wanted in result)
seed = json.load(open(ROOT / 'knowledge' / 'memory_seed.json', encoding='utf-8'))
print('SEED_CATEGORIES', sorted(seed))