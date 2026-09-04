import json
import sys
import os

from engine.engine import rank, _card_applies
from engine.models import ContextFrame, RankedCard, SignalValue

def run_evaluation():
    try:
        with open('eval/golden_set.json', 'r') as f:
            scenarios = json.load(f)
    except FileNotFoundError:
        print("Golden dataset missing. Run build_golden.py first.")
        sys.exit(1)

    matches_engine = 0
    matches_baseline_a = 0
    matches_baseline_b = 0

    mismatches = {
        "aqi_dominance": [],
        "cold_start": [],
        "persona_differentiation": [],
        "urgency_interactions": [],
        "safety_overrides": [],
        "missing_data": []
    }

    with open('eval/detailed_report.txt', 'w', encoding='utf-8') as rep:
        for s in scenarios:
            persona = s['persona']
            cat = s.get('type', 'general')
            expected_top = s['expected_top_card']

            data = s['context']
            data['temp_c'] = SignalValue(**data['temp_c'])
            data['aqi'] = SignalValue(**data['aqi'])
            data['precip_prob_pct'] = SignalValue(**data['precip_prob_pct'])
            data['uv'] = SignalValue(**data['uv'])
            data['wind_kmh'] = SignalValue(**data['wind_kmh'])
            if 'visibility_km' in data:
                data['visibility_km'] = SignalValue(**data['visibility_km'])
            if 'soil_moisture_pct' in data:
                data['soil_moisture_pct'] = SignalValue(**data['soil_moisture_pct'])
            if 'wave_height_m' in data:
                data['wave_height_m'] = SignalValue(**data['wave_height_m'])
            if 'water_temp_c' in data:
                data['water_temp_c'] = SignalValue(**data['water_temp_c'])
            if 'destinations' in data:
                from engine.models import DestinationContext
                for d in data['destinations']:
                    if 'temp_c' in d and isinstance(d['temp_c'], dict):
                        d['temp_c'] = SignalValue(**d['temp_c'])
                data['destinations'] = [DestinationContext(**d) for d in data['destinations']]
                
            cf = ContextFrame(**data)

            # True Engine Rank
            try:
                out = rank(cf)
                ranked = out.override_warnings + out.ranked_cards if hasattr(out, "ranked_cards") else out
            except Exception as e:
                rep.write(f"[{s['id']}] FAILED engine.rank: {e}\n")
                continue

            true_top = ranked[0].card_id if ranked else None

            # Baseline A: default_general execution
            data_a = data.copy()
            data_a['personas'] = ['default_general']
            cf_a = ContextFrame(**data_a)
            out_a = rank(cf_a)
            ranked_a = out_a.override_warnings + out_a.ranked_cards if hasattr(out_a, "ranked_cards") else out_a
            top_a = ranked_a[0].card_id if ranked_a else None

            # Baseline B: Static Persona Order
            baseline_b_ranks = []
            from engine.scoring import PERSONA_WEIGHT
            from engine.cards import CARD_DEFINITIONS
            from engine.priority import _HARD_ALERT_URGENCY
            for card_id, defn in CARD_DEFINITIONS.items():
                if not _card_applies(card_id, cf): continue
                w = PERSONA_WEIGHT.get((card_id, persona), PERSONA_WEIGHT.get((card_id, "default_general"), 0.2))
                baseline_b_ranks.append((card_id, w))

            alert_p0 = None
            if cf.warnings:
                for w in cf.warnings:
                    severity = w.get("severity") or w.get("type", "")
                    if _HARD_ALERT_URGENCY.get(severity, 0) == 1.0:
                        alert_p0 = "severe_warning"
                        break

            if alert_p0:
                top_b = alert_p0
            else:
                baseline_b_ranks.sort(key=lambda x: x[1], reverse=True)
                top_b = baseline_b_ranks[0][0] if baseline_b_ranks else None

            if true_top == expected_top: matches_engine += 1
            else:
                if "aqi" in true_top and "aqi" not in expected_top: mismatches["aqi_dominance"].append(s['id'])
                elif cat == "cold_start": mismatches["cold_start"].append(s['id'])
                elif cat == "normal": mismatches["persona_differentiation"].append(s['id'])
                elif cat == "conflict" or cat == "thresholds": mismatches["urgency_interactions"].append(s['id'])
                elif cat == "p0_override": mismatches["safety_overrides"].append(s['id'])
                elif cat == "missing_data": mismatches["missing_data"].append(s['id'])

            if top_a == expected_top: matches_baseline_a += 1
            if top_b == expected_top: matches_baseline_b += 1

            rep.write(f"[{s['id']}] Persona: {persona} \n")
            rep.write(f"   Rationale: {s.get('rationale', 'none')}\n")
            rep.write(f"   Expected: {expected_top}\n")
            rep.write(f"   Engine:   {true_top} {'(MATCH)' if true_top == expected_top else '(MISMATCH)'}\n")
            rep.write(f"   Bsl A:    {top_a}\n")
            rep.write(f"   Bsl B:    {top_b}\n\n")

        rep.write("====================\n")
        rep.write("EVALUATION RESULTS\n")
        rep.write(f"Total Scenarios:       {len(scenarios)}\n")
        rep.write(f"Engine Match Rate:     {matches_engine}/{len(scenarios)} ({(matches_engine/len(scenarios))*100:.1f}%)\n")
        rep.write(f"Baseline A (Generic):  {matches_baseline_a}/{len(scenarios)} ({(matches_baseline_a/len(scenarios))*100:.1f}%)\n")
        rep.write(f"Baseline B (Static):   {matches_baseline_b}/{len(scenarios)} ({(matches_baseline_b/len(scenarios))*100:.1f}%)\n\n")

        rep.write("MISMATCH CATEGORIES (Engine vs Golden):\n")
        for k, v in mismatches.items():
            rep.write(f"  {k}: {len(v)} ({', '.join(v) if v else 'None'})\n")

        if matches_engine == len(scenarios):
             rep.write("\nVERDICT: GO. The engine outperforms naive baselines deterministically.")
        elif matches_engine > matches_baseline_a and matches_engine > matches_baseline_b:
             rep.write("\nVERDICT: CONDITIONAL GO (RECALIBRATE). The engine outperforms naive logic, but specific weights skew edge-cases.")
        else:
             rep.write("\nVERDICT: PIVOT. The baseline logic equalled or defeated dynamic scoring. Weights/Urgency models fail.")

if __name__ == '__main__':
    run_evaluation()
