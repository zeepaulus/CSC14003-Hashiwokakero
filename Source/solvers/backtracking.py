from typing import List, Dict, Tuple, Optional
from collections import Counter
from cnf_encoder import CNFEncoder

Grid = List[List[int]]
IslandInfo = Tuple[int, int, int]
EdgeInfo = Tuple[int, int, Tuple]
SolutionDict = Dict[Tuple[int, int], int]

class BacktrackingSolver:
    def __init__(self, grid: Grid) -> None:
        self.grid: Grid = grid
        self.solution: Optional[SolutionDict] = None
        self.islands: Dict[int, IslandInfo] = {}
        self.edges: List[EdgeInfo] = []
        self.recursive_calls = 0
        self.backtracks = 0

    @staticmethod
    def _unit_propagate(clauses: List[List[int]], assignment: Dict[int, bool]) -> Tuple[Optional[List[List[int]]], Optional[Dict[int, bool]]]:
        new_assignment = assignment.copy()
        active_clauses = []
        
        for clause in clauses:
            is_satisfied = False
            for lit in clause:
                val = new_assignment.get(abs(lit))
                if (lit > 0 and val is True) or (lit < 0 and val is False):
                    is_satisfied = True
                    break
            if not is_satisfied:
                active_clauses.append(clause)
        
        changed = True
        while changed:
            changed = False
            next_clauses = []
            
            for clause in active_clauses:
                unassigned = []
                is_satisfied = False
                
                for lit in clause:
                    val = new_assignment.get(abs(lit))
                    if val is None:
                        unassigned.append(lit)
                    elif (lit > 0 and val is True) or (lit < 0 and val is False):
                        is_satisfied = True
                        break
                
                if is_satisfied:
                    continue
                if not unassigned:
                    return None, None
                if len(unassigned) == 1:
                    lit = unassigned[0]
                    var = abs(lit)
                    val = (lit > 0)
                    if var in new_assignment and new_assignment[var] != val:
                        return None, None
                    if var not in new_assignment:
                        new_assignment[var] = val
                        changed = True
                else:
                    next_clauses.append(clause)
            
            active_clauses = next_clauses
            
        return active_clauses, new_assignment

    def solve(self) -> Tuple[Optional[SolutionDict], Dict[int, IslandInfo], List[EdgeInfo]]:
        enc = CNFEncoder()
        enc.encode(self.grid)
        
        self.islands = enc.islands
        self.edges = enc.edges
        edge_vars = enc.edge_vars
        
        initial_clauses = [list(c) for c in enc.cnf.clauses]
        decision_vars = set()
        for (x1, x2) in edge_vars.values():
            decision_vars.add(x1)
            decision_vars.add(x2)
            
        var_freq = Counter()
        for clause in initial_clauses:
            for lit in clause:
                if abs(lit) in decision_vars:
                    var_freq[abs(lit)] += 1
                    
        ordered_vars = sorted(var_freq.keys(), key=lambda v: -var_freq[v])
        self.recursive_calls = 0
        self.backtracks = 0

        def dpll(cur_clauses: List[List[int]], cur_assignment: Dict[int, bool]) -> Optional[Dict[int, bool]]:
            self.recursive_calls += 1
            up_clauses, up_assignment = self._unit_propagate(cur_clauses, cur_assignment)
            
            if up_clauses is None:
                self.backtracks += 1
                return None
            
            if not up_clauses:
                temp_sol = {}
                for (i, j), (x1, x2) in edge_vars.items():
                    cnt = 0
                    if up_assignment.get(x1, False): cnt = 1
                    if up_assignment.get(x2, False): cnt = 2
                    if cnt > 0: temp_sol[(i, j)] = cnt
                
                if CNFEncoder.check_connectivity(self.islands, temp_sol):
                    return up_assignment
                else:
                    self.backtracks += 1
                    return None

            chosen_var = None
            for v in ordered_vars:
                if v not in up_assignment:
                    chosen_var = v
                    break
            
            if chosen_var is None:
                for clause in up_clauses:
                    for lit in clause:
                        if abs(lit) not in up_assignment:
                            chosen_var = abs(lit)
                            break
                    if chosen_var: break
                if chosen_var is None:
                    self.backtracks += 1
                    return None

            for value in [True, False]:
                new_assignment = up_assignment.copy()
                new_assignment[chosen_var] = value
                res = dpll(up_clauses, new_assignment)
                if res is not None:
                    return res
            
            self.backtracks += 1
            return None

        final_assignment = dpll(initial_clauses, {})

        if final_assignment is None:
            self.solution = None
            return None, self.islands, self.edges

        sol: SolutionDict = {}
        for (i, j), (x1, x2) in edge_vars.items():
            v1 = final_assignment.get(x1, False)
            v2 = final_assignment.get(x2, False)
            if v1:
                cnt = 1 + (1 if v2 else 0)
                sol[(i, j)] = cnt

        self.solution = sol
        return sol, self.islands, self.edges
