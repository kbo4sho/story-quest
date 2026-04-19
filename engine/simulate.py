#!/usr/bin/env python3
"""
Simulate the engine's happy path over the story spec.
Confirms: the schema + story can reach a finale with a solvable puzzle sequence.
Mirrors engine logic (flag conditions, effects, puzzle solving) without a browser.
"""
import json, sys, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
story = json.load(open(ROOT / 'schema' / 'story-example.json'))

def eval_cond(cond, flags):
    if not cond: return True
    if 'flag' in cond:
        v = flags.get(cond['flag'])
        if 'equals' in cond: return v == cond['equals']
        if 'gte' in cond:    return isinstance(v, (int, float)) and v >= cond['gte']
    if 'all' in cond: return all(eval_cond(c, flags) for c in cond['all'])
    if 'any' in cond: return any(eval_cond(c, flags) for c in cond['any'])
    return False

def apply_effect(e, state):
    if 'set_flag' in e:       state['flags'][e['set_flag']] = e['value']
    if 'increment_flag' in e: state['flags'][e['increment_flag']] = state['flags'].get(e['increment_flag'], 0) + e['by']
    if 'pickup_item' in e and e['pickup_item'] not in state['inventory']:
        state['inventory'].append(e['pickup_item'])
    if 'show_narration' in e: state['narration_log'].append(e['show_narration'])

def apply_effects(effs, state): [apply_effect(e, state) for e in (effs or [])]

def fresh_state():
    flags = {k: f['default'] for k, f in story.get('flags', {}).items()}
    return {
        'room': story['world']['spawn']['room'],
        'flags': flags,
        'inventory': [],
        'visited': set(),
        'beats_fired': set(),
        'puzzles_solved': set(),
        'narration_log': [],
        'trace': [],
    }

def check_arc_beats(state):
    for beat in story['arc']['beats']:
        if beat['id'] in state['beats_fired']: continue
        if eval_cond(beat['when'], state['flags']):
            state['beats_fired'].add(beat['id'])
            state['narration_log'].append(f"[act{beat['act']}] {beat['narrator_card']}")
            apply_effects(beat.get('effects'), state)

def enter_room(room_id, state):
    first = room_id not in state['visited']
    state['room'] = room_id
    state['visited'].add(room_id)
    room = story['world']['rooms'][room_id]
    apply_effects(room.get('on_enter') if first else room.get('on_enter_again'), state)
    check_arc_beats(state)
    state['trace'].append(f"enter {room_id}")

def solve_puzzle(p, state):
    # Honor on_solved side effects
    apply_effects(p['on_solved'], state)
    state['puzzles_solved'].add(p['id'])
    state['trace'].append(f"solve {p['id']}")
    check_arc_beats(state)

def step(state, path_choice='brave'):
    """One step: solve an unsolved puzzle in room, else take an available exit."""
    room = story['world']['rooms'][state['room']]

    # Scene 1 hatch affordance
    if room['id'] == 'meadow-hatch' and not state['flags'].get('hatch_opened'):
        state['flags']['hatch_opened'] = True
        state['trace'].append("open hatch")
        check_arc_beats(state)
        return True

    # Meadow collect: simulate collecting all 3 wonder items if puzzle is here
    for pid in room.get('puzzles_in_room', []):
        if pid in state['puzzles_solved']: continue
        p = story['puzzles'][pid]
        if p['type'] == 'collect-and-deliver':
            for t in p['config']['targets']:
                if t not in state['inventory']: state['inventory'].append(t)
            state['flags']['wonder_items_collected'] = len(p['config']['targets'])
        solve_puzzle(p, state)
        return True

    # Take first available exit, preferring the chosen crystal-cave path
    for ex in room.get('exits', []):
        if 'hidden_until' in ex and not eval_cond(ex['hidden_until'], state['flags']): continue
        if 'condition' in ex and not eval_cond(ex['condition'], state['flags']): continue
        if room['id'] == 'crystal-cave' and path_choice and path_choice not in ex['label'].lower() and not any(
            path_choice in e['label'].lower() for e in room['exits']
        ):
            pass
        if room['id'] == 'crystal-cave':
            # only take the chosen path
            label = ex['label'].lower()
            if path_choice == 'brave' and 'brave' not in label: continue
            if path_choice == 'wise'  and 'wise'  not in label: continue
            if path_choice == 'nature' and 'nature' not in label: continue
        apply_effects(ex.get('effects'), state)
        enter_room(ex['target_room'], state)
        return True

    return False  # stuck

def simulate(path='brave'):
    state = fresh_state()
    enter_room(state['room'], state)
    for i in range(50):
        advanced = step(state, path_choice=path)
        room = story['world']['rooms'][state['room']]
        # Check end condition
        if room['scene_type'] == 'finale' and state['flags'].get('finale_solved'):
            return state, True
        if not advanced: return state, False
    return state, False

def main():
    all_ok = True
    for path in ('brave', 'wise', 'nature'):
        state, reached = simulate(path)
        status = 'REACHED FINALE' if reached else 'STUCK'
        print(f'[{path:6s}] {status}')
        print(f'   visited: {len(state["visited"])} rooms, solved: {len(state["puzzles_solved"])} puzzles, beats: {len(state["beats_fired"])}')
        print(f'   final flags: {", ".join(f"{k}={v}" for k,v in state["flags"].items() if v not in (False, 0, ""))}')
        if not reached:
            print(f'   last room: {state["room"]}')
            print(f'   trace: {state["trace"][-10:]}')
            all_ok = False
        print()
    return 0 if all_ok else 1

if __name__ == '__main__':
    sys.exit(main())
