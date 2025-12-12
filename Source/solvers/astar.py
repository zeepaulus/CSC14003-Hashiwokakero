import heapq
from typing import List, Dict, Tuple, Optional, Set
from cnf_encoder import build_cnf_from_grid, CNFEncoder 

Grid = List[List[int]]
IslandInfo = Tuple[int, int, int]
EdgeInfo = Tuple[int, int, Tuple]
SolutionDict = Dict[Tuple[int, int], int]


class AStarSolver:
    def __init__(self, grid: Grid) -> None:
        self.grid = grid
        self.solution: Optional[SolutionDict] = None
        self.islands: Dict[int, IslandInfo] = {}
        self.edges: List[EdgeInfo] = []
        self.expanded_nodes = 0
        self.generated_nodes = 0

    def solve(self) -> Tuple[Optional[SolutionDict], Dict[int, IslandInfo], List[EdgeInfo]]:
        _, _, islands, edges, edge_vars, _, crossing_pairs = build_cnf_from_grid(self.grid)
        self.islands, self.edges = islands, edges
        
        if not islands:
            return {}, islands, edges
        
        edge_list = list(edge_vars.keys())
        n_edges = len(edge_list)
        
        if n_edges == 0:
            if all(info[2] == 0 for info in islands.values()):
                return {}, islands, edges
            return None, islands, edges
        
        island_to_edges: Dict[int, List[int]] = {i: [] for i in islands}
        for idx, (i, j) in enumerate(edge_list):
            island_to_edges[i].append(idx)
            island_to_edges[j].append(idx)
        
        required_deg = {i: info[2] for i, info in islands.items()}
        
        crossing_set: Set[Tuple[int, int]] = set()
        edge_to_idx = {e: i for i, e in enumerate(edge_list)}
        for e1, e2 in crossing_pairs:
            if e1 in edge_to_idx and e2 in edge_to_idx:
                a, b = edge_to_idx[e1], edge_to_idx[e2]
                crossing_set.add((min(a, b), max(a, b)))
        
        crossing_lookup: Dict[int, Set[int]] = {i: set() for i in range(n_edges)}
        for a, b in crossing_set:
            crossing_lookup[a].add(b)
            crossing_lookup[b].add(a)
        
        def get_bounds(state: tuple, island_id: int) -> Tuple[int, int]:
            min_d, max_d = 0, 0
            for e in island_to_edges[island_id]:
                v = state[e]
                if v is None:
                    max_d += 2
                else:
                    min_d += v
                    max_d += v
            return min_d, max_d
        
        def propagate(state: tuple) -> Optional[tuple]:
            state_list = list(state)
            changed = True
            
            while changed:
                changed = False
                for island_id, req in required_deg.items():
                    edges_idx = island_to_edges[island_id]
                    min_d, max_d = 0, 0
                    undecided = []
                    for e in edges_idx:
                        v = state_list[e]
                        if v is None:
                            undecided.append(e)
                            max_d += 2
                        else:
                            min_d += v
                            max_d += v
                    
                    if req > max_d or req < min_d:
                        return None

                    deficit = req - min_d
                    slack = max_d - req
                    
                    if not undecided:
                        continue

                    if deficit == 0:
                        for e in undecided:
                            if state_list[e] is None:
                                state_list[e] = 0
                                changed = True
                    elif slack == 0:
                        for e in undecided:
                            if state_list[e] is None:
                                can_set_2 = all(state_list[ce] is None or state_list[ce] == 0 for ce in crossing_lookup[e])
                                if not can_set_2:
                                    return None
                                state_list[e] = 2
                                changed = True
                                for ce in crossing_lookup[e]:
                                    if state_list[ce] is None:
                                        state_list[ce] = 0
                                        changed = True
                    elif len(undecided) == 1 and deficit > 0:
                        e = undecided[0]
                        if deficit > 2:
                            return None
                        if deficit > 0:
                            for ce in crossing_lookup[e]:
                                if state_list[ce] is not None and state_list[ce] > 0:
                                    return None
                        state_list[e] = deficit
                        changed = True
                        if deficit > 0:
                            for ce in crossing_lookup[e]:
                                if state_list[ce] is None:
                                    state_list[ce] = 0
                                    changed = True
            
            return tuple(state_list)
        
        def heuristic(state: tuple) -> float:
            total_deficit = 0
            for island_id, req in required_deg.items():
                min_d, max_d = get_bounds(state, island_id)
                if req > max_d or req < min_d:
                    return float('inf')
                total_deficit += max(0, req - min_d)
            h_bridges = total_deficit // 2
            
            parent = list(range(len(islands)))
            island_list = list(islands.keys())
            idx_map = {iid: i for i, iid in enumerate(island_list)}
            
            def find(x):
                while parent[x] != x:
                    parent[x] = parent[parent[x]]
                    x = parent[x]
                return x
            
            for e_idx, (i, j) in enumerate(edge_list):
                if state[e_idx] is not None and state[e_idx] > 0:
                    pi, pj = find(idx_map[i]), find(idx_map[j])
                    if pi != pj:
                        parent[pi] = pj
            
            components = len(set(find(i) for i in range(len(islands))))
            return max(h_bridges, components - 1)
        
        def is_complete(state: tuple) -> bool:
            return all(v is not None for v in state)
        
        def is_valid_solution(state: tuple) -> bool:
            for island_id, req in required_deg.items():
                actual = sum(state[e] for e in island_to_edges[island_id])
                if actual != req:
                    return False
            solution = {edge_list[i]: v for i, v in enumerate(state) if v and v > 0}
            return CNFEncoder.check_connectivity(islands, solution)
        
        def get_successors(state: tuple) -> List[tuple]:
            best_edge, best_slack = -1, float('inf')
            for e_idx in range(n_edges):
                if state[e_idx] is not None:
                    continue
                i, j = edge_list[e_idx]
                _, max_i = get_bounds(state, i)
                _, max_j = get_bounds(state, j)
                slack = (max_i - required_deg[i]) + (max_j - required_deg[j])
                if slack < best_slack:
                    best_slack = slack
                    best_edge = e_idx
            
            if best_edge == -1:
                return []
            
            successors = []
            i, j = edge_list[best_edge]
            min_i, max_i = get_bounds(state, i)
            min_j, max_j = get_bounds(state, j)
            req_i, req_j = required_deg[i], required_deg[j]
            crossing_blocked = any(state[ce] is not None and state[ce] > 0 for ce in crossing_lookup[best_edge])
            
            for val in [1, 2, 0]:
                if val > 0 and crossing_blocked:
                    continue
                new_min_i, new_min_j = min_i + val, min_j + val
                new_max_i, new_max_j = max_i - 2 + val, max_j - 2 + val
                if new_min_i > req_i or new_min_j > req_j:
                    continue
                if new_max_i < req_i or new_max_j < req_j:
                    continue
                
                new_state = list(state)
                new_state[best_edge] = val
                if val > 0:
                    for ce in crossing_lookup[best_edge]:
                        if new_state[ce] is None:
                            new_state[ce] = 0
                
                propagated = propagate(tuple(new_state))
                if propagated is not None:
                    successors.append(propagated)
            
            return successors
        
        def count_bridges(state: tuple) -> int:
            return sum(v for v in state if v is not None and v > 0)
        
        init_state = propagate(tuple([None] * n_edges))
        if init_state is None:
            return None, islands, edges
        
        h0 = heuristic(init_state)
        if h0 == float('inf'):
            return None, islands, edges
        
        counter = 0
        pq = [(h0, counter, init_state)]
        visited = set()
        self.expanded_nodes = 0
        self.generated_nodes = 1

        while pq:
            f, _, state = heapq.heappop(pq)
            self.expanded_nodes += 1
            
            if state in visited:
                continue
            visited.add(state)
            
            if is_complete(state):
                if is_valid_solution(state):
                    solution = {edge_list[i]: v for i, v in enumerate(state) if v and v > 0}
                    self.solution = solution
                    return solution, islands, edges
                continue

            for succ in get_successors(state):
                if succ not in visited:
                    h = heuristic(succ)
                    if h < float('inf'):
                        g = count_bridges(succ)
                        counter += 1
                        self.generated_nodes += 1
                        heapq.heappush(pq, (g + h, counter, succ))

        self.solution = None
        return None, islands, edges
