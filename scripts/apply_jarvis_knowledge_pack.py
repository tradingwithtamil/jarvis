from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from memory.memory_manager import update_memory, memory_stats
from skills.skill_manager import list_skills, load_constitution_for_prompt

seed_path = ROOT / 'knowledge' / 'memory_seed.json'
seed = json.loads(seed_path.read_text(encoding='utf-8'))
update_memory(seed)

skills = list_skills()
constitution = load_constitution_for_prompt()
required = {
    'authority-matrix', 'source-of-truth', 'infrastructure-map',
    'account-prop-registry', 'incident-playbooks', 'change-management',
    'trading-safety-constitution', 'daily-ceo-routine', 'memory-policy',
    'communication-personality', 'personal-assistant-ops', 'boss-learning-mode',
    'confidence-unknown-policy', 'cross-system-reasoning', 'disaster-recovery',
    'cost-optimizer', 'security-operations', 'goal-strategy-memory',
}
names = {s['name'] for s in skills}
missing = sorted(required - names)
if missing:
    raise SystemExit(f'missing skills: {missing}')
if 'JARVIS Constitution v1' not in constitution:
    raise SystemExit('constitution not loaded')

print(json.dumps({
    'status': 'PASS',
    'skills_total': len(skills),
    'governance_required': len(required),
    'governance_missing': missing,
    'constitution_chars': len(constitution),
    'memory': memory_stats(),
}, indent=2))
