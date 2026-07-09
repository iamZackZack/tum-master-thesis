from pathlib import Path
from event_log import read_xes
from miner import Miner
from dcr_graph import DcrGraph
from optimizations import (
    TransitiveReduction,
    PredecessorSuccessors,
    PredecessorExclusions,
    MutualExclusions,
    ExclusionOptimization,
)


def optimize_graph(graph, log):
    activities = set(graph.activities)
    optimized = DcrGraph(activities)

    reduction = TransitiveReduction()

    reduced_conditions = reduction.transitive_reduce(graph.conditions)
    optimized.conditions = reduced_conditions

    reduced_responses = reduction.transitive_reduce(graph.responses)
    optimized.responses = reduced_responses

    optimized.includes = set(graph.includes)

    predecessors_successors = PredecessorSuccessors(log, activities)

    self_excluding = set()
    for source, target in graph.excludes:
        if source == target:
            self_excluding.add(source)

    excludes = set(graph.excludes)

    predecessor_excludes = PredecessorExclusions().find(activities, predecessors_successors, self_excluding)
    mutual_excludes = MutualExclusions().find(activities, predecessors_successors)
    excludes.update(predecessor_excludes)
    excludes.update(mutual_excludes)

    optimized.excludes = ExclusionOptimization().prune(excludes, predecessors_successors)

    return optimized


if __name__ == "__main__":
    ROOT = Path(__file__).resolve().parent.parent
    input_dir = ROOT / "log_files" / "transformed_logs"
    output_dir = ROOT / "parnek_outputs" / "reimplementation_outputs"

    processes = ["action_move", "action_attack", "get_input", "gridmaster", "manipulate_grid", "player_turn"]

    for process in processes:
        log_path = input_dir / f"{process}.xes"
        graph_path = output_dir / process / f"dcr.yaml"
        optimized_path = output_dir / process / f"optimized.yaml"
        (output_dir / process).mkdir(parents=True, exist_ok=True)

        log = read_xes(log_path)
        graph = Miner().mine(log)
        graph.save(graph_path)

        optimized_graph = optimize_graph(graph, log)
        optimized_graph.save(optimized_path)

        print(process, ": Done")
