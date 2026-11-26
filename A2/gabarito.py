"""
PAA 2025.2 — GABARITO das questões práticas (soluções de referência)
=====================================================================
Só olhe depois de tentar! Para resolver, use o arquivo `praticas.py`
e rode `python testes.py`. Somente biblioteca padrão.

Este arquivo também é usado por `testes.py` como "oráculo" nos testes
aleatórios e de desempenho.
"""
from __future__ import annotations

import bisect
import heapq
from collections import deque, defaultdict
from math import sqrt, inf

INF = inf


class Sensor:
    def __init__(self, id: int, x: float, y: float, r: float):
        self.id = id
        self.x = x
        self.y = y
        self.r = r

    def __repr__(self):
        return f"Sensor({self.id}, {self.x}, {self.y}, {self.r})"


class Task:
    def __init__(self, start, end, value, name):
        self.start = start
        self.end = end
        self.value = value
        self.name = name

    def __repr__(self):
        return f"Task({self.start}, {self.end}, {self.value}, {self.name!r})"


# ============================================================================
# ★★★ PRIORIDADE ALTA
# ============================================================================

def q01_orcamento_adaptacao(edges: list[tuple[int, int, int]], C: int) -> bool:
    """
    [Q01 ★★★] Orçamento para adaptar ruas — FONTE: Prova A2 2025.2, Questão 1
    Tema: Árvore Geradora Mínima (Kruskal + union-find)

    Cada aresta (a, b, custo) é um segmento de rua de mão dupla entre os
    cruzamentos a e b; custo é o preço de adaptá-lo. Os cruzamentos são os
    números que aparecem nas arestas (não necessariamente 0..n-1).
    Retorne True se é possível escolher segmentos com custo total <= C de forma
    que todos os cruzamentos fiquem conectados usando só os segmentos escolhidos.

    Complexidade esperada: O(E log E).

    Exemplo:
        edges = [(1,2,1),(1,4,2),(2,3,7),(2,5,1),(3,6,9),(4,5,3),
                 (4,7,2),(5,6,1),(5,8,2),(6,9,10),(7,8,1),(8,9,1)]
        C=16 -> True ;  C=21 -> True ;  C=10 -> False
    """
    vertices = set()
    for a, b, _ in edges:
        vertices.add(a)
        vertices.add(b)
    if len(vertices) <= 1:
        return C >= 0
    pai = {v: v for v in vertices}
    tam = {v: 1 for v in vertices}

    def find(x):
        while pai[x] != x:
            pai[x] = pai[pai[x]]
            x = pai[x]
        return x

    custo, usadas = 0, 0
    for a, b, c in sorted(edges, key=lambda e: e[2]):
        ra, rb = find(a), find(b)
        if ra != rb:
            if tam[ra] < tam[rb]:
                ra, rb = rb, ra
            pai[rb] = ra
            tam[ra] += tam[rb]
            custo += c
            usadas += 1
    if usadas != len(vertices) - 1:      # cidade desconexa: impossível
        return False
    return custo <= C


def q02_caminho_energia(edges: list[tuple[int, int, int]], origem: int, destino: int):
    """
    [Q02 ★★★] Caminho de menor saldo de bateria — FONTE: Prova A2 2025.2, Questão 2
    Tema: Bellman-Ford (pesos negativos)

    ADAPTAÇÃO: aqui cada tupla (a, b, consumo) é uma aresta DIRIGIDA a -> b
    (veja no guia por que a versão não-dirigida com pesos negativos é problemática).
    consumo < 0 significa recarga. É garantido que não há ciclos negativos.
    Retorne a lista de arestas [(a, b), ...] do caminho de origem até destino com
    menor consumo total, ou None se o destino for inalcançável.
    Se origem == destino, retorne [].

    Complexidade esperada: O(V·E).

    Exemplo (versão dirigida do exemplo da prova):
        edges = [(3,2,2),(2,1,2),(1,4,-2),(4,7,2),(7,8,-2),(8,9,1),
                 (2,5,-3),(5,6,3),(5,8,5)]
        q02_caminho_energia(edges, 3, 9) -> [(3,2),(2,1),(1,4),(4,7),(7,8),(8,9)]
    """
    vertices = {origem, destino}
    for a, b, _ in edges:
        vertices.add(a)
        vertices.add(b)
    d = {v: INF for v in vertices}
    pai = {v: None for v in vertices}
    d[origem] = 0
    for _ in range(len(vertices) - 1):
        mudou = False
        for a, b, w in edges:
            if d[a] != INF and d[a] + w < d[b]:
                d[b] = d[a] + w
                pai[b] = a
                mudou = True
        if not mudou:
            break
    if d[destino] == INF:
        return None
    caminho = []
    v = destino
    while v != origem:
        caminho.append((pai[v], v))
        v = pai[v]
    return caminho[::-1]


def q03_troco_minimo(coins: list[int], value: int):
    """
    [Q03 ★★★] Troco com menor número de moedas — FONTE: Prova A2 2025.2, Questão 3
    Tema: Programação dinâmica (o guloso falha para sistemas não canônicos)

    Retorne a lista (ordenada crescente) de moedas que somam `value` usando a
    menor quantidade possível (cada denominação pode ser usada várias vezes),
    ou -1 se for impossível. value = 0 -> [].

    Complexidade esperada: O(value · len(coins)) (pseudo-polinomial).

    Exemplos:
        coins=[1,5,6,9], value=11 -> [5, 6]
        coins=[2],       value=3  -> -1
        coins=[1,2,5],   value=11 -> [1, 5, 5]
    """
    dp = [0] + [INF] * value
    escolha = [0] * (value + 1)
    for x in range(1, value + 1):
        for m in coins:
            if m <= x and dp[x - m] + 1 < dp[x]:
                dp[x] = dp[x - m] + 1
                escolha[x] = m
    if dp[value] == INF:
        return -1
    res = []
    while value:
        res.append(escolha[value])
        value -= escolha[value]
    return sorted(res)


def q04_rota_sensores(sensors: list[Sensor], s_i: int, s_f: int):
    """
    [Q04 ★★★] Rede de sensores (ida e volta) — FONTE: Simulado A2 2025.2, Questão 1
    Tema: Dijkstra em grafo DIRIGIDO construído a partir da geometria

    O sensor A envia diretamente para B se dist(A, B) <= A.r (depende do raio
    de quem envia). Retorne a sequência de ids
    do caminho de menor distância de s_i até s_f seguida do caminho de menor
    distância de s_f de volta a s_i (sem repetir s_f), ou None se algum dos
    dois trechos não existir.

    Complexidade esperada: O(n² + n² log n) — construir o grafo é Θ(n²).

    Exemplo:
        sensors = [Sensor(0,0,0,30), Sensor(1,25,0,25), Sensor(2,50,0,30),
                   Sensor(3,15,20,35), Sensor(4,35,25,25), Sensor(5,75,10,15),
                   Sensor(6,70,20,20), Sensor(7,55,25,25)]
        q04_rota_sensores(sensors, 0, 5) -> [0, 1, 2, 5, 6, 7, 4, 3, 0]
    """
    adj = {s.id: [] for s in sensors}
    for a in sensors:
        for b in sensors:
            if a.id != b.id:
                d = sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)
                if d <= a.r:
                    adj[a.id].append((b.id, d))

    def dijkstra(o, t):
        dist = {v: INF for v in adj}
        pai = {v: None for v in adj}
        dist[o] = 0
        heap = [(0, o)]
        while heap:
            du, u = heapq.heappop(heap)
            if du > dist[u]:
                continue
            for v, w in adj[u]:
                if du + w < dist[v]:
                    dist[v] = du + w
                    pai[v] = u
                    heapq.heappush(heap, (dist[v], v))
        if dist[t] == INF:
            return None
        cam = [t]
        while cam[-1] != o:
            cam.append(pai[cam[-1]])
        return cam[::-1]

    ida = dijkstra(s_i, s_f)
    if ida is None:
        return None
    volta = dijkstra(s_f, s_i)
    if volta is None:
        return None
    return ida + volta[1:]


def q05_eh_ponte(graph: list[list[int]], n: int, vi: int, vj: int) -> bool:
    """
    [Q05 ★★★] A aresta é uma ponte? — FONTE: Simulado A2 2025.2, Questão 2(b)
    Tema: BFS/DFS (conectividade)

    graph é a lista de adjacência de um grafo NÃO dirigido e conexo com
    vértices 0..n-1. Retorne True se remover a aresta (vi, vj) desconecta o grafo.
    O enunciado original exige O(V + E).

    Complexidade esperada: O(V + E).

    Exemplo:
        edges = [(0,1),(0,3),(1,2),(1,4),(3,4)]  (n = 5)
        (1,2) -> True ; (4,3) -> False ; (0,1) -> False
    """
    visitado = [False] * n
    visitado[vi] = True
    fila = deque([vi])
    pulou = False
    while fila:
        u = fila.popleft()
        for v in graph[u]:
            if not pulou and ((u == vi and v == vj) or (u == vj and v == vi)):
                pulou = True          # ignora UMA cópia da aresta removida
                continue
            if not visitado[v]:
                visitado[v] = True
                fila.append(v)
    return not visitado[vj]


def q06_rota_alternativa(n: int, streets: list[tuple[int, int]],
                         queries: list[tuple[int, int]]) -> list[int]:
    """
    [Q06 ★★★] Rota alternativa após interditar uma rua — FONTE: Prova AS 2025.2, Questão 3
    Tema: BFS (caminho mais curto em nº de arestas)

    Cruzamentos 0..n-1, ruas de mão dupla. Para cada consulta (a, b) (uma rua
    existente), retorne o número de ruas da menor rota de a até b SEM usar essa
    rua, ou -1 se não existir. O enunciado original exige O(m · (V + E)),
    com m = nº de consultas.

    Complexidade esperada: O(m · (V + E)), m = nº de consultas.

    Exemplo:
        n=5, streets=[(0,1),(1,2),(2,0),(2,3),(3,4)], queries=[(0,1),(2,3),(3,4)]
        -> [2, -1, -1]
    """
    adj = [[] for _ in range(n)]
    for i, (a, b) in enumerate(streets):
        adj[a].append((b, i))
        adj[b].append((a, i))
    resp = []
    for a, b in queries:
        proibida = -1
        for i, (x, y) in enumerate(streets):
            if (x, y) in ((a, b), (b, a)):
                proibida = i
                break
        dist = [-1] * n
        dist[a] = 0
        fila = deque([a])
        while fila:
            u = fila.popleft()
            for v, i in adj[u]:
                if i != proibida and dist[v] == -1:
                    dist[v] = dist[u] + 1
                    fila.append(v)
        resp.append(dist[b])
    return resp


def q07_agendamento_tarefas(tasks: list[Task]) -> tuple[int, list[str]]:
    """
    [Q07 ★★★] Agendamento de tarefas com valor — FONTE: Simulado A2 2025.2, Questão 3
    Tema: Programação dinâmica + "tarefa anterior compatível" (busca binária)

    Duas tarefas são compatíveis se uma termina antes ou exatamente quando a
    outra começa (end <= start). Retorne (valor_máximo, nomes das tarefas
    escolhidas) — a ordem dos nomes não importa.

    Complexidade esperada: O(n log n) (O(n²) se a busca da anterior for linear).

    Exemplo:
        tasks = [Task(1,3,50,"A"), Task(4,6,30,"B"), Task(7,9,30,"C"),
                 Task(2,5,20,"D"), Task(5,7,40,"E"), Task(6,8,60,"F")]
        -> (140, ['A', 'B', 'F'])
    """
    if not tasks:
        return 0, []
    T = sorted(tasks, key=lambda t: t.end)
    fins = [t.end for t in T]
    n = len(T)

    def anterior_compativel(j):     # nº de tarefas (prefixo) que terminam <= start_j
        return bisect.bisect_right(fins, T[j].start, 0, j)

    dp = [0] * (n + 1)
    for j in range(n):
        dp[j + 1] = max(dp[j], T[j].value + dp[anterior_compativel(j)])
    nomes, j = [], n
    while j > 0:
        p = anterior_compativel(j - 1)
        if T[j - 1].value + dp[p] >= dp[j - 1]:
            nomes.append(T[j - 1].name)
            j = p
        else:
            j -= 1
    return dp[n], nomes[::-1]


def q08_menores_custos(n: int, adj: list[list[tuple[int, int]]], s: int):
    """
    [Q08 ★★★] Menores custos a partir de uma origem — FONTE: Slides 10 (Menor caminho)
    Tema: caminho mais barato com pesos >= 0

    adj[u] = [(v, w), ...] (grafo dirigido, w >= 0). Retorne (dist, parent):
      dist[v]   = custo do caminho mais barato de s a v (float('inf') se inalcançável)
      parent[v] = vértice anterior a v nesse caminho; parent[s] = s; -1 se inalcançável

    Complexidade esperada: O((V + E) log V).
    """
    dist = [INF] * n
    parent = [-1] * n
    dist[s] = 0
    parent[s] = s
    heap = [(0, s)]
    while heap:
        du, u = heapq.heappop(heap)
        if du > dist[u]:
            continue
        for v, w in adj[u]:
            if du + w < dist[v]:
                dist[v] = du + w
                parent[v] = u
                heapq.heappush(heap, (dist[v], v))
    return dist, parent


def q09_custos_com_negativos(n: int, edges: list[tuple[int, int, int]], s: int):
    """
    [Q09 ★★★] Menores custos com pesos negativos — FONTE: Slides 10 (Menor caminho)
    Tema: pesos negativos e detecção de ciclo negativo

    edges = [(u, v, w), ...] dirigidas, vértices 0..n-1. Retorne (ok, dist):
      ok = False se existe ciclo negativo ALCANÇÁVEL a partir de s (dist pode ser qualquer coisa);
      ok = True e dist[v] = menor custo (float('inf') se inalcançável) caso contrário.

    Complexidade esperada: O(V · E).
    """
    dist = [INF] * n
    dist[s] = 0
    for _ in range(n - 1):
        mudou = False
        for u, v, w in edges:
            if dist[u] != INF and dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                mudou = True
        if not mudou:
            break
    for u, v, w in edges:
        if dist[u] != INF and dist[u] + w < dist[v]:
            return False, dist
    return True, dist


def q10_arvore_minima_arestas(n: int, edges: list[tuple[int, int, int]]):
    """
    [Q10 ★★★] Árvore geradora mínima (lista de arestas) — FONTE: Slides 11 (Árvore geradora mínima)
    Tema: MST

    Grafo não dirigido, vértices 0..n-1, edges = [(u, v, w), ...].
    Retorne (custo_total, lista_de_arestas_da_MST) com arestas no formato da
    entrada, ou None se o grafo for desconexo.

    Complexidade esperada: O(E log E).
    """
    pai = list(range(n))
    tam = [1] * n

    def find(x):
        while pai[x] != x:
            pai[x] = pai[pai[x]]
            x = pai[x]
        return x

    custo, mst = 0, []
    for u, v, w in sorted(edges, key=lambda e: e[2]):
        ru, rv = find(u), find(v)
        if ru != rv:
            if tam[ru] < tam[rv]:
                ru, rv = rv, ru
            pai[rv] = ru
            tam[ru] += tam[rv]
            custo += w
            mst.append((u, v, w))
    if len(mst) != n - 1:
        return None
    return custo, mst


def q11_arvore_minima_adjacencia(n: int, adj: list[list[tuple[int, int]]]):
    """
    [Q11 ★★★] Árvore geradora mínima (lista de adjacência) — FONTE: Slides 11 (Árvore geradora mínima)
    Tema: MST

    adj[u] = [(v, w), ...] de um grafo NÃO dirigido (cada aresta aparece nos
    dois sentidos). Retorne (custo_total, parent), com parent descrevendo a
    árvore enraizada no vértice 0: parent[0] = 0 e parent[v] = pai de v,
    ou None se o grafo for desconexo.

    Complexidade esperada: O((V + E) log V).
    """
    custo_v = [INF] * n
    parent = [-1] * n
    na = [False] * n
    custo_v[0] = 0
    parent[0] = 0
    heap = [(0, 0)]
    total = 0
    while heap:
        c, u = heapq.heappop(heap)
        if na[u]:
            continue
        na[u] = True
        total += c
        for v, w in adj[u]:
            if not na[v] and w < custo_v[v]:
                custo_v[v] = w
                parent[v] = u
                heapq.heappush(heap, (w, v))
    if not all(na):
        return None
    return total, parent


def _edmonds_karp(n, arcos, s, t):
    g = [[] for _ in range(n)]
    for u, v, c in arcos:
        g[u].append([v, c, len(g[v])])
        g[v].append([u, 0, len(g[u]) - 1])
    total = 0
    while True:
        pai = [None] * n
        pai[s] = (s, -1)
        fila = deque([s])
        while fila and pai[t] is None:
            u = fila.popleft()
            for i, (v, cap, _) in enumerate(g[u]):
                if cap > 0 and pai[v] is None:
                    pai[v] = (u, i)
                    fila.append(v)
        if pai[t] is None:
            return total, g
        delta = INF
        v = t
        while v != s:
            u, i = pai[v]
            delta = min(delta, g[u][i][1])
            v = u
        v = t
        while v != s:
            u, i = pai[v]
            g[u][i][1] -= delta
            g[v][g[u][i][2]][1] += delta
            v = u
        total += delta


def q12_fluxo_maximo(n: int, edges: list[tuple[int, int, int]], s: int, t: int) -> int:
    """
    [Q12 ★★★] Fluxo máximo — FONTE: Slides 12 (Fluxo máximo)
    Tema: rede residual, caminhos aumentadores

    edges = [(u, v, capacidade), ...] dirigidas, vértices 0..n-1 (pode haver
    arestas paralelas e antiparalelas). Retorne a intensidade do fluxo máximo de s a t.

    Complexidade esperada: O(V · E²) (Edmonds-Karp).
    """
    if s == t:
        return 0
    return _edmonds_karp(n, edges, s, t)[0]


def q13_ordem_topologica(n: int, adj: list[list[int]]):
    """
    [Q13 ★★★] Ordem topológica — FONTE: Slides 09 (Busca em grafos)
    Tema: DAG, fontes, grau de entrada

    adj[u] = lista de vizinhos (grafo dirigido, vértices 0..n-1).
    Retorne uma lista com os vértices em ordem topológica (toda aresta u->v com
    u antes de v), ou None se o grafo tiver ciclo.

    Complexidade esperada: O(V + E).
    """
    grau = [0] * n
    for u in range(n):
        for v in adj[u]:
            grau[v] += 1
    fila = deque(u for u in range(n) if grau[u] == 0)
    ordem = []
    while fila:
        u = fila.popleft()
        ordem.append(u)
        for v in adj[u]:
            grau[v] -= 1
            if grau[v] == 0:
                fila.append(v)
    return ordem if len(ordem) == n else None


def q14_viagem_cupom(n: int, routes: list[tuple[int, int, int]]) -> int:
    """
    [Q14 ★★★] Viagem intergaláctica com cupom — FONTE: Lista 3, Questão 6 (≈ CSES 1195 "Flight Discount")
    Tema: Dijkstra em grafo de estados (vértice, já usou cupom?)

    Planetas 1..n, rotas DIRIGIDAS (a, b, c). Exatamente uma rota do percurso
    pode ter o custo reduzido para c // 2. Retorne o menor custo de 1 até n
    (ou -1 se n for inalcançável).

    Complexidade esperada: O(m log n).

    Exemplos:
        n=3, routes=[(1,2,3),(2,3,1),(1,3,7)] -> 2
        n=3, routes=[(1,2,3),(2,3,3),(1,3,7)] -> 3
    """
    adj = [[] for _ in range(n + 1)]
    for a, b, c in routes:
        adj[a].append((b, c))
    dist = [[INF, INF] for _ in range(n + 1)]
    dist[1][0] = 0
    heap = [(0, 1, 0)]
    while heap:
        d, u, usou = heapq.heappop(heap)
        if d > dist[u][usou]:
            continue
        for v, c in adj[u]:
            if d + c < dist[v][usou]:
                dist[v][usou] = d + c
                heapq.heappush(heap, (d + c, v, usou))
            if not usou and d + c // 2 < dist[v][1]:
                dist[v][1] = d + c // 2
                heapq.heappush(heap, (d + c // 2, v, 1))
    r = min(dist[n])
    return -1 if r == INF else r


def q15_reparo_estradas(n: int, roads: list[tuple[int, int, int]]) -> int:
    """
    [Q15 ★★★] Reparo das estradas — FONTE: Lista 3, Questão 7 (≈ CSES 1675 "Road Reparation")
    Tema: MST (estradas com custo 0 já estão boas)

    Cidades 1..n, estradas bidirecionais (a, b, c), c >= 0. Retorne o custo
    mínimo para que todas as cidades fiquem conectadas, ou -1 se for impossível.

    Complexidade esperada: O(m log n).

    Exemplos:
        n=5, [(1,2,3),(2,3,5),(2,4,2),(3,4,8),(5,1,7),(5,4,4)] -> 14
        n=5, [(1,2,3),(2,3,5),(2,4,2),(3,4,0),(5,1,7),(5,4,4)] -> 9
        n=2, [(1,2,0)] -> 0
    """
    pai = list(range(n + 1))

    def find(x):
        while pai[x] != x:
            pai[x] = pai[pai[x]]
            x = pai[x]
        return x

    total, usadas = 0, 0
    for a, b, c in sorted(roads, key=lambda e: e[2]):
        ra, rb = find(a), find(b)
        if ra != rb:
            pai[ra] = rb
            total += c
            usadas += 1
    return total if usadas == n - 1 else -1


def q16_formas_zerar_jogo(n: int, transitions: list[tuple[int, int]]) -> int:
    """
    [Q16 ★★★] Quantas formas de zerar o jogo — FONTE: Lista 3, Questão 8 (≈ CSES 1681 "Game Routes")
    Tema: contagem de caminhos em DAG via ordem topológica (PD no DAG)

    Estados 1..n, transições dirigidas (a, b), o grafo é acíclico. Retorne o
    número de caminhos distintos do estado 1 ao estado n (sem módulo).

    Complexidade esperada: O(n + m).

    Exemplos:
        n=3, [(1,2),(2,3)] -> 1
        n=5, [(1,3),(3,4),(1,2),(2,5),(1,4),(4,5),(3,5)] -> 4
        n=3, [(1,2),(3,2)] -> 0
    """
    adj = [[] for _ in range(n + 1)]
    grau = [0] * (n + 1)
    for a, b in transitions:
        adj[a].append(b)
        grau[b] += 1
    fila = deque(v for v in range(1, n + 1) if grau[v] == 0)
    ways = [0] * (n + 1)
    ways[1] = 1
    while fila:
        u = fila.popleft()
        for v in adj[u]:
            ways[v] += ways[u]
            grau[v] -= 1
            if grau[v] == 0:
                fila.append(v)
    return ways[n]


def q17_escape_caverna(grid: list[str]) -> int:
    """
    [Q17 ★★★] Escape se for possível — FONTE: Lista 3, Questão 5 (≈ CSES 1194 "Monsters")
    Tema: BFS com múltiplas fontes (água) + BFS da pessoa

    grid é uma lista de strings com 'V' (você), 'A' (água), '.' (livre), '#' (parede).
    A cada instante a água se espalha para os vizinhos (4 direções) e você anda
    uma casa. Você só pode entrar numa casa no instante t se a água chegar nela
    estritamente depois de t. Escapar = estar numa casa da borda do grid.
    Retorne o menor número de movimentos para escapar, ou -1.

    Complexidade esperada: O(n · m).

    Exemplos (ver testes): 5, -1 e 0.
    """
    n, m = len(grid), len(grid[0])
    agua = [[INF] * m for _ in range(n)]
    fila = deque()
    inicio = None
    for i in range(n):
        for j in range(m):
            if grid[i][j] == 'A':
                agua[i][j] = 0
                fila.append((i, j))
            elif grid[i][j] == 'V':
                inicio = (i, j)
    viz = ((1, 0), (-1, 0), (0, 1), (0, -1))
    while fila:
        i, j = fila.popleft()
        for di, dj in viz:
            a, b = i + di, j + dj
            if 0 <= a < n and 0 <= b < m and grid[a][b] != '#' and agua[a][b] == INF:
                agua[a][b] = agua[i][j] + 1
                fila.append((a, b))

    def borda(i, j):
        return i == 0 or j == 0 or i == n - 1 or j == m - 1

    if borda(*inicio):
        return 0
    t = [[-1] * m for _ in range(n)]
    t[inicio[0]][inicio[1]] = 0
    fila = deque([inicio])
    while fila:
        i, j = fila.popleft()
        for di, dj in viz:
            a, b = i + di, j + dj
            if 0 <= a < n and 0 <= b < m and grid[a][b] != '#' and t[a][b] == -1:
                nt = t[i][j] + 1
                if nt < agua[a][b]:
                    if borda(a, b):
                        return nt
                    t[a][b] = nt
                    fila.append((a, b))
    return -1


def q18_cavalo(n: int) -> list[list[int]]:
    """
    [Q18 ★★★] Cavalo no tabuleiro — FONTE: Lista 3, Questão 4
    Tema: BFS em grafo implícito

    Tabuleiro n x n (n >= 3). Retorne a matriz A em que A[i][j] é o número
    mínimo de movimentos de cavalo para ir de (i, j) até (0, 0).

    Casas inalcançáveis (só acontece no centro do 3x3) recebem -1.

    Complexidade esperada: O(n²).
    """
    A = [[-1] * n for _ in range(n)]
    A[0][0] = 0
    fila = deque([(0, 0)])
    movs = ((1, 2), (2, 1), (-1, 2), (-2, 1), (1, -2), (2, -1), (-1, -2), (-2, -1))
    while fila:
        i, j = fila.popleft()
        for di, dj in movs:
            a, b = i + di, j + dj
            if 0 <= a < n and 0 <= b < n and A[a][b] == -1:
                A[a][b] = A[i][j] + 1
                fila.append((a, b))
    return A


def q19_todas_as_pontes(n: int, connections: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """
    [Q19 ★★★] Todas as pontes (conexões críticas) — FONTE EXTERNA: LeetCode 1192 "Critical Connections in a Network"
    Tema: DFS + low-link de Tarjan (generaliza a Q05 do simulado)

    Grafo não dirigido, vértices 0..n-1, sem arestas paralelas. Retorne todas
    as arestas cuja remoção desconecta o grafo (qualquer ordem/orientação).

    Complexidade esperada: O(V + E)  (fazer uma BFS por aresta = O(E(V+E)) é lento!)

    Exemplo: n=4, [(0,1),(1,2),(2,0),(1,3)] -> [(1,3)]
    """
    adj = [[] for _ in range(n)]
    for i, (a, b) in enumerate(connections):
        adj[a].append((b, i))
        adj[b].append((a, i))
    pre = [-1] * n
    low = [0] * n
    pontes = []
    t = 0
    for s in range(n):
        if pre[s] != -1:
            continue
        pre[s] = low[s] = t
        t += 1
        pilha = [(s, -1, 0)]               # (vértice, id da aresta para o pai, próximo índice)
        while pilha:
            u, ep, k = pilha[-1]
            if k < len(adj[u]):
                pilha[-1] = (u, ep, k + 1)
                v, ei = adj[u][k]
                if ei == ep:
                    continue
                if pre[v] == -1:
                    pre[v] = low[v] = t
                    t += 1
                    pilha.append((v, ei, 0))
                else:
                    low[u] = min(low[u], pre[v])
            else:
                pilha.pop()
                if pilha:
                    p = pilha[-1][0]
                    low[p] = min(low[p], low[u])
                    if low[u] > pre[p]:
                        pontes.append((p, u))
    return pontes


def q20_velocidade_download(n: int, connections: list[tuple[int, int, int]]) -> int:
    """
    [Q20 ★★★] Velocidade de download — FONTE EXTERNA: CSES 1694 "Download Speed"
    Tema: fluxo máximo

    Computadores 1..n; o servidor é o 1 e o seu computador é o n. Cada conexão
    (a, b, c) transmite até c unidades por segundo de a para b (dirigida).
    Retorne a velocidade máxima de download.

    Complexidade esperada: O(V · E²).

    Exemplo: n=4, [(1,2,3),(2,4,2),(1,3,4),(3,4,5),(4,1,3)] -> 6
    """
    return _edmonds_karp(n, [(a - 1, b - 1, c) for a, b, c in connections], 0, n - 1)[0]


# ============================================================================
# ★★ PRIORIDADE MÉDIA
# ============================================================================

def q21_plataformas_trem(trains: list[tuple[int, int]]) -> int:
    """
    [Q21 ★★] Plataformas de trem — FONTE: Prova AS 2025.2, Questão 2
    Tema: guloso / varredura de eventos

    Cada trem é (chegada, partida). Dois trens podem dividir uma plataforma se a
    partida de um for <= chegada do outro. Retorne o número mínimo de plataformas.
    O enunciado original exige O(n log n).

    Complexidade esperada: O(n log n).

    Exemplos:
        [(1100,1130),(900,910),(950,1120),(940,1200)] -> 3
        [(100,200),(200,300)] -> 1
    """
    # Guloso: ordena por chegada; heap com os horários de partida das plataformas ocupadas.
    # Se a plataforma que libera primeiro já liberou (partida <= chegada), reaproveita.
    ocupadas = []
    for a, b in sorted(trains):
        if ocupadas and ocupadas[0] <= a:
            heapq.heapreplace(ocupadas, b)
        else:
            heapq.heappush(ocupadas, b)
    return len(ocupadas)


def q22_menor_distancia_pontos(points: list[tuple[float, float]]) -> float:
    """
    [Q22 ★★] Par de pontos mais próximo — FONTE: Prova AS 2025.2, Questão 1 (e Slides 07)
    Tema: dividir e conquistar

    Retorne a menor distância euclidiana entre dois pontos distintos da lista
    (len(points) >= 2).

    Complexidade esperada: O(n log n)  (força bruta O(n²) não passa no teste de desempenho).
    """
    def dist(p, q):
        return sqrt((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2)

    def rec(px):
        n = len(px)
        if n <= 3:
            d = INF
            for i in range(n):
                for j in range(i + 1, n):
                    d = min(d, dist(px[i], px[j]))
            return d, sorted(px, key=lambda p: p[1])
        m = n // 2
        xm = px[m][0]
        dl, ly = rec(px[:m])
        dr, ry = rec(px[m:])
        d = min(dl, dr)
        py = []
        i = j = 0
        while i < len(ly) or j < len(ry):
            if j == len(ry) or (i < len(ly) and ly[i][1] <= ry[j][1]):
                py.append(ly[i]); i += 1
            else:
                py.append(ry[j]); j += 1
        faixa = [p for p in py if abs(p[0] - xm) < d]
        for i in range(len(faixa)):
            for j in range(i + 1, min(i + 8, len(faixa))):
                if faixa[j][1] - faixa[i][1] >= d:
                    break
                d = min(d, dist(faixa[i], faixa[j]))
        return d, py

    return rec(sorted(points))[0]


def q23_tem_ciclo_dirigido(n: int, adj: list[list[int]]) -> bool:
    """
    [Q23 ★★] Detectar ciclo em grafo dirigido — FONTE: Slides 09 (Busca em grafos)
    Tema: DFS e arestas de retorno

    Retorne True se o grafo dirigido (adj, vértices 0..n-1) possui um ciclo.

    Complexidade esperada: O(V + E). Cuidado com recursão profunda (use pilha
    explícita ou sys.setrecursionlimit) — há teste com caminho de 20000 vértices.
    """
    cor = [0] * n
    for s in range(n):
        if cor[s]:
            continue
        cor[s] = 1
        pilha = [(s, 0)]
        while pilha:
            u, k = pilha[-1]
            if k < len(adj[u]):
                pilha[-1] = (u, k + 1)
                v = adj[u][k]
                if cor[v] == 1:
                    return True
                if cor[v] == 0:
                    cor[v] = 1
                    pilha.append((v, 0))
            else:
                cor[u] = 2
                pilha.pop()
    return False


def q24_classificar_arestas(n: int, adj: list[list[int]]) -> dict:
    """
    [Q24 ★★] Classificar arestas — FONTE: Slides 09 (Busca em grafos)
    Tema: pré-ordem, pós-ordem, intervalo de vida

    Grafo DIRIGIDO. Rode a DFS iniciando nos vértices na ordem 0, 1, ..., n-1 e
    percorrendo cada adj[u] na ordem dada. Retorne um dicionário
    {(u, v): tipo} com tipo em {"arvore", "retorno", "avanco", "cruzada"}.

    Complexidade esperada: O(V + E).

    Exemplo: n=6, adj=[[1,2],[3,4],[4],[4],[5,1],[]] ->
        {(0,1):'arvore',(1,3):'arvore',(3,4):'arvore',(4,5):'arvore',(4,1):'retorno',
         (1,4):'avanco',(0,2):'arvore',(2,4):'cruzada'}
    """
    pre = [-1] * n
    post = [-1] * n
    tipo = {}
    c = [0, 0]
    for s in range(n):
        if pre[s] != -1:
            continue
        pre[s] = c[0]; c[0] += 1
        pilha = [(s, 0)]
        while pilha:
            u, k = pilha[-1]
            if k < len(adj[u]):
                pilha[-1] = (u, k + 1)
                v = adj[u][k]
                if pre[v] == -1:
                    tipo[(u, v)] = "arvore"
                    pre[v] = c[0]; c[0] += 1
                    pilha.append((v, 0))
                elif post[v] == -1:
                    tipo[(u, v)] = "retorno"
                elif pre[u] < pre[v]:
                    tipo[(u, v)] = "avanco"
                else:
                    tipo[(u, v)] = "cruzada"
            else:
                post[u] = c[1]; c[1] += 1
                pilha.pop()
    return tipo


def q25_corte_minimo(n: int, edges: list[tuple[int, int, int]], s: int, t: int):
    """
    [Q25 ★★] Corte mínimo — FONTE: Slides 12 (Fluxo máximo)
    Tema: alcançáveis no grafo residual

    Mesma entrada da Q12. Retorne (capacidade_do_corte, arestas_do_corte), onde
    arestas_do_corte é uma lista de tuplas (u, v, c) da entrada cuja remoção
    separa s de t e cuja soma de capacidades é mínima.

    Complexidade esperada: O(V · E²).
    """
    valor, g = _edmonds_karp(n, edges, s, t)
    alc = [False] * n
    alc[s] = True
    fila = deque([s])
    while fila:
        u = fila.popleft()
        for v, cap, _ in g[u]:
            if cap > 0 and not alc[v]:
                alc[v] = True
                fila.append(v)
    corte = [(u, v, c) for u, v, c in edges if alc[u] and not alc[v] and c > 0]
    return valor, corte


def q26_menor_caminho_dag(n: int, edges: list[tuple[int, int, int]], s: int) -> list:
    """
    [Q26 ★★] Caminho mais barato em DAG — FONTE: Slides 10 (Menor caminho em DAG)
    Tema: relaxamento seguindo a ordem topológica (aceita pesos negativos)

    edges = [(u, v, w), ...] de um DAG (pesos podem ser negativos). Retorne dist com dist[v] = menor custo de s a v
    (float('inf') se inalcançável).

    Complexidade esperada: O(V + E).
    """
    adj = [[] for _ in range(n)]
    grau = [0] * n
    for u, v, w in edges:
        adj[u].append((v, w))
        grau[v] += 1
    fila = deque(u for u in range(n) if grau[u] == 0)
    dist = [INF] * n
    dist[s] = 0
    while fila:
        u = fila.popleft()
        for v, w in adj[u]:
            if dist[u] != INF and dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
            grau[v] -= 1
            if grau[v] == 0:
                fila.append(v)
    return dist


def q27_bipartido(n: int, adj: list[list[int]]) -> bool:
    """
    [Q27 ★★] Grafo bipartido — FONTE: Slides 08 (definição) / ≈ LeetCode 785 "Is Graph Bipartite?"
    Tema: 2-coloração com BFS

    Grafo não dirigido (pode ser desconexo). Retorne True se for bipartido.

    Complexidade esperada: O(V + E).
    """
    cor = [-1] * n
    for s in range(n):
        if cor[s] != -1:
            continue
        cor[s] = 0
        fila = deque([s])
        while fila:
            u = fila.popleft()
            for v in adj[u]:
                if cor[v] == -1:
                    cor[v] = 1 - cor[u]
                    fila.append(v)
                elif cor[v] == cor[u]:
                    return False
    return True


def q28_tempo_atraso_rede(times: list[tuple[int, int, int]], n: int, k: int) -> int:
    """
    [Q28 ★★] Tempo de atraso da rede — FONTE EXTERNA: LeetCode 743 "Network Delay Time"
    Tema: Dijkstra

    Nós 1..n; times = [(u, v, w)] arestas dirigidas com tempo w >= 0. Um sinal
    sai do nó k. Retorne o tempo até TODOS os nós receberem o sinal, ou -1.

    Complexidade esperada: O(E log V).

    Exemplo: times=[(2,1,1),(2,3,1),(3,4,1)], n=4, k=2 -> 2
    """
    adj = [[] for _ in range(n + 1)]
    for u, v, w in times:
        adj[u].append((v, w))
    dist = [INF] * (n + 1)
    dist[k] = 0
    heap = [(0, k)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        for v, w in adj[u]:
            if d + w < dist[v]:
                dist[v] = d + w
                heapq.heappush(heap, (dist[v], v))
    r = max(dist[1:])
    return -1 if r == INF else r


def q29_voos_k_escalas(n: int, flights: list[tuple[int, int, int]], src: int, dst: int, k: int) -> int:
    """
    [Q29 ★★] Voo mais barato com até k escalas — FONTE EXTERNA: LeetCode 787 "Cheapest Flights Within K Stops"
    Tema: Bellman-Ford limitado (k+1 rodadas, usando cópia do vetor)

    Cidades 0..n-1, voos dirigidos (de, para, preço). Retorne o menor preço de
    src até dst usando no máximo k escalas (k+1 voos), ou -1.

    Complexidade esperada: O(k · E).

    Exemplo: n=4, [(0,1,100),(1,2,100),(2,0,100),(1,3,600),(2,3,200)], 0, 3, 1 -> 700
    """
    dist = [INF] * n
    dist[src] = 0
    for _ in range(k + 1):
        novo = dist[:]                  # cópia: cada rodada usa no máx. +1 aresta
        for u, v, w in flights:
            if dist[u] != INF and dist[u] + w < novo[v]:
                novo[v] = dist[u] + w
        dist = novo
    return -1 if dist[dst] == INF else dist[dst]


def q30_conectar_pontos(points: list[tuple[int, int]]) -> int:
    """
    [Q30 ★★] Custo mínimo para conectar todos os pontos — FONTE EXTERNA: LeetCode 1584 "Min Cost to Connect All Points"
    Tema: MST em grafo COMPLETO (denso) -> Prim com vetor O(V²)

    O custo de ligar dois pontos é a distância de Manhattan |x1-x2| + |y1-y2|.
    Retorne o custo mínimo para conectar todos.

    Complexidade esperada: O(n²)  (Kruskal com todas as arestas seria O(n² log n)).

    Exemplo: [(0,0),(2,2),(3,10),(5,2),(7,0)] -> 20
    """
    n = len(points)
    custo = [INF] * n
    na = [False] * n
    custo[0] = 0
    total = 0
    for _ in range(n):
        u = -1
        for v in range(n):
            if not na[v] and (u == -1 or custo[v] < custo[u]):
                u = v
        na[u] = True
        total += custo[u]
        xu, yu = points[u]
        for v in range(n):
            if not na[v]:
                d = abs(xu - points[v][0]) + abs(yu - points[v][1])
                if d < custo[v]:
                    custo[v] = d
    return total


def q31_pode_concluir_cursos(num_cursos: int, prerequisitos: list[tuple[int, int]]) -> bool:
    """
    [Q31 ★★] Grade de cursos — FONTE EXTERNA: LeetCode 207 "Course Schedule"
    Tema: ordem topológica / detecção de ciclo

    Cursos 0..num_cursos-1. Cada par (a, b) significa "para fazer a é preciso ter
    feito b" (aresta b -> a). Retorne True se é possível concluir todos.

    Complexidade esperada: O(V + E).
    """
    adj = [[] for _ in range(num_cursos)]
    grau = [0] * num_cursos
    for a, b in prerequisitos:
        adj[b].append(a)
        grau[a] += 1
    fila = deque(i for i in range(num_cursos) if grau[i] == 0)
    feitos = 0
    while fila:
        u = fila.popleft()
        feitos += 1
        for v in adj[u]:
            grau[v] -= 1
            if grau[v] == 0:
                fila.append(v)
    return feitos == num_cursos


def q32_numero_ilhas(grid: list[str]) -> int:
    """
    [Q32 ★★] Número de ilhas — FONTE EXTERNA: LeetCode 200 "Number of Islands" (≈ CSES 1192 "Counting Rooms")
    Tema: componentes conexas em grid (BFS/DFS)

    grid: lista de strings com '1' (terra) e '0' (água). Ilhas são grupos de
    '1' ligados na horizontal/vertical. Retorne a quantidade de ilhas.

    Complexidade esperada: O(linhas · colunas).
    """
    if not grid:
        return 0
    n, m = len(grid), len(grid[0])
    vis = [[False] * m for _ in range(n)]
    ilhas = 0
    for i in range(n):
        for j in range(m):
            if grid[i][j] == '1' and not vis[i][j]:
                ilhas += 1
                vis[i][j] = True
                fila = deque([(i, j)])
                while fila:
                    a, b = fila.popleft()
                    for x, y in ((a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)):
                        if 0 <= x < n and 0 <= y < m and grid[x][y] == '1' and not vis[x][y]:
                            vis[x][y] = True
                            fila.append((x, y))
    return ilhas


def q33_laranjas_podres(grid: list[list[int]]) -> int:
    """
    [Q33 ★★] Laranjas podres — FONTE EXTERNA: LeetCode 994 "Rotting Oranges"
    Tema: BFS com múltiplas fontes (mesma ideia da água na Q17)

    0 = vazio, 1 = laranja boa, 2 = laranja podre. A cada minuto, laranjas boas
    vizinhas (4 direções) de podres apodrecem. Retorne os minutos até não sobrar
    laranja boa, ou -1 se for impossível.

    Complexidade esperada: O(linhas · colunas).

    Exemplo: [[2,1,1],[1,1,0],[0,1,1]] -> 4
    """
    n, m = len(grid), len(grid[0])
    t = [[-1] * m for _ in range(n)]
    fila = deque()
    boas = 0
    for i in range(n):
        for j in range(m):
            if grid[i][j] == 2:
                t[i][j] = 0
                fila.append((i, j))
            elif grid[i][j] == 1:
                boas += 1
    resp = 0
    while fila:
        a, b = fila.popleft()
        for x, y in ((a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)):
            if 0 <= x < n and 0 <= y < m and grid[x][y] == 1 and t[x][y] == -1:
                t[x][y] = t[a][b] + 1
                resp = max(resp, t[x][y])
                boas -= 1
                fila.append((x, y))
    return resp if boas == 0 else -1


def q34_conexao_redundante(edges: list[tuple[int, int]]) -> tuple[int, int]:
    """
    [Q34 ★★] Conexão redundante — FONTE EXTERNA: LeetCode 684 "Redundant Connection"
    Tema: union-find (aresta que fecha ciclo = aresta que o Kruskal rejeitaria)

    Uma árvore com nós 1..n recebeu UMA aresta extra. edges tem n arestas.
    Retorne a aresta que pode ser removida para voltar a ser árvore; se houver
    várias, a que aparece por último na entrada.

    Complexidade esperada: O(n · α(n)) ≈ O(n).

    Exemplo: [(1,2),(1,3),(2,3)] -> (2,3)
    """
    pai = list(range(len(edges) + 1))

    def find(x):
        while pai[x] != x:
            pai[x] = pai[pai[x]]
            x = pai[x]
        return x

    for a, b in edges:
        ra, rb = find(a), find(b)
        if ra == rb:
            return (a, b)
        pai[ra] = rb
    return (-1, -1)


def q35_menor_esforco(heights: list[list[int]]) -> int:
    """
    [Q35 ★★] Caminho com menor esforço — FONTE EXTERNA: LeetCode 1631 "Path With Minimum Effort"
    Tema: Dijkstra com custo "gargalo" (max em vez de soma)

    Vá de (0,0) até (n-1,m-1) andando em 4 direções. O esforço de um caminho é a
    MAIOR diferença absoluta de altura entre duas casas consecutivas. Retorne o
    menor esforço possível.

    Complexidade esperada: O(nm log(nm)).

    Exemplo: [[1,2,2],[3,8,2],[5,3,5]] -> 2
    """
    n, m = len(heights), len(heights[0])
    best = [[INF] * m for _ in range(n)]
    best[0][0] = 0
    heap = [(0, 0, 0)]
    while heap:
        e, a, b = heapq.heappop(heap)
        if e > best[a][b]:
            continue
        if (a, b) == (n - 1, m - 1):
            return e
        for x, y in ((a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)):
            if 0 <= x < n and 0 <= y < m:
                ne = max(e, abs(heights[x][y] - heights[a][b]))
                if ne < best[x][y]:
                    best[x][y] = ne
                    heapq.heappush(heap, (ne, x, y))
    return best[n - 1][m - 1]


def q36_formas_menor_caminho(n: int, roads: list[tuple[int, int, int]]) -> int:
    """
    [Q36 ★★] Número de caminhos mais curtos — FONTE EXTERNA: LeetCode 1976 "Number of Ways to Arrive at Destination"
    Tema: Dijkstra + contagem (PD sobre a ordem de finalização do Dijkstra)

    Interseções 0..n-1, ruas bidirecionais (u, v, tempo > 0). Retorne quantos
    caminhos de 0 até n-1 têm o menor tempo possível, módulo 10**9 + 7.

    Complexidade esperada: O(E log V).

    Exemplo: n=7, [(0,6,7),(0,1,2),(1,2,3),(1,3,3),(6,3,3),(3,5,1),(6,5,1),(2,5,1),(0,4,5),(4,6,2)] -> 4
    """
    MOD = 10 ** 9 + 7
    adj = [[] for _ in range(n)]
    for u, v, w in roads:
        adj[u].append((v, w))
        adj[v].append((u, w))
    dist = [INF] * n
    ways = [0] * n
    dist[0] = 0
    ways[0] = 1
    heap = [(0, 0)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        for v, w in adj[u]:
            if d + w < dist[v]:
                dist[v] = d + w
                ways[v] = ways[u]
                heapq.heappush(heap, (dist[v], v))
            elif d + w == dist[v]:
                ways[v] = (ways[v] + ways[u]) % MOD
    return ways[n - 1] % MOD


def q37_maior_pontuacao(n: int, tunnels: list[tuple[int, int, int]]) -> int:
    """
    [Q37 ★★] Maior pontuação — FONTE EXTERNA: CSES 1673 "High Score"
    Tema: Bellman-Ford (caminho mais LONGO = mais barato com pesos negados) + ciclo

    Salas 1..n, túneis dirigidos (a, b, x): passar pelo túnel soma x pontos
    (x pode ser negativo). Vá de 1 até n (há pelo menos um caminho). Retorne a
    maior pontuação possível, ou -1 se ela puder ser arbitrariamente grande.

    Complexidade esperada: O(n · m).

    Exemplo: n=4, [(1,2,3),(2,4,-1),(1,3,-2),(3,4,7)] -> 5
    """
    edges = [(a, b, -x) for a, b, x in tunnels]
    radj = [[] for _ in range(n + 1)]
    for a, b, _ in edges:
        radj[b].append(a)
    chega_n = [False] * (n + 1)
    chega_n[n] = True
    fila = deque([n])
    while fila:
        u = fila.popleft()
        for v in radj[u]:
            if not chega_n[v]:
                chega_n[v] = True
                fila.append(v)
    d = [INF] * (n + 1)
    d[1] = 0
    for _ in range(n - 1):
        for a, b, w in edges:
            if d[a] != INF and d[a] + w < d[b]:
                d[b] = d[a] + w
    for a, b, w in edges:
        if d[a] != INF and d[a] + w < d[b] and chega_n[b]:
            return -1
    return -d[n]


def q38_ciclo_negativo(n: int, edges: list[tuple[int, int, int]]):
    """
    [Q38 ★★] Encontrar um ciclo negativo — FONTE EXTERNA: CSES 1197 "Cycle Finding"
    Tema: Bellman-Ford + reconstrução pelo vetor de pais

    Vértices 1..n, arestas dirigidas (a, b, w). Se existir ciclo de custo
    negativo (em qualquer lugar do grafo), retorne-o como lista de vértices que
    começa e termina no mesmo vértice, ex.: [2, 3, 4, 2]. Senão, retorne None.

    Dica: inicialize TODAS as distâncias com 0 (equivale a uma fonte virtual).
    Complexidade esperada: O(n · m).
    """
    d = [0] * (n + 1)
    pai = [-1] * (n + 1)
    x = -1
    for _ in range(n):
        x = -1
        for a, b, w in edges:
            if d[a] + w < d[b]:
                d[b] = d[a] + w
                pai[b] = a
                x = b
        if x == -1:
            return None
    for _ in range(n):                  # garante cair dentro do ciclo
        x = pai[x]
    ciclo = [x]
    v = pai[x]
    while v != x:
        ciclo.append(v)
        v = pai[v]
    ciclo.append(x)
    return ciclo[::-1]


def q39_rota_mais_longa_dag(n: int, flights: list[tuple[int, int]]):
    """
    [Q39 ★★] Rota com mais cidades — FONTE EXTERNA: CSES 1680 "Longest Flight Route"
    Tema: caminho mais longo em DAG (PD na ordem topológica)

    Cidades 1..n, voos dirigidos (a, b), grafo acíclico. Retorne a rota de 1 até
    n que visita o MAIOR número de cidades (lista de cidades), ou None se não existir.

    Complexidade esperada: O(n + m).  (Em grafo geral esse problema é NP-difícil!)
    """
    adj = [[] for _ in range(n + 1)]
    grau = [0] * (n + 1)
    for a, b in flights:
        adj[a].append(b)
        grau[b] += 1
    fila = deque(v for v in range(1, n + 1) if grau[v] == 0)
    best = [-INF] * (n + 1)
    pai = [0] * (n + 1)
    best[1] = 1
    while fila:
        u = fila.popleft()
        for v in adj[u]:
            if best[u] + 1 > best[v]:
                best[v] = best[u] + 1
                pai[v] = u
            grau[v] -= 1
            if grau[v] == 0:
                fila.append(v)
    if best[n] == -INF:
        return None
    rota = [n]
    while rota[-1] != 1:
        rota.append(pai[rota[-1]])
    return rota[::-1]


def q40_baile_escola(n_meninos: int, n_meninas: int, pares: list[tuple[int, int]]) -> int:
    """
    [Q40 ★★] Baile da escola — FONTE EXTERNA: CSES 1696 "School Dance"
    Tema: emparelhamento bipartido máximo = fluxo máximo com capacidades 1

    Meninos 1..n_meninos, meninas 1..n_meninas; pares (a, b) indicam que o
    menino a aceita dançar com a menina b. Cada pessoa dança com no máximo um
    par. Retorne o número máximo de pares formados.

    Complexidade esperada: O(V · E) (caminhos aumentadores).
    """
    adj = [[] for _ in range(n_meninos + 1)]
    for a, b in pares:
        adj[a].append(b)
    par_menina = [0] * (n_meninas + 1)

    def tenta(u, visto):
        for v in adj[u]:
            if not visto[v]:
                visto[v] = True
                if par_menina[v] == 0 or tenta(par_menina[v], visto):
                    par_menina[v] = u
                    return True
        return False

    total = 0
    for u in range(1, n_meninos + 1):
        if tenta(u, [False] * (n_meninas + 1)):
            total += 1
    return total


def q41_perseguicao_policial(n: int, ruas: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """
    [Q41 ★★] Perseguição policial — FONTE EXTERNA: CSES 1695 "Police Chase"
    Tema: corte mínimo em grafo não dirigido com capacidades 1

    Cruzamentos 1..n, ruas bidirecionais (a, b). Retorne uma lista com o MENOR
    número possível de ruas a bloquear para que não exista caminho de 1 até n.

    Complexidade esperada: O(V · E²).

    Exemplo: n=4, [(1,2),(1,3),(2,3),(3,4),(1,4)] -> 2 ruas, ex.: [(3,4),(1,4)]
    """
    arcos = []
    for a, b in ruas:
        arcos.append((a - 1, b - 1, 1))
        arcos.append((b - 1, a - 1, 1))
    _, g = _edmonds_karp(n, arcos, 0, n - 1)
    alc = [False] * n
    alc[0] = True
    fila = deque([0])
    while fila:
        u = fila.popleft()
        for v, cap, _ in g[u]:
            if cap > 0 and not alc[v]:
                alc[v] = True
                fila.append(v)
    return [(a, b) for a, b in ruas if alc[a - 1] != alc[b - 1]]


def q42_lucro_tarefas(start: list[int], end: list[int], profit: list[int]) -> int:
    """
    [Q42 ★★] Lucro máximo com tarefas — FONTE EXTERNA: LeetCode 1235 "Maximum Profit in Job Scheduling"
    Tema: mesma PD da Q07 (intervalos ponderados) com busca binária

    Tarefa i ocupa [start[i], end[i]) e dá profit[i]. Pode começar uma tarefa no
    exato instante em que outra termina. Retorne o lucro máximo.

    Complexidade esperada: O(n log n).

    Exemplo: start=[1,2,3,3], end=[3,4,5,6], profit=[50,10,40,70] -> 120
    """
    jobs = sorted(zip(start, end, profit), key=lambda j: j[1])
    fins = [j[1] for j in jobs]
    dp = [0] * (len(jobs) + 1)
    for i, (s, e, p) in enumerate(jobs):
        k = bisect.bisect_right(fins, s, 0, i)
        dp[i + 1] = max(dp[i], dp[k] + p)
    return dp[-1]


# ============================================================================
# ★ PRIORIDADE BAIXA / COMPLEMENTAR
# ============================================================================

def q43_sisi_sorvete_2(A: list[int]) -> int:
    """
    [Q43 ★] Sisi e a sorveteria, parte 2 — FONTE: Lista 3, Questão 1 (≈ Codeforces 1139B)
    Tema: guloso de trás para frente

    q_i <= A[i]; a sequência q é 0...0 e depois estritamente crescente.
    Retorne a soma máxima de q.

    Complexidade esperada: O(n).

    Exemplos: [1,2,1,3,6] -> 10 ; [3,2,5,4,10] -> 20 ; [2,2,2,2] -> 3
    """
    total = 0
    teto = INF
    for a in reversed(A):
        q = min(a, teto - 1)
        if q <= 0:
            break
        total += q
        teto = q
    return int(total)


def q44_custo_reparo(n: int, k: int, C1: int, C2: int, A: list[int]) -> int:
    """
    [Q44 ★] Minimizando custos de reparo — FONTE: Lista 3, Questão 2 (≈ Codeforces 1111C "Creative Snap")
    Tema: dividir e conquistar + busca binária para contar buracos

    Estrada [1, 2^n]; buracos nas posições A. Consertar um segmento de tamanho l
    custa C1 se não tem buracos e C2 · (nº de buracos) · l caso contrário; ou
    pode-se dividir o segmento ao meio (se l >= 2). Retorne o custo mínimo.

    Complexidade esperada: O(k log k · n)  (só recursa onde há buracos).

    Exemplos: (2, 2, 1, 2, [1,3]) -> 6 ; (3, 2, 1, 2, [1,7]) -> 8
    """
    P = sorted(A)

    def conta(l, r):
        return bisect.bisect_right(P, r) - bisect.bisect_left(P, l)

    def resolve(l, r):
        nb = conta(l, r)
        if nb == 0:
            return C1
        custo = C2 * nb * (r - l + 1)
        if l == r:
            return custo
        m = (l + r) // 2
        return min(custo, resolve(l, m) + resolve(m + 1, r))

    return resolve(1, 2 ** n)


def q45_subsequencias_radicais(A: list[int]) -> int:
    """
    [Q45 ★] Subsequências radicais — FONTE: Lista 3, Questão 3 (≈ Codeforces 1061C "Multiplicity")
    Tema: programação dinâmica sobre divisores

    Conte as subsequências não vazias b de A tais que b_i é divisível por i
    (1-indexado). Responda módulo 999999937.

    Complexidade esperada: O(n √n).

    Exemplos: [1,2,2] -> 6 ; [1] -> 1 ; [1,2] -> 3 ; [2,2,1,5,3] -> 7
    (o PDF da lista diz 8 para o último, mas a contagem por força bruta dá 7:
     [2],[2],[1],[5],[3],[2,2],[2,2,3])
    """
    MOD = 999999937
    n = len(A)
    dp = [0] * (n + 1)
    dp[0] = 1
    for a in A:
        divs = []
        i = 1
        while i * i <= a:
            if a % i == 0:
                divs.append(i)
                if i != a // i:
                    divs.append(a // i)
            i += 1
        for d in sorted(divs, reverse=True):     # decrescente: não reutiliza o mesmo a
            if d <= n:
                dp[d] = (dp[d] + dp[d - 1]) % MOD
    return sum(dp[1:]) % MOD


def q46_eh_caminho(adj: list[list[int]], path: list[int]) -> tuple[bool, bool]:
    """
    [Q46 ★] Verificar caminho e caminho simples — FONTE: Slides 08/09 (Exercício 4)
    Tema: definições de caminho

    Retorne (eh_caminho, eh_simples). path precisa ter pelo menos 2 vértices e
    cada par consecutivo precisa ser uma aresta (u -> v em adj). Se não for
    caminho, retorne (False, False). Simples = sem vértices repetidos.

    Complexidade esperada: O(len(path) + E) com lista de adjacência.
    """
    if len(path) < 2:
        return (False, False)
    vizinhos = [set(l) for l in adj]
    for u, v in zip(path, path[1:]):
        if v not in vizinhos[u]:
            return (False, False)
    return (True, len(set(path)) == len(path))


def q47_biblioteca_pico(intervals: list[tuple[int, int]]) -> tuple[int, tuple[int, int]]:
    """
    [Q47 ★] Biblioteca de Alexandria (período de pico) — FONTE: Lista 2, Questão 1 (≈ CSES 1619)
    Tema: varredura de eventos (conteúdo da A1)

    Tempos todos distintos. Retorne (k, (u, v)): k = máximo de pessoas ao mesmo
    tempo e (u, v) o intervalo de pico de MAIOR comprimento (empate: menor u).

    Complexidade esperada: O(n log n).

    Exemplos: [(5,8),(2,4),(3,9)] -> (2, (5,8)) ; [(5,8),(2,6),(3,9)] -> (3, (5,6))
    """
    ev = sorted([(a, 1) for a, _ in intervals] + [(b, -1) for _, b in intervals])
    k, atual = 0, 0
    melhor = None
    for i, (t, d) in enumerate(ev):
        atual += d
        if d == 1 and i + 1 < len(ev):
            u, v = t, ev[i + 1][0]
            if atual > k:
                k, melhor = atual, (u, v)
            elif atual == k and (v - u > melhor[1] - melhor[0]):
                melhor = (u, v)
    return k, melhor


def q48_sisi_sorvete(A: list[int]) -> int:
    """
    [Q48 ★] Sisi e a sorveteria — FONTE: Lista 2, Questão 2 (≈ CSES 1141 "Playlist")
    Tema: janela deslizante / dois ponteiros (conteúdo da A1)

    Retorne o tamanho do maior trecho contíguo sem valores repetidos.

    Complexidade esperada: O(n).

    Exemplos: [1,2,1,4] -> 3 ; [11,22,11,33,22,77,44,22] -> 5 ; [3,3,3,3,3,3] -> 1
    """
    ultimo = {}
    ini = melhor = 0
    for i, x in enumerate(A):
        if x in ultimo and ultimo[x] >= ini:
            ini = ultimo[x] + 1
        ultimo[x] = i
        melhor = max(melhor, i - ini + 1)
    return melhor


def q49_hotel_hilbert(guests: list[tuple[int, int]]) -> tuple[int, list[int]]:
    """
    [Q49 ★] Hotel de Hilbert — FONTE: Lista 2, Questão 3 (≈ CSES 1164 "Room Allocation")
    Tema: guloso + heap (conteúdo da A1; mesma ideia da Q21)

    Hóspede i = (chegada, partida). Dois hóspedes dividem um quarto se a partida
    de um for ESTRITAMENTE menor que a chegada do outro. Retorne (k, quartos)
    com k mínimo e quartos[i] em 1..k (qualquer distribuição válida).

    Complexidade esperada: O(n log n).
    """
    ordem = sorted(range(len(guests)), key=lambda i: guests[i][0])
    livres = []            # heap de (partida, quarto)
    quarto = [0] * len(guests)
    k = 0
    for i in ordem:
        a, b = guests[i]
        if livres and livres[0][0] < a:
            _, r = heapq.heappop(livres)
        else:
            k += 1
            r = k
        quarto[i] = r
        heapq.heappush(livres, (b, r))
    return k, quarto


def q50_quadra(A: list[int], k: int) -> tuple[int, int, int, int]:
    """
    [Q50 ★] Quadra — FONTE: Lista 2, Questão 4 (≈ CSES 1642)
    Tema: soma de pares + hashing (conteúdo da A1)

    Retorne (a, b, c, d) 1-indexados com a < b < c < d e A_a+A_b+A_c+A_d = k,
    ou (-1, -1, -1, -1).

    Complexidade esperada: O(n²) com dicionário (O(n² log n) com ordenação).
    """
    n = len(A)
    pares = {}
    for j in range(n):
        for l in range(j + 1, n):         # (j, l) é o par da direita
            alvo = k - A[j] - A[l]
            if alvo in pares:
                a, b = pares[alvo]
                return tuple(sorted((a + 1, b + 1, j + 1, l + 1)))
        for i in range(j):                # adiciona pares (i, j) com i < j
            pares.setdefault(A[i] + A[j], (i, j))
    return (-1, -1, -1, -1)


def q51_torres_blocos(A: list[int]) -> int:
    """
    [Q51 ★] Os blocos (torres) — FONTE: Lista 2, Questão 5 (≈ CSES 1073 "Towers")
    Tema: guloso + busca binária (relação com maior subsequência crescente)

    Um bloco só pode ir em cima de outro de tamanho >= ao dele; blocos chegam em
    ordem. Retorne o número mínimo de torres.

    Complexidade esperada: O(n log n).

    Exemplos: [1,2,1,4] -> 3 ; [11,22,11,33,22,77,44,22] -> 4 ; [3,3,3,3,3,3] -> 1
    """
    topos = []                 # sempre ordenado crescente
    for x in A:
        i = bisect.bisect_left(topos, x)     # menor topo >= x
        if i == len(topos):
            topos.append(x)
        else:
            topos[i] = x
    return len(topos)


def q52_sistema_planetario(A: list[int], k: int) -> int:
    """
    [Q52 ★] O grande sistema planetário — FONTE: Lista 2, Questão 6 (≈ CSES 1620 "Factory Machines")
    Tema: busca binária na resposta (conteúdo da A1)

    Retorne o menor inteiro T tal que sum(T // A_i) >= k.

    Complexidade esperada: O(n log M).

    Exemplos: ([3,2,6], 7) -> 8 ; ([3,2,6,5,8,2,1], 1234) -> 438
    """
    lo, hi = 0, min(A) * k
    while lo < hi:
        mid = (lo + hi) // 2
        if sum(mid // a for a in A) >= k:
            hi = mid
        else:
            lo = mid + 1
    return lo


def q53_otimizacao(A: list[int]) -> int:
    """
    [Q53 ★] Otimização (minimizar soma de |A_i - k|) — FONTE: Lista 2, Questão 7 (≈ CSES 1074 "Stick Lengths")
    Tema: mediana / seleção em tempo linear (conteúdo da A1)

    Retorne o MENOR k que minimiza sum(|A_i - k|).

    Complexidade esperada: O(n) com quickselect.
    """
    import random

    def select(L, i):              # i-ésimo menor (0-indexado), esperado O(n)
        while True:
            p = random.choice(L)
            menores = [x for x in L if x < p]
            iguais = [x for x in L if x == p]
            if i < len(menores):
                L = menores
            elif i < len(menores) + len(iguais):
                return p
            else:
                i -= len(menores) + len(iguais)
                L = [x for x in L if x > p]

    return select(list(A), (len(A) - 1) // 2)
