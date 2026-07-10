from pathlib import Path
from log_loader import load_log
from frequent_sets import FrequentSetMiner
from candidates import CandidateGenerator
from evaluators import ConstraintEvaluator
from pruning import ConstraintPruner
from reduction import ConstraintReducer
import yaml


def save_yaml(document, path):
    with open(path, "w", encoding="utf-8") as file:
        yaml.safe_dump(document, file, sort_keys=False, allow_unicode=True)


def sort_keys(constraint):
    return constraint["template"], constraint["a"], constraint["b"]


def sort_constraints(constraints):
    keys = {}
    sorted_constraints = []
    for constraint in constraints:
        keys[sort_keys(constraint)] = constraint
    for key in sorted(keys):
        sorted_constraints.append(keys[key])

    return sorted_constraints


def activities_in_model(constraints):
    model_activities = set()
    for constraint in constraints:
        model_activities.add(constraint["a"])
        if constraint["b"] is not None:
            model_activities.add(constraint["b"])
    return sorted(model_activities)


def build_model(process_name, min_support, num_traces, num_candidates, pruned_cons, reduced_cons):
    constraints = sort_constraints(reduced_cons)
    return {
        "process": process_name,
        "source_log": f"xes_logs/{process_name}.xes",
        "templates": list(TEMPLATES),
        "thresholds": {
            "support": min_support,
            "alpha": 0,
            "apriori_support": 0
        },
        "log_info": {
            "number_of_traces": num_traces,
            "number_of_candidates": num_candidates,
            "candidates_after_pruning": len(pruned_cons),
            "number_of_constraints": len(constraints),
        },
        "reduction": {
            "number_of_input__constraints": len(pruned_cons),
            "reduced_constraints": len(pruned_cons) - len(constraints),
            "final_constraints": len(constraints),
        },
        "declare_model": {
            "activities": activities_in_model(constraints),
            "constraints": constraints,
        },
    }


if __name__ == "__main__":
    TEMPLATES = ["existence", "absence", "init", "responded_existence", "coexistence", "exclusive_choice", "response",
                 "precedence", "succession", "alternate_response", "alternate_precedence", "alternate_succession",
                 "chain_response", "chain_precedence", "chain_succession"]

    ROOT = Path(__file__).resolve().parent.parent
    input_dir = ROOT / "log_files" / "transformed_logs"
    output_dir = ROOT / "declare_outputs" / "reimplementation_outputs"

    processes = ["action_attack", "action_move", "get_input", "gridmaster", "manipulate_grid", "player_turn"]
    supports = [5, 20, 50, 80, 100]

    for process in processes:
        models_dir = output_dir / process
        # models_dir.mkdir(parents=True, exist_ok=True)

        traces = load_log(input_dir / f"{process}.xes")
        activities = sorted({activity for trace in traces for activity in trace})

        frequent_sets = FrequentSetMiner(0.0).generate_sets(traces)
        save_yaml({"number_of_sets": len(frequent_sets), "frequent_sets": frequent_sets}, models_dir / "frequent_sets.yaml")

        candidates = CandidateGenerator(TEMPLATES).generate_candidates(frequent_sets, activities)
        save_yaml({"number_of_candidates": len(candidates), "candidates": candidates}, models_dir / "candidates.yaml")

        evaluated = ConstraintEvaluator(traces).evaluate_candidates(candidates)
        save_yaml({"number_of_evaluations": len(evaluated), "constraints": evaluated}, models_dir / "evaluated.yaml")

        for support in supports:
            support_ratio = support / 100
            pruned = ConstraintPruner(support_ratio, 0).prune_constraints(evaluated)
            reduced = ConstraintReducer(TEMPLATES).reduce(pruned)
            model = build_model(process, support_ratio, len(traces), len(candidates), pruned, reduced)
            save_yaml(model, models_dir / f"model_supp{support}_alpha0.yaml")

        print(process, ": Done")
