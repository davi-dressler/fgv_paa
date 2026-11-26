"""
PAA 2025.2 — Implementações de referência dos algoritmos da A2 (slides 07 a 13)
Somente biblioteca padrão do Python (nada de pip install).

Convenções usadas em todo o arquivo
-----------------------------------
- Vértices numerados de 0 a n-1.
- Lista de adjacência:  adj[u] = [v1, v2, ...]            (grafo sem peso)
                        adj[u] = [(v1, w1), (v2, w2), ...] (grafo ponderado)
- Lista de arestas:     edges = [(u, v), ...] ou [(u, v, w), ...]
- INF = float('inf') representa "sem caminho".

Cada bloco entre "# >>> nome" e "# <<<" é exibido no guia HTML.
"""
import heapq
from collections import deque
from math import sqrt, inf

INF = inf


# >>> representacoes
def matriz_adjacencia(n, edges, dirigido=False):
    """Espaço Θ(V²). Testar aresta: Θ(1). Varrer vizinhos de u: Θ(V)."""
    A = [[0] * n for _ in range(n)]
    for u, v in edges:
        A[u][v] = 1
        if not dirigido:
            A[v][u] = 1
    return A


def lista_adjacencia(n, edges, dirigido=False):
    """Espaço Θ(V + E). Varrer vizinhos de u: Θ(g(u)). Testar aresta: O(g(u))."""
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
        if not dirigido:
            adj[v].append(u)
    return adj
# <<<


# >>> dfs
def dfs(n, adj):
    """
    Busca em profundidade em TODO o grafo (floresta DFS).
    Devolve pré-ordem (descoberta), pós-ordem (exaustão) e vetor de pais.
    Θ(V + E) com lista de adjacência; Θ(V²) com matriz.
    """
    pre = [-1] * n
    post = [-1] * n
    parent = [-1] * n
    cont = {"pre": 0, "post": 0}

    def visita(u):
        pre[u] = cont["pre"]; cont["pre"] += 1
        for v in adj[u]:
            if pre[v] == -1:          # v ainda não descoberto -> aresta de árvore
                parent[v] = u
                visita(v)
        post[u] = cont["post"]; cont["post"] += 1   # u exaurido

    for s in range(n):                # tenta a partir de cada vértice (grafo pode ser desconexo)
        if pre[s] == -1:
            parent[s] = s             # raiz de uma árvore da floresta
            visita(s)
    return pre, post, parent
# <<<


# >>> dfs_iterativa
def dfs_iterativa(n, adj, s):
    """Mesma ideia sem recursão (evita estourar a pilha do Python em grafos grandes)."""
    visitado = [False] * n
    ordem = []
    pilha = [s]
    while pilha:
        u = pilha.pop()
        if visitado[u]:
            continue
        visitado[u] = True
        ordem.append(u)
        for v in reversed(adj[u]):    # reversed: mesma ordem da versão recursiva
            if not visitado[v]:
                pilha.append(v)
    return ordem
# <<<


# >>> dfs_iterativa_pre_pos
def dfs_iterativa_pre_pos(n, adj):
    """
    DFS SEM recursão que calcula pré-ordem, pós-ordem e a floresta DFS.

    Truque: a pilha guarda (vértice, índice do próximo vizinho a examinar).
    - Ao DESCOBRIR v: recebe a pré-ordem e entra na pilha com índice 0.
    - O topo examina UM vizinho por vez (avança o índice).
    - Quando o índice passa do último vizinho, o vértice está EXAURIDO:
      sai da pilha e recebe a pós-ordem.
    Visita na mesma ordem da versão recursiva. Θ(V + E).

    Por que a dfs_iterativa acima não serve para pós-ordem? Ela empilha todos
    os vizinhos de uma vez e "esquece" u logo depois: não há um momento em que
    se saiba que u terminou.
    """
    pre = [-1] * n
    post = [-1] * n
    parent = [-1] * n
    cont_pre = cont_post = 0

    for s in range(n):                        # floresta: tenta cada vértice
        if pre[s] != -1:
            continue
        parent[s] = s
        pre[s] = cont_pre; cont_pre += 1      # s descoberto
        pilha = [(s, 0)]
        while pilha:
            u, i = pilha[-1]                  # olha o topo (sem tirar)
            if i < len(adj[u]):
                pilha[-1] = (u, i + 1)        # da próxima vez, o vizinho seguinte
                v = adj[u][i]
                if pre[v] == -1:              # v não descoberto -> desce
                    parent[v] = u
                    pre[v] = cont_pre; cont_pre += 1
                    pilha.append((v, 0))
            else:                             # todos os vizinhos de u examinados
                pilha.pop()
                post[u] = cont_post; cont_post += 1   # u exaurido
    return pre, post, parent
# <<<


# >>> classificar_arestas_iterativa
def classificar_arestas_iterativa(n, adj):
    """
    Classificação ON-THE-FLY das arestas de um grafo DIRIGIDO, sem recursão.
    É a dfs_iterativa_pre_pos + uma decisão no momento em que (u, v) é examinada:

      pre[v] == -1                  -> árvore  (v ainda não descoberto)
      pre[v] != -1 e post[v] == -1  -> retorno (v descoberto, NÃO exaurido:
                                                 está na pilha, é ancestral de u)
      post[v] != -1 e pre[u] < pre[v] -> avanço  (v exaurido, descendente de u)
      post[v] != -1 e pre[v] < pre[u] -> cruzada (v exaurido, primo mais velho)

    Existe aresta de retorno <=> o grafo tem ciclo. Θ(V + E).
    """
    pre = [-1] * n
    post = [-1] * n
    tipo = {}
    cont_pre = cont_post = 0

    for s in range(n):
        if pre[s] != -1:
            continue
        pre[s] = cont_pre; cont_pre += 1
        pilha = [(s, 0)]
        while pilha:
            u, i = pilha[-1]
            if i < len(adj[u]):
                pilha[-1] = (u, i + 1)
                v = adj[u][i]
                if pre[v] == -1:
                    tipo[(u, v)] = "arvore"
                    pre[v] = cont_pre; cont_pre += 1
                    pilha.append((v, 0))
                elif post[v] == -1:
                    tipo[(u, v)] = "retorno"
                elif pre[u] < pre[v]:
                    tipo[(u, v)] = "avanco"
                else:
                    tipo[(u, v)] = "cruzada"
            else:
                pilha.pop()
                post[u] = cont_post; cont_post += 1
    return tipo


# Exemplo (o mesmo grafo do slide, 0-indexado):
#   adj = [[1, 2], [3, 4], [4], [4], [5, 1], []]
#   dfs_iterativa_pre_pos(6, adj)
#     pre  = [0, 1, 5, 2, 3, 4]      post = [5, 3, 4, 2, 1, 0]
#   classificar_arestas_iterativa(6, adj)
#     {(0,1):'arvore', (1,3):'arvore', (3,4):'arvore', (4,5):'arvore',
#      (4,1):'retorno', (1,4):'avanco', (0,2):'arvore', (2,4):'cruzada'}
# <<<


# >>> classificar_arestas
def classificar_arestas(n, adj):
    """
    Classifica cada aresta (u, v) de um grafo DIRIGIDO durante a DFS ("on-the-fly"):
      - árvore : v ainda não descoberto
      - retorno: v descoberto mas não exaurido (v é ancestral de u)  -> CICLO
      - avanço : v exaurido e pre[u] < pre[v]   (v é descendente de u)
      - cruzada: v exaurido e pre[v] < pre[u]   (v é primo mais velho)
    Θ(V + E).
    """
    pre = [-1] * n
    post = [-1] * n
    tipo = {}
    cont = [0, 0]

    def visita(u):
        pre[u] = cont[0]; cont[0] += 1
        for v in adj[u]:
            if pre[v] == -1:
                tipo[(u, v)] = "arvore"
                visita(v)
            elif post[v] == -1:
                tipo[(u, v)] = "retorno"
            elif pre[u] < pre[v]:
                tipo[(u, v)] = "avanco"
            else:
                tipo[(u, v)] = "cruzada"
        post[u] = cont[1]; cont[1] += 1

    for s in range(n):
        if pre[s] == -1:
            visita(s)
    return tipo
# <<<


# >>> tem_ciclo
def tem_ciclo_dirigido(n, adj):
    """
    Um grafo dirigido tem ciclo  <=>  a DFS encontra uma aresta de RETORNO.
    Cores: 0 = branco (não descoberto), 1 = cinza (na pilha), 2 = preto (exaurido).
    Θ(V + E).
    """
    cor = [0] * n

    def visita(u):
        cor[u] = 1
        for v in adj[u]:
            if cor[v] == 1:           # aresta de retorno
                return True
            if cor[v] == 0 and visita(v):
                return True
        cor[u] = 2
        return False

    return any(cor[s] == 0 and visita(s) for s in range(n))


def tem_ciclo_nao_dirigido(n, adj):
    """Em grafo NÃO dirigido: ciclo <=> achar vizinho já visitado que não é o pai."""
    visitado = [False] * n
    for s in range(n):
        if visitado[s]:
            continue
        visitado[s] = True
        pilha = [(s, -1)]
        while pilha:
            u, pai = pilha.pop()
            for v in adj[u]:
                if not visitado[v]:
                    visitado[v] = True
                    pilha.append((v, u))
                elif v != pai:
                    return True
    return False
# <<<


# >>> topologica
def ordem_topologica(n, adj):
    """
    Algoritmo de Kahn (o do slide): remove fontes (grau de entrada 0) repetidamente.
    Se sobrar vértice sem ser numerado, há ciclo -> não existe ordem topológica.
    Θ(V + E).
    """
    grau_ent = [0] * n
    for u in range(n):
        for v in adj[u]:
            grau_ent[v] += 1
    fila = deque(u for u in range(n) if grau_ent[u] == 0)
    ordem = []
    while fila:
        u = fila.popleft()
        ordem.append(u)
        for v in adj[u]:
            grau_ent[v] -= 1          # "remove" a aresta (u, v)
            if grau_ent[v] == 0:
                fila.append(v)
    return ordem if len(ordem) == n else None


def ordem_topologica_dfs(n, adj):
    """Alternativa: ordem topológica = pós-ordem da DFS invertida (supondo DAG)."""
    pre, post, _ = dfs(n, adj)
    return sorted(range(n), key=lambda v: -post[v])
# <<<


# >>> bfs
def bfs(n, adj, s):
    """
    Busca em largura a partir de s. Percorre por camadas usando uma FILA.
    dist[v] = nº mínimo de arestas de s até v (-1 se inalcançável).
    parent define a árvore de caminhos mais curtos (SPT). Θ(V + E).
    """
    dist = [-1] * n
    parent = [-1] * n
    dist[s] = 0
    parent[s] = s
    fila = deque([s])
    while fila:
        u = fila.popleft()
        for v in adj[u]:
            if dist[v] == -1:         # cada vértice entra na fila UMA vez
                dist[v] = dist[u] + 1
                parent[v] = u
                fila.append(v)
    return dist, parent


def reconstruir_caminho(parent, s, t):
    """Sobe pelo vetor de pais de t até s. O(V)."""
    if parent[t] == -1:
        return None
    caminho = [t]
    while t != s:
        t = parent[t]
        caminho.append(t)
    return caminho[::-1]
# <<<


# >>> componentes
def componentes_conexas(n, adj):
    """Rótulo de componente para cada vértice (grafo não dirigido). Θ(V + E)."""
    comp = [-1] * n
    c = 0
    for s in range(n):
        if comp[s] != -1:
            continue
        comp[s] = c
        fila = deque([s])
        while fila:
            u = fila.popleft()
            for v in adj[u]:
                if comp[v] == -1:
                    comp[v] = c
                    fila.append(v)
        c += 1
    return c, comp


def bipartido(n, adj):
    """2-coloração com BFS: bipartido <=> não existe ciclo ímpar. Θ(V + E)."""
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
# <<<


# >>> ponte
def eh_ponte(n, adj, a, b):
    """
    (Simulado A2) A aresta (a, b) é ponte <=> sem ela, b não é alcançável a partir de a.
    Uma BFS que ignora a aresta (a, b): Θ(V + E).
    """
    visitado = [False] * n
    visitado[a] = True
    fila = deque([a])
    while fila:
        u = fila.popleft()
        for v in adj[u]:
            if (u, v) in ((a, b), (b, a)):   # pula a aresta removida
                continue
            if not visitado[v]:
                visitado[v] = True
                fila.append(v)
    return not visitado[b]


def todas_as_pontes(n, adj):
    """
    Tarjan: low[u] = menor pré-ordem alcançável a partir da subárvore de u usando
    no máximo UMA aresta de retorno. (u, v) de árvore é ponte <=> low[v] > pre[u].
    Θ(V + E).  (Iterativo para não estourar recursão.)
    """
    pre = [-1] * n
    low = [0] * n
    pontes = []
    t = 0
    for s in range(n):
        if pre[s] != -1:
            continue
        pre[s] = low[s] = t; t += 1
        pilha = [(s, -1, iter(adj[s]))]
        while pilha:
            u, pai, it = pilha[-1]
            avancou = False
            for v in it:
                if v == pai:
                    pai = -2                  # ignora UMA vez a aresta para o pai
                    pilha[-1] = (u, pai, it)
                    continue
                if pre[v] == -1:
                    pre[v] = low[v] = t; t += 1
                    pilha.append((v, u, iter(adj[v])))
                    avancou = True
                    break
                low[u] = min(low[u], pre[v])  # aresta de retorno
            if not avancou:
                pilha.pop()
                if pilha:
                    p = pilha[-1][0]
                    low[p] = min(low[p], low[u])
                    if low[u] > pre[p]:
                        pontes.append((p, u))
    return pontes
# <<<


# >>> dag_spt
def menor_caminho_dag(n, adj, s, ordem):
    """
    Caminho mais barato em DAG: relaxa as arestas seguindo a ORDEM TOPOLÓGICA.
    Quando u é processado, d[u] já é final (todos que apontam para u vieram antes).
    Funciona com pesos negativos (DAG não tem ciclo). Θ(V + E).
    """
    d = [INF] * n
    parent = [-1] * n
    d[s] = 0
    parent[s] = s
    for u in ordem:
        if d[u] == INF:
            continue
        for v, w in adj[u]:
            if d[u] + w < d[v]:       # relaxamento
                d[v] = d[u] + w
                parent[v] = u
    return d, parent
# <<<


# >>> dijkstra_lento
def dijkstra_lento(n, adj, s):
    """
    Dijkstra "array" (versão do slide cptDijkstraSlow): a cada passo procura
    linearmente o vértice não verificado de menor distância.
    Θ(V² + E) = Θ(V²)  -> melhor escolha para grafos DENSOS.
    """
    d = [INF] * n
    parent = [-1] * n
    verificado = [False] * n
    d[s] = 0
    parent[s] = s
    for _ in range(n):
        u = -1
        for v in range(n):                      # O(V) por iteração
            if not verificado[v] and (u == -1 or d[v] < d[u]):
                u = v
        if u == -1 or d[u] == INF:
            break
        verificado[u] = True
        for v, w in adj[u]:
            if not verificado[v] and d[u] + w < d[v]:
                d[v] = d[u] + w
                parent[v] = u
    return d, parent
# <<<


# >>> dijkstra
def dijkstra(n, adj, s):
    """
    Dijkstra com heap mínimo (heapq). Exige pesos >= 0.
    heapq não tem "decrease-key": inserimos de novo e ignoramos entradas velhas.
    O((V + E) log V).
    """
    d = [INF] * n
    parent = [-1] * n
    d[s] = 0
    parent[s] = s
    heap = [(0, s)]
    while heap:
        du, u = heapq.heappop(heap)
        if du > d[u]:                 # entrada desatualizada ("lazy deletion")
            continue
        for v, w in adj[u]:
            if du + w < d[v]:         # relaxamento
                d[v] = du + w
                parent[v] = u
                heapq.heappush(heap, (d[v], v))
    return d, parent
# <<<


# >>> bellman_ford
def bellman_ford(n, edges, s):
    """
    Bellman-Ford: relaxa TODAS as arestas V-1 vezes. Aceita pesos negativos.
    Depois de i rodadas, d[v] <= custo do melhor caminho com até i arestas.
    Se a V-ésima rodada ainda melhora algo -> ciclo negativo alcançável.
    Devolve (sucesso, d, parent). Θ(V·E).
    """
    d = [INF] * n
    parent = [-1] * n
    d[s] = 0
    parent[s] = s
    for _ in range(n - 1):
        mudou = False
        for u, v, w in edges:
            if d[u] != INF and d[u] + w < d[v]:
                d[v] = d[u] + w
                parent[v] = u
                mudou = True
        if not mudou:                 # otimização: parada antecipada
            break
    for u, v, w in edges:             # rodada extra = detector de ciclo negativo
        if d[u] != INF and d[u] + w < d[v]:
            return False, d, parent
    return True, d, parent
# <<<


# >>> union_find
class UnionFind:
    """
    Union-Find (conjuntos disjuntos) com união por tamanho + compressão de caminho.
    Com só união por tamanho (versão do slide): find O(log n).
    Com as duas otimizações: custo amortizado quase constante (α(n)).
    """
    def __init__(self, n):
        self.pai = list(range(n))
        self.tam = [1] * n

    def find(self, x):
        raiz = x
        while raiz != self.pai[raiz]:
            raiz = self.pai[raiz]
        while x != raiz:              # compressão de caminho
            self.pai[x], x = raiz, self.pai[x]
        return raiz

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False              # já estavam no mesmo conjunto (formaria ciclo)
        if self.tam[ra] < self.tam[rb]:
            ra, rb = rb, ra
        self.pai[rb] = ra             # menor pendurado no maior
        self.tam[ra] += self.tam[rb]
        return True
# <<<


# >>> kruskal
def kruskal(n, edges):
    """
    Kruskal: ordena as arestas por custo e adiciona cada uma que NÃO forma ciclo
    (líderes diferentes no union-find). Cresce uma FLORESTA até virar árvore.
    O(E log E) = O(E log V).  Devolve (custo, arestas) ou None se desconexo.
    """
    uf = UnionFind(n)
    custo, mst = 0, []
    for u, v, w in sorted(edges, key=lambda e: e[2]):
        if uf.union(u, v):
            custo += w
            mst.append((u, v, w))
            if len(mst) == n - 1:
                break
    return (custo, mst) if len(mst) == n - 1 else None
# <<<


# >>> prim
def prim(n, adj, raiz=0):
    """
    Prim com heap: cresce UMA árvore a partir da raiz; a cada passo adiciona o
    vértice da fronteira ligado à árvore pela aresta mais barata da franja.
    O((V + E) log V).  Devolve (custo, parent) ou None se desconexo.
    """
    custo_v = [INF] * n
    parent = [-1] * n
    na_arvore = [False] * n
    custo_v[raiz] = 0
    parent[raiz] = raiz
    heap = [(0, raiz)]
    total = 0
    while heap:
        c, u = heapq.heappop(heap)
        if na_arvore[u]:
            continue
        na_arvore[u] = True
        total += c
        for v, w in adj[u]:
            if not na_arvore[v] and w < custo_v[v]:   # diferença p/ Dijkstra: compara só w
                custo_v[v] = w
                parent[v] = u
                heapq.heappush(heap, (w, v))
    return (total, parent) if all(na_arvore) else None


def prim_denso(n, W):
    """Prim com vetor (W = matriz de custos, INF = sem aresta). Θ(V²): ideal p/ grafo denso."""
    custo_v = [INF] * n
    na_arvore = [False] * n
    custo_v[0] = 0
    total = 0
    for _ in range(n):
        u = min((v for v in range(n) if not na_arvore[v]), key=lambda v: custo_v[v])
        if custo_v[u] == INF:
            return None
        na_arvore[u] = True
        total += custo_v[u]
        for v in range(n):
            if not na_arvore[v] and W[u][v] < custo_v[v]:
                custo_v[v] = W[u][v]
    return total
# <<<


# >>> edmonds_karp
def fluxo_maximo(n, arestas, s, t):
    """
    Ford-Fulkerson com busca em LARGURA (Edmonds-Karp).
    Cada aresta original (u, v, c) ganha uma aresta "virtual" (v, u, 0) — a reversa.
    Capacidade residual de uma aresta = cap - fluxo. Empurrar δ numa aresta
    tira δ da sua reversa (é isso que permite "desfazer" fluxo).
    O(V · E²).  Devolve (valor do fluxo, grafo residual).
    """
    # grafo residual: g[u] = lista de [v, capacidade, índice da reversa em g[v]]
    g = [[] for _ in range(n)]
    for u, v, c in arestas:
        g[u].append([v, c, len(g[v])])
        g[v].append([u, 0, len(g[u]) - 1])

    total = 0
    while True:
        # BFS procurando caminho aumentador (o MENOR em nº de arestas)
        pai = [None] * n              # pai[v] = (u, índice da aresta em g[u])
        pai[s] = (s, -1)
        fila = deque([s])
        while fila and pai[t] is None:
            u = fila.popleft()
            for i, (v, cap, _) in enumerate(g[u]):
                if cap > 0 and pai[v] is None:
                    pai[v] = (u, i)
                    fila.append(v)
        if pai[t] is None:            # não há caminho aumentador -> fluxo máximo
            return total, g
        # capacidade residual δ do caminho = menor residual nas arestas
        delta = INF
        v = t
        while v != s:
            u, i = pai[v]
            delta = min(delta, g[u][i][1])
            v = u
        # empurra δ: direta perde δ de residual, reversa ganha δ
        v = t
        while v != s:
            u, i = pai[v]
            g[u][i][1] -= delta
            rev = g[u][i][2]
            g[v][rev][1] += delta
            v = u
        total += delta
# <<<


# >>> corte_minimo
def corte_minimo(n, arestas, s, t):
    """
    Teorema fluxo-máximo / corte-mínimo: depois do fluxo máximo, S = vértices
    alcançáveis a partir de s no grafo RESIDUAL. As arestas originais que saem
    de S para fora formam um corte mínimo e a soma das capacidades = fluxo máximo.
    """
    valor, g = fluxo_maximo(n, arestas, s, t)
    alcancavel = [False] * n
    alcancavel[s] = True
    fila = deque([s])
    while fila:
        u = fila.popleft()
        for v, cap, _ in g[u]:
            if cap > 0 and not alcancavel[v]:
                alcancavel[v] = True
                fila.append(v)
    corte = [(u, v, c) for u, v, c in arestas if alcancavel[u] and not alcancavel[v]]
    return valor, corte
# <<<


# >>> par_mais_proximo
def par_mais_proximo(pontos):
    """
    Dividir e conquistar (slides 07 / sua AS). Ordena por x uma vez; cada chamada
    devolve a lista ordenada por y (merge), evitando reordenar: T(n) = 2T(n/2) + O(n)
    = Θ(n log n).
    """
    def dist(p, q):
        return sqrt((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2)

    def rec(px):                      # px ordenado por x; devolve (d, py)
        n = len(px)
        if n <= 3:
            d = min((dist(px[i], px[j]) for i in range(n) for j in range(i + 1, n)),
                    default=INF)
            return d, sorted(px, key=lambda p: p[1])
        m = n // 2
        xm = px[m][0]
        dl, ly = rec(px[:m])
        dr, ry = rec(px[m:])
        d = min(dl, dr)
        py, i, j = [], 0, 0           # merge por y: O(n)
        while i < len(ly) or j < len(ry):
            if j == len(ry) or (i < len(ly) and ly[i][1] <= ry[j][1]):
                py.append(ly[i]); i += 1
            else:
                py.append(ry[j]); j += 1
        faixa = [p for p in py if abs(p[0] - xm) < d]
        for i in range(len(faixa)):   # cada ponto compara com no máx. 7 seguintes
            for j in range(i + 1, min(i + 8, len(faixa))):
                if faixa[j][1] - faixa[i][1] >= d:
                    break
                d = min(d, dist(faixa[i], faixa[j]))
        return d, py

    return rec(sorted(pontos))[0]
# <<<


# >>> inversoes
def contar_inversoes(A):
    """Merge sort contando inversões entre metades. Θ(n log n)."""
    if len(A) <= 1:
        return 0, list(A)
    m = len(A) // 2
    il, L = contar_inversoes(A[:m])
    ir, R = contar_inversoes(A[m:])
    res, i, j, inv = [], 0, 0, 0
    while i < len(L) and j < len(R):
        if L[i] <= R[j]:
            res.append(L[i]); i += 1
        else:
            res.append(R[j]); j += 1
            inv += len(L) - i         # R[j] é menor que todos os L[i:] restantes
    res += L[i:] + R[j:]
    return il + ir + inv, res
# <<<


# >>> guloso_intervalos
def max_tarefas_compativeis(tarefas):
    """Guloso (slide 07): ordena por TÉRMINO e pega cada tarefa compatível. Θ(n log n)."""
    escolhidas, fim = [], -INF
    for ini, f in sorted(tarefas, key=lambda t: t[1]):
        if ini >= fim:
            escolhidas.append((ini, f))
            fim = f
    return escolhidas


def mochila_fracionaria(itens, W):
    """Guloso por razão valor/peso. itens = [(peso, valor)]. Θ(n log n)."""
    total = 0.0
    for w, v in sorted(itens, key=lambda it: it[1] / it[0], reverse=True):
        if W <= 0:
            break
        pega = min(w, W)
        total += v * pega / w
        W -= pega
    return total
# <<<


# >>> mochila01
def mochila01(pesos, valores, W):
    """
    PD bottom-up: M[j][c] = melhor valor usando os j primeiros itens com capacidade c.
    M[j][c] = max(M[j-1][c], v_j + M[j-1][c - w_j])  (se w_j <= c)
    Θ(nW) — PSEUDO-polinomial (W é um valor, ocupa log W bits).
    """
    n = len(pesos)
    M = [[0] * (W + 1) for _ in range(n + 1)]
    for j in range(1, n + 1):
        w, v = pesos[j - 1], valores[j - 1]
        for c in range(W + 1):
            M[j][c] = M[j - 1][c]
            if w <= c:
                M[j][c] = max(M[j][c], v + M[j - 1][c - w])
    # reconstrução: anda de trás para frente
    itens, c = [], W
    for j in range(n, 0, -1):
        if M[j][c] != M[j - 1][c]:
            itens.append(j - 1)
            c -= pesos[j - 1]
    return M[n][W], itens[::-1]
# <<<


# >>> troco
def troco_minimo(moedas, valor):
    """
    (A2 2025.2, Q3) PD: dp[x] = menor nº de moedas para formar x.
    dp[x] = 1 + min(dp[x - m]) para toda moeda m <= x.
    Guloso só funciona em sistema canônico: moedas [1,5,6,9], valor 11 ->
    guloso dá 9+1+1 (3 moedas), ótimo é 5+6 (2 moedas).
    Θ(valor · nº de moedas) — pseudo-polinomial.
    """
    dp = [0] + [INF] * valor
    escolha = [-1] * (valor + 1)
    for x in range(1, valor + 1):
        for m in moedas:
            if m <= x and dp[x - m] + 1 < dp[x]:
                dp[x] = dp[x - m] + 1
                escolha[x] = m
    if dp[valor] == INF:
        return -1
    usadas = []
    while valor > 0:
        usadas.append(escolha[valor])
        valor -= escolha[valor]
    return sorted(usadas)
# <<<


# >>> intervalos_ponderados
def agendamento_ponderado(tarefas):
    """
    (Simulado A2, Q3) tarefas = [(inicio, fim, valor)].
    Ordena por fim; p(j) = última tarefa i < j com fim_i <= inicio_j (busca binária).
    dp[j] = max(dp[j-1], valor_j + dp[p(j)])     ->  Θ(n log n).
    """
    import bisect
    T = sorted(tarefas, key=lambda t: t[1])
    fins = [t[1] for t in T]
    n = len(T)
    dp = [0] * (n + 1)                 # dp[j] considera as j primeiras tarefas
    for j in range(1, n + 1):
        ini, fim, val = T[j - 1]
        p = bisect.bisect_right(fins, ini, 0, j - 1)   # nº de tarefas compatíveis antes
        dp[j] = max(dp[j - 1], val + dp[p])
    escolhidas, j = [], n               # reconstrução
    while j > 0:
        ini, fim, val = T[j - 1]
        p = bisect.bisect_right(fins, ini, 0, j - 1)
        if val + dp[p] >= dp[j - 1] and dp[j] == val + dp[p]:
            escolhidas.append(T[j - 1])
            j = p
        else:
            j -= 1
    return dp[n], escolhidas[::-1]
# <<<


# >>> lcs
def lcs(a, b):
    """Maior subsequência comum. m[i][j] usa prefixos a[:i], b[:j]. Θ(p·q)."""
    p, q = len(a), len(b)
    m = [[0] * (q + 1) for _ in range(p + 1)]
    for i in range(1, p + 1):
        for j in range(1, q + 1):
            if a[i - 1] == b[j - 1]:
                m[i][j] = m[i - 1][j - 1] + 1
            else:
                m[i][j] = max(m[i - 1][j], m[i][j - 1])
    return m[p][q]
# <<<


if __name__ == "__main__":
    # Pequena autoverificação
    E = [(0, 1), (0, 2), (1, 3), (1, 4), (2, 4), (3, 4), (4, 5), (4, 1)]
    adj = lista_adjacencia(6, E, dirigido=True)
    print("DFS pre/post:", dfs(6, adj)[:2])
    print("Classificação:", classificar_arestas(6, adj))
    print("Tem ciclo?", tem_ciclo_dirigido(6, adj))
    print("Topológica:", ordem_topologica(6, adj))
    print("BFS:", bfs(6, adj, 0))
    W = [(0, 1, 4), (0, 2, 1), (2, 1, 2), (1, 3, 1), (2, 3, 5)]
    adjw = [[] for _ in range(4)]
    for u, v, w in W:
        adjw[u].append((v, w))
    print("Dijkstra:", dijkstra(4, adjw, 0)[0], dijkstra_lento(4, adjw, 0)[0])
    print("Bellman-Ford:", bellman_ford(4, W, 0)[:2])
    und = [[] for _ in range(4)]
    for u, v, w in W:
        und[u].append((v, w)); und[v].append((u, w))
    print("Kruskal:", kruskal(4, W), "Prim:", prim(4, und)[0])
    print("Fluxo:", fluxo_maximo(4, W, 0, 3)[0], corte_minimo(4, W, 0, 3))
    print("Par mais próximo:", par_mais_proximo([(0, 0), (5, 5), (1, 1), (9, 0), (5, 6)]))
    print("Inversões:", contar_inversoes([3, 7, 2, 9, 5])[0])
    print("Mochila:", mochila01([1, 2, 5, 6, 7], [1, 6, 18, 22, 28], 11))
    print("Troco:", troco_minimo([1, 5, 6, 9], 11), troco_minimo([2], 3))
    print("Ponderado:", agendamento_ponderado([(1, 3, 50), (4, 6, 30), (7, 9, 30), (2, 5, 20), (5, 7, 40), (6, 8, 60)]))
    print("LCS:", lcs("ABCBDAB", "BDCABA"))
    g = lista_adjacencia(5, [(0, 1), (0, 3), (1, 2), (1, 4), (3, 4)])
    print("Pontes:", todas_as_pontes(5, g), eh_ponte(5, g, 1, 2), eh_ponte(5, g, 4, 3))
