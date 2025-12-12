from typing import List, Dict, Tuple, Optional
from pysat.solvers import Solver
from cnf_encoder import build_cnf_from_grid, CNFEncoder

Grid = List[List[int]]
IslandInfo = Tuple[int, int, int]
EdgeInfo = Tuple[int, int, Tuple]
SolutionDict = Dict[Tuple[int, int], int]

class PySatSolver:
    def __init__(self, grid: Grid) -> None:
        self.grid: Grid = grid
        self.solution: Optional[SolutionDict] = None
        self.islands: Dict[int, IslandInfo] = {}
        self.edges: List[EdgeInfo] = []
        self.conflicts = 0
        self.decisions = 0

    def solve(self) -> Tuple[Optional[SolutionDict], Dict[int, IslandInfo], List[EdgeInfo]]:
        cnf, vpool, islands, edges, edge_vars, max_var, _ = build_cnf_from_grid(self.grid)
        self.islands, self.edges = islands, edges
        decision_vars = set()
        for (x1, x2) in edge_vars.values():
            decision_vars.add(x1)
            decision_vars.add(x2)

        solution: Optional[SolutionDict] = None
        self.conflicts = 0
        self.decisions = 0
        
        with Solver(name="g4") as solver:
            solver.append_formula(cnf.clauses)
            while solver.solve():
                model = solver.get_model()
                true_vars = set(lit for lit in model if lit > 0)
                
                current_solution: SolutionDict = {}
                for (i, j), (x1, x2) in edge_vars.items():
                    val_x1 = x1 in true_vars
                    val_x2 = x2 in true_vars
                    if val_x1:
                        count = 2 if val_x2 else 1
                        current_solution[(i, j)] = count
                
                if CNFEncoder.check_connectivity(islands, current_solution):
                    solution = current_solution
                    try:
                        stats = solver.accum_stats()
                        self.conflicts = stats.get('conflicts', 0)
                        self.decisions = stats.get('decisions', 0)
                    except:
                        pass
                    break
                else:
                    blocking_clause = [-lit for lit in model if abs(lit) in decision_vars]
                    solver.add_clause(blocking_clause)
            
            if solution is None:
                try:
                    stats = solver.accum_stats()
                    self.conflicts = stats.get('conflicts', 0)
                    self.decisions = stats.get('decisions', 0)
                except:
                    pass

        self.solution = solution
        return solution, islands, edges
