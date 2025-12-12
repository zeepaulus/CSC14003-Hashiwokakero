import time
import tracemalloc
from typing import List, Dict, Tuple, Type
from concurrent.futures import ProcessPoolExecutor, TimeoutError as FuturesTimeoutError
from utils import read_input

Grid = List[List[int]]
DEFAULT_TIMEOUT = 5


def _get_solver_classes():
    from solvers import PySatSolver, AStarSolver, BacktrackingSolver, BruteForceCNFSolver
    return {"PySatSolver": PySatSolver, "AStarSolver": AStarSolver,
            "BacktrackingSolver": BacktrackingSolver, "BruteForceCNFSolver": BruteForceCNFSolver}


def _get_default_solvers():
    from solvers import PySatSolver, AStarSolver, BacktrackingSolver, BruteForceCNFSolver
    return [("PySAT", PySatSolver), ("AStar", AStarSolver),
            ("Backtracking", BacktrackingSolver), ("BruteForce", BruteForceCNFSolver)]


def _solve_task(solver_cls_name: str, grid: Grid):
    solvers_map = _get_solver_classes()
    solver_cls = solvers_map[solver_cls_name]
    
    tracemalloc.start()
    t0 = time.perf_counter()
    metrics, solution, islands = {}, None, {}
    
    try:
        solver = solver_cls(grid)
        solution, islands, _ = solver.solve()
        success = solution is not None
        
        if solver_cls_name == "AStarSolver":
            metrics["expanded"] = getattr(solver, 'expanded_nodes', 0)
            metrics["generated"] = getattr(solver, 'generated_nodes', 0)
        elif solver_cls_name == "BacktrackingSolver":
            metrics["calls"] = getattr(solver, 'recursive_calls', 0)
            metrics["backtracks"] = getattr(solver, 'backtracks', 0)
        elif solver_cls_name == "BruteForceCNFSolver":
            metrics["iterations"] = getattr(solver, 'iterations', 0)
        elif solver_cls_name == "PySatSolver":
            metrics["conflicts"] = getattr(solver, 'conflicts', 0)
            metrics["decisions"] = getattr(solver, 'decisions', 0)
    except Exception as e:
        success = False
        metrics["error"] = str(e)
    
    elapsed = time.perf_counter() - t0
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return elapsed, peak / (1024 * 1024), success, metrics, solution, islands


def run_and_profile(solver_cls: Type, grid: Grid, timeout: float = DEFAULT_TIMEOUT):
    solver_cls_name = solver_cls.__name__
    executor = ProcessPoolExecutor(max_workers=1)
    try:
        future = executor.submit(_solve_task, solver_cls_name, grid)
        try:
            return future.result(timeout=timeout) + (False,)
        except FuturesTimeoutError:
            future.cancel()
            return timeout, 0, False, {}, None, {}, True
        except Exception:
            return 0, 0, False, {}, None, {}, False
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


def run_benchmark(indices: List[int], solver_subset: List[Tuple[str, Type]] = None, 
                  timeout: float = DEFAULT_TIMEOUT) -> Dict:
    solvers = solver_subset if solver_subset else _get_default_solvers()
    grids = {}
    for idx in indices:
        try:
            grids[idx] = read_input(f"Inputs/input-{idx:02d}.txt")
        except FileNotFoundError:
            grids[idx] = None

    results = {"indices": indices, "solvers": {}, "grids": grids, "timeout": timeout}

    for name, cls in solvers:
        times, mems, timeouts_list, all_metrics, solutions, islands_list = [], [], [], [], [], []
        
        for idx in indices:
            grid = grids.get(idx)
            if grid is None:
                times.append(0); mems.append(0); timeouts_list.append(False)
                all_metrics.append({}); solutions.append(None); islands_list.append({})
                continue
            
            elapsed, mem, success, metrics, solution, islands, timed_out = run_and_profile(cls, grid, timeout)
            
            if timed_out:
                times.append(-1); mems.append(-1); timeouts_list.append(True)
                all_metrics.append({}); solutions.append(None); islands_list.append({})
            elif not success:
                times.append(0); mems.append(0); timeouts_list.append(False)
                all_metrics.append(metrics); solutions.append(None); islands_list.append({})
            else:
                times.append(elapsed * 1000); mems.append(mem); timeouts_list.append(False)
                all_metrics.append(metrics); solutions.append(solution); islands_list.append(islands)
        
        results["solvers"][name] = {
            "times": times, "mems": mems, "timeouts": timeouts_list,
            "metrics": all_metrics, "solutions": solutions, "islands": islands_list
        }
    
    return results
