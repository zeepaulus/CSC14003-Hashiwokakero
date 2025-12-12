from typing import List, Dict
from utils import draw_solution

METRICS = {"PySAT": "conflicts", "AStar": "expanded", "Backtracking": "calls", "BruteForce": "iterations"}


def get_grid_lines(data: dict, i: int, grid, name: str) -> List[str]:
    sol = data["solvers"][name]["solutions"][i]
    islands = data["solvers"][name]["islands"][i]
    timeout = data["solvers"][name]["timeouts"][i]
    lines = [f"[{name}]"]
    if sol:
        char_grid = draw_solution(grid, islands, sol)
        for row in char_grid:
            lines.append(" ".join(f"{c:>2}" for c in row))
    else:
        lines.append("TIMEOUT" if timeout else "FAILED")
    return lines


def print_two_grids(lines1: List[str], lines2: List[str], gap: int = 6) -> None:
    max_len = max(len(lines1), len(lines2))
    width1 = max(len(l) for l in lines1) if lines1 else 0
    for j in range(max_len):
        left = lines1[j] if j < len(lines1) else ""
        right = lines2[j] if j < len(lines2) else ""
        print(f"{left:<{width1}}{' '*gap}{right}")
    print()


def print_input_result(data: dict, i: int, idx: int, solver_names: List[str]) -> None:
    grid = data["grids"].get(idx)
    if not grid:
        return
    
    print(f"\n{'='*70}")
    print(f"  Input {idx} ({len(grid)}x{len(grid[0])})")
    print(f"{'='*70}")
    
    grids = {name: get_grid_lines(data, i, grid, name) for name in solver_names}
    
    # 2x2 layout
    if len(solver_names) >= 2:
        print_two_grids(grids.get(solver_names[0], []), grids.get(solver_names[1], []))
    if len(solver_names) >= 4:
        print_two_grids(grids.get(solver_names[2], []), grids.get(solver_names[3], []))
    
    print(f"{'Solver':<15} {'Time(ms)':<12} {'Mem(MB)':<12} {'Metric':<15}")
    print("-" * 54)
    for name in solver_names:
        res = data["solvers"][name]
        t, m, to = res["times"][i], res["mems"][i], res["timeouts"][i]
        met = res["metrics"][i].get(METRICS.get(name, ""), 0)
        if to:
            print(f"{name:<15} {'TIMEOUT':<12} {'-':<12} {'-':<15}")
        elif res["solutions"][i] is None:
            print(f"{name:<15} {'FAILED':<12} {'-':<12} {'-':<15}")
        else:
            print(f"{name:<15} {t:<12.2f} {m:<12.2f} {met:<15,}")


def print_benchmark_table(all_data: Dict[str, dict], solver_names: List[str]) -> None:
    print(f"\n{'='*80}")
    print(f"  BENCHMARK SUMMARY")
    print(f"{'='*80}")
    print(f"{'Level':<10} {'Input':<8} {'Size':<8} {'Solver':<15} {'Time(ms)':<12} {'Mem(MB)':<10} {'Metric':<12}")
    print("-" * 80)
    
    for label, data in all_data.items():
        for i, idx in enumerate(data["indices"]):
            grid = data["grids"].get(idx)
            size = f"{len(grid)}x{len(grid[0])}" if grid else "-"
            for j, name in enumerate(solver_names):
                res = data["solvers"][name]
                t, m, to = res["times"][i], res["mems"][i], res["timeouts"][i]
                met = res["metrics"][i].get(METRICS.get(name, ""), 0)
                
                disp_label = label if j == 0 else ""
                disp_idx = str(idx) if j == 0 else ""
                disp_size = size if j == 0 else ""
                
                if to:
                    print(f"{disp_label:<10} {disp_idx:<8} {disp_size:<8} {name:<15} {'TIMEOUT':<12} {'-':<10} {'-':<12}")
                elif res["solutions"][i] is None:
                    print(f"{disp_label:<10} {disp_idx:<8} {disp_size:<8} {name:<15} {'FAILED':<12} {'-':<10} {'-':<12}")
                else:
                    print(f"{disp_label:<10} {disp_idx:<8} {disp_size:<8} {name:<15} {t:<12.2f} {m:<10.2f} {met:<12,}")
            print("-" * 80)
