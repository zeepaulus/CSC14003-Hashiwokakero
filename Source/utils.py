import os
from typing import List, Dict, Tuple

Grid = List[List[int]]
SolutionDict = Dict[Tuple[int, int], int]

def read_input(file_path: str) -> Grid:
    grid = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            parts = [p.strip() for p in line.split(",")]
            grid.append([int(x) for x in parts])
    return grid

def draw_solution(grid: Grid, islands: Dict[int, Tuple[int, int, int]], solution: SolutionDict) -> List[List[str]]:
    rows, cols = len(grid), len(grid[0])
    char_grid = [["0" for _ in range(cols)] for _ in range(rows)]
    pos: Dict[int, Tuple[int,int]] = {}
    
    for i, (r, c, req) in islands.items():
        char_grid[r][c] = str(req)
        pos[i] = (r, c)
        
    for (i, j), cnt in solution.items():
        r1, c1 = pos[i]
        r2, c2 = pos[j]
        
        if r1 == r2:
            start_c, end_c = min(c1, c2), max(c1, c2)
            for c in range(start_c + 1, end_c):
                char_grid[r1][c] = "-" if cnt == 1 else "="
                
        elif c1 == c2:
            start_r, end_r = min(r1, r2), max(r1, r2)
            for r in range(start_r + 1, end_r):
                char_grid[r][c1] = "|" if cnt == 1 else "$"
                
    return char_grid

def write_output(
    solver_name: str,
    idx: int,
    grid: Grid,
    islands: Dict[int, Tuple[int, int, int]],
    solution: SolutionDict) -> None:
    
    out_dir = f"Outputs/{solver_name}"
    os.makedirs(out_dir, exist_ok=True)
    
    file_path = f"{out_dir}/output-{idx:02d}.txt"
    char_grid = draw_solution(grid, islands, solution)
    
    with open(file_path, "w", encoding="utf-8") as f:
        for row in char_grid:
            f.write('["' + '", "'.join(row) + '"]\n')