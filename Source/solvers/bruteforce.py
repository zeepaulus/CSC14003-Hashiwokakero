from typing import List, Dict, Tuple, Optional
import itertools
from cnf_encoder import CNFEncoder

Grid = List[List[int]]
SolutionDict = Dict[Tuple[int, int], int]

class BruteForceCNFSolver:
    def __init__(self, grid: Grid) -> None:
        self.grid: Grid = grid
        self.solution: Optional[SolutionDict] = None
        self.islands = None
        self.edges = None
        self.iterations = 0

    @staticmethod
    def _degrees_match(islands: Dict[int, Tuple[int, int, int]], solution: SolutionDict) -> bool:
        degree_counter: Dict[int, int] = {idx: 0 for idx in islands}
        for (u, v), cnt in solution.items():
            degree_counter[u] += cnt
            degree_counter[v] += cnt
        return all(degree_counter[idx] == islands[idx][2] for idx in islands)

    def solve(self):
        enc = CNFEncoder()
        enc.encode(self.grid)

        self.islands = enc.islands
        self.edges = enc.edges
        edge_vars = enc.edge_vars
        clauses = enc.cnf.clauses
        decision_limit = enc.vpool.top

        pure_clauses = [clause for clause in clauses if all(abs(lit) <= decision_limit for lit in clause)]
        edge_keys = list(edge_vars.keys())
        n_edges = len(edge_keys)
        self.iterations = 0

        for bridges in itertools.product([0, 1, 2], repeat=n_edges):
            self.iterations += 1
            current_assignment: Dict[int, bool] = {}
            temp_sol: SolutionDict = {}

            for idx, count in enumerate(bridges):
                edge_coord = edge_keys[idx]
                x1, x2 = edge_vars[edge_coord]
                if count == 0:
                    current_assignment[x1] = False
                    current_assignment[x2] = False
                elif count == 1:
                    current_assignment[x1] = True
                    current_assignment[x2] = False
                    temp_sol[edge_coord] = 1
                else:
                    current_assignment[x1] = True
                    current_assignment[x2] = True
                    temp_sol[edge_coord] = 2

            clause_ok = True
            for clause in pure_clauses:
                satisfied = False
                for lit in clause:
                    val = current_assignment.get(abs(lit))
                    if val is None:
                        continue
                    if (lit > 0 and val) or (lit < 0 and not val):
                        satisfied = True
                        break
                if not satisfied:
                    clause_ok = False
                    break

            if not clause_ok:
                continue
            if not self._degrees_match(self.islands, temp_sol):
                continue
            if CNFEncoder.check_connectivity(self.islands, temp_sol):
                self.solution = temp_sol
                return temp_sol, self.islands, self.edges

        self.solution = None
        return None, self.islands, self.edges
