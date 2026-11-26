"""
PAA 2025.2 — QUESTÕES PRÁTICAS (para você resolver)
===================================================
- Escreva sua solução no corpo de cada função (apague o `raise NotImplementedError`).
- NÃO mude o nome nem a assinatura das funções.
- Só biblioteca padrão; importe o que precisar. Nada de pip install.
- Funções/classes auxiliares: defina DENTRO da função da questão (como na prova).
- Para corrigir:   python testes.py          (todas)
                   python testes.py 1 4 17   (só algumas)
                   python testes.py --prioridade 3
- Prioridade: ★★★ alta (estilo da A2, cai com certeza)  ★★ média  ★ baixa/complementar.
"""
from __future__ import annotations

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

    Cada aresta (a, b, custo) é um segmento de rua de mão dupla entre os
    cruzamentos a e b; custo é o preço de adaptá-lo. Os cruzamentos são os
    números que aparecem nas arestas (não necessariamente 0..n-1).
    Retorne True se é possível escolher segmentos com custo total <= C de forma
    que todos os cruzamentos fiquem conectados usando só os segmentos escolhidos.

    Exemplo:
        edges = [(1,2,1),(1,4,2),(2,3,7),(2,5,1),(3,6,9),(4,5,3),
                 (4,7,2),(5,6,1),(5,8,2),(6,9,10),(7,8,1),(8,9,1)]
        C=16 -> True ;  C=21 -> True ;  C=10 -> False
    """
    # escreva sua solução aqui
    raise NotImplementedError


def q02_caminho_energia(edges: list[tuple[int, int, int]], origem: int, destino: int):
    """
    [Q02 ★★★] Caminho de menor saldo de bateria — FONTE: Prova A2 2025.2, Questão 2

    ADAPTAÇÃO: aqui cada tupla (a, b, consumo) é uma aresta DIRIGIDA a -> b
    (veja no guia por que a versão não-dirigida com pesos negativos é problemática).
    consumo < 0 significa recarga. É garantido que não há ciclos negativos.
    Retorne a lista de arestas [(a, b), ...] do caminho de origem até destino com
    menor consumo total, ou None se o destino for inalcançável.
    Se origem == destino, retorne [].

    Exemplo (versão dirigida do exemplo da prova):
        edges = [(3,2,2),(2,1,2),(1,4,-2),(4,7,2),(7,8,-2),(8,9,1),
                 (2,5,-3),(5,6,3),(5,8,5)]
        q02_caminho_energia(edges, 3, 9) -> [(3,2),(2,1),(1,4),(4,7),(7,8),(8,9)]
    """
    # escreva sua solução aqui
    raise NotImplementedError


def q03_troco_minimo(coins: list[int], value: int):
    """
    [Q03 ★★★] Troco com menor número de moedas — FONTE: Prova A2 2025.2, Questão 3

    Retorne a lista (ordenada crescente) de moedas que somam `value` usando a
    menor quantidade possível (cada denominação pode ser usada várias vezes),
    ou -1 se for impossível. value = 0 -> [].

    Exemplos:
        coins=[1,5,6,9], value=11 -> [5, 6]
        coins=[2],       value=3  -> -1
        coins=[1,2,5],   value=11 -> [1, 5, 5]
    """
    # escreva sua solução aqui
    raise NotImplementedError



def q04_rota_sensores(sensors: list[Sensor], s_i: int, s_f: int):
    """
    [Q04 ★★★] Rede de sensores (ida e volta) — FONTE: Simulado A2 2025.2, Questão 1

    O sensor A envia diretamente para B se dist(A, B) <= A.r (depende do raio
    de quem envia). Retorne a sequência de ids
    do caminho de menor distância de s_i até s_f seguida do caminho de menor
    distância de s_f de volta a s_i (sem repetir s_f), ou None se algum dos
    dois trechos não existir.

    Exemplo:
        sensors = [Sensor(0,0,0,30), Sensor(1,25,0,25), Sensor(2,50,0,30),
                   Sensor(3,15,20,35), Sensor(4,35,25,25), Sensor(5,75,10,15),
                   Sensor(6,70,20,20), Sensor(7,55,25,25)]
        q04_rota_sensores(sensors, 0, 5) -> [0, 1, 2, 5, 6, 7, 4, 3, 0]
    """
    # escreva sua solução aqui
    import heapq
    import math

    def calculate_dist(s1, s2):
        return math.sqrt((s1.x - s2.x)**2 + (s1.y - s2.y)**2)

    graph = {s.id: [] for s in sensors}

    for s1 in sensors:
        for s2 in sensors:
            if s1.id != s2.id:
                dist = calculate_dist(s1, s2)
                if dist <= s1.r:
                    graph[s1.id].append((s2.id, dist))

    def Djikstra(source, target):
        parents = [-1 for _ in range(len(graph))]
        distances = [float('inf') for _ in range(len(graph))]
        parents[source] = source
        distances[source] = 0

        heap = [(0, source)]

        while heap:
            d, v = heapq.heappop(heap)

            if d > distances[v]:
                continue

            if v == target:
                break
    
            for v_next, w in graph[v]:
                if d + w < distances[v_next]:
                    distances[v_next] = d + w
                    parents[v_next] = v
                    heapq.heappush(heap, (distances[v_next], v_next))

        if distances[target] == float('inf'): return None

        caminho = [target]
        while caminho[-1] != source:
            caminho.append(parents[caminho[-1]])

        return caminho[::-1]

    ida = Djikstra(s_i, s_f)
    if ida == None:
        return None
    volta = Djikstra(s_f, s_i)
    if volta == None:
        return None

    return ida + volta[1:]



    

if __name__ == "__main__":
    sensors = sensors = [Sensor(0,0,0,30), Sensor(1,25,0,25), Sensor(2,50,0,30),
                   Sensor(3,15,20,35), Sensor(4,35,25,25), Sensor(5,75,10,15),
                   Sensor(6,70,20,20), Sensor(7,55,25,25)]
    print(q04_rota_sensores(sensors, 0, 5))    

def q05_eh_ponte(graph: list[list[int]], n: int, vi: int, vj: int) -> bool:
    """
    [Q05 ★★★] A aresta é uma ponte? — FONTE: Simulado A2 2025.2, Questão 2(b)

    graph é a lista de adjacência de um grafo NÃO dirigido e conexo com
    vértices 0..n-1. Retorne True se remover a aresta (vi, vj) desconecta o grafo.
    O enunciado original exige O(V + E).

    Exemplo:
        edges = [(0,1),(0,3),(1,2),(1,4),(3,4)]  (n = 5)
        (1,2) -> True ; (4,3) -> False ; (0,1) -> False
    """
    # escreva sua solução aqui
    raise NotImplementedError


def q06_rota_alternativa(n: int, streets: list[tuple[int, int]],
                         queries: list[tuple[int, int]]) -> list[int]:
    """
    [Q06 ★★★] Rota alternativa após interditar uma rua — FONTE: Prova AS 2025.2, Questão 3

    Cruzamentos 0..n-1, ruas de mão dupla. Para cada consulta (a, b) (uma rua
    existente), retorne o número de ruas da menor rota de a até b SEM usar essa
    rua, ou -1 se não existir. O enunciado original exige O(m · (V + E)),
    com m = nº de consultas.

    Exemplo:
        n=5, streets=[(0,1),(1,2),(2,0),(2,3),(3,4)], queries=[(0,1),(2,3),(3,4)]
        -> [2, -1, -1]
    """
    # escreva sua solução aqui
    raise NotImplementedError


def q07_agendamento_tarefas(tasks: list[Task]) -> tuple[int, list[str]]:
    """
    [Q07 ★★★] Agendamento de tarefas com valor — FONTE: Simulado A2 2025.2, Questão 3

    Duas tarefas são compatíveis se uma termina antes ou exatamente quando a
    outra começa (end <= start). Retorne (valor_máximo, nomes das tarefas
    escolhidas) — a ordem dos nomes não importa.

    Exemplo:
        tasks = [Task(1,3,50,"A"), Task(4,6,30,"B"), Task(7,9,30,"C"),
                 Task(2,5,20,"D"), Task(5,7,40,"E"), Task(6,8,60,"F")]
        -> (140, ['A', 'B', 'F'])
    """
    # escreva sua solução aqui
    raise NotImplementedError


def q08_menores_custos(n: int, adj: list[list[tuple[int, int]]], s: int):
    """
    [Q08 ★★★] Menores custos a partir de uma origem — FONTE: Slides 10 (Menor caminho)

    adj[u] = [(v, w), ...] (grafo dirigido, w >= 0). Retorne (dist, parent):
      dist[v]   = custo do caminho mais barato de s a v (float('inf') se inalcançável)
      parent[v] = vértice anterior a v nesse caminho; parent[s] = s; -1 se inalcançável
    """
    # escreva sua solução aqui
    raise NotImplementedError


def q09_custos_com_negativos(n: int, edges: list[tuple[int, int, int]], s: int):
    """
    [Q09 ★★★] Menores custos com pesos negativos — FONTE: Slides 10 (Menor caminho)

    edges = [(u, v, w), ...] dirigidas, vértices 0..n-1. Retorne (ok, dist):
      ok = False se existe ciclo negativo ALCANÇÁVEL a partir de s (dist pode ser qualquer coisa);
      ok = True e dist[v] = menor custo (float('inf') se inalcançável) caso contrário.
    """
    # escreva sua solução aqui
    raise NotImplementedError


def q10_arvore_minima_arestas(n: int, edges: list[tuple[int, int, int]]):
    """
    [Q10 ★★★] Árvore geradora mínima (lista de arestas) — FONTE: Slides 11 (Árvore geradora mínima)

    Grafo não dirigido, vértices 0..n-1, edges = [(u, v, w), ...].
    Retorne (custo_total, lista_de_arestas_da_MST) com arestas no formato da
    entrada, ou None se o grafo for desconexo.
    """
    # escreva sua solução aqui
    raise NotImplementedError


def q11_arvore_minima_adjacencia(n: int, adj: list[list[tuple[int, int]]]):
    """
    [Q11 ★★★] Árvore geradora mínima (lista de adjacência) — FONTE: Slides 11 (Árvore geradora mínima)

    adj[u] = [(v, w), ...] de um grafo NÃO dirigido (cada aresta aparece nos
    dois sentidos). Retorne (custo_total, parent), com parent descrevendo a
    árvore enraizada no vértice 0: parent[0] = 0 e parent[v] = pai de v,
    ou None se o grafo for desconexo.
    """
    # escreva sua solução aqui
    raise NotImplementedError


def q12_fluxo_maximo(n: int, edges: list[tuple[int, int, int]], s: int, t: int) -> int:
    """
    [Q12 ★★★] Fluxo máximo — FONTE: Slides 12 (Fluxo máximo)

    edges = [(u, v, capacidade), ...] dirigidas, vértices 0..n-1 (pode haver
    arestas paralelas e antiparalelas). Retorne a intensidade do fluxo máximo de s a t.
    """
    # escreva sua solução aqui
    raise NotImplementedError


def q13_ordem_topologica(n: int, adj: list[list[int]]):
    """
    [Q13 ★★★] Ordem topológica — FONTE: Slides 09 (Busca em grafos)

    adj[u] = lista de vizinhos (grafo dirigido, vértices 0..n-1).
    Retorne uma lista com os vértices em ordem topológica (toda aresta u->v com
    u antes de v), ou None se o grafo tiver ciclo.
    """
    # escreva sua solução aqui
    raise NotImplementedError


def q14_viagem_cupom(n: int, routes: list[tuple[int, int, int]]) -> int:
    """
    [Q14 ★★★] Viagem intergaláctica com cupom — FONTE: Lista 3, Questão 6 (≈ CSES 1195 "Flight Discount")

    Planetas 1..n, rotas DIRIGIDAS (a, b, c). Exatamente uma rota do percurso
    pode ter o custo reduzido para c // 2. Retorne o menor custo de 1 até n
    (ou -1 se n for inalcançável).

    Exemplos:
        n=3, routes=[(1,2,3),(2,3,1),(1,3,7)] -> 2
        n=3, routes=[(1,2,3),(2,3,3),(1,3,7)] -> 3
    """
    # escreva sua solução aqui
    raise NotImplementedError


def q15_reparo_estradas(n: int, roads: list[tuple[int, int, int]]) -> int:
    """
    [Q15 ★★★] Reparo das estradas — FONTE: Lista 3, Questão 7 (≈ CSES 1675 "Road Reparation")

    Cidades 1..n, estradas bidirecionais (a, b, c), c >= 0. Retorne o custo
    mínimo para que todas as cidades fiquem conectadas, ou -1 se for impossível.

    Exemplos:
        n=5, [(1,2,3),(2,3,5),(2,4,2),(3,4,8),(5,1,7),(5,4,4)] -> 14
        n=5, [(1,2,3),(2,3,5),(2,4,2),(3,4,0),(5,1,7),(5,4,4)] -> 9
        n=2, [(1,2,0)] -> 0
    """
    # escreva sua solução aqui
    raise NotImplementedError


def q16_formas_zerar_jogo(n: int, transitions: list[tuple[int, int]]) -> int:
    """
    [Q16 ★★★] Quantas formas de zerar o jogo — FONTE: Lista 3, Questão 8 (≈ CSES 1681 "Game Routes")

    Estados 1..n, transições dirigidas (a, b), o grafo é acíclico. Retorne o
    número de caminhos distintos do estado 1 ao estado n (sem módulo).

    Exemplos:
        n=3, [(1,2),(2,3)] -> 1
        n=5, [(1,3),(3,4),(1,2),(2,5),(1,4),(4,5),(3,5)] -> 4
        n=3, [(1,2),(3,2)] -> 0
    """
    # escreva sua solução aqui
    raise NotImplementedError


def q17_escape_caverna(grid: list[str]) -> int:
    """
    [Q17 ★★★] Escape se for possível — FONTE: Lista 3, Questão 5 (≈ CSES 1194 "Monsters")

    grid é uma lista de strings com 'V' (você), 'A' (água), '.' (livre), '#' (parede).
    A cada instante a água se espalha para os vizinhos (4 direções) e você anda
    uma casa. Você só pode entrar numa casa no instante t se a água chegar nela
    estritamente depois de t. Escapar = estar numa casa da borda do grid.
    Retorne o menor número de movimentos para escapar, ou -1.

    Exemplos (ver testes): 5, -1 e 0.
    """
    # escreva sua solução aqui
    raise NotImplementedError


def q18_cavalo(n: int) -> list[list[int]]:
    """
    [Q18 ★★★] Cavalo no tabuleiro — FONTE: Lista 3, Questão 4

    Tabuleiro n x n (n >= 3). Retorne a matriz A em que A[i][j] é o número
    mínimo de movimentos de cavalo para ir de (i, j) até (0, 0).

    Casas inalcançáveis (só acontece no centro do 3x3) recebem -1.
    """
    # escreva sua solução aqui
    raise NotImplementedError


def q19_todas_as_pontes(n: int, connections: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """
    [Q19 ★★★] Todas as pontes (conexões críticas) — FONTE EXTERNA: LeetCode 1192 "Critical Connections in a Network"

    Grafo não dirigido, vértices 0..n-1, sem arestas paralelas. Retorne todas
    as arestas cuja remoção desconecta o grafo (qualquer ordem/orientação).

    Exemplo: n=4, [(0,1),(1,2),(2,0),(1,3)] -> [(1,3)]
    """
    # escreva sua solução aqui
    raise NotImplementedError


def q20_velocidade_download(n: int, connections: list[tuple[int, int, int]]) -> int:
    """
    [Q20 ★★★] Velocidade de download — FONTE EXTERNA: CSES 1694 "Download Speed"

    Computadores 1..n; o servidor é o 1 e o seu computador é o n. Cada conexão
    (a, b, c) transmite até c unidades por segundo de a para b (dirigida).
    Retorne a velocidade máxima de download.

    Exemplo: n=4, [(1,2,3),(2,4,2),(1,3,4),(3,4,5),(4,1,3)] -> 6
    """
    # escreva sua solução aqui
    raise NotImplementedError


# ============================================================================
# ★★ PRIORIDADE MÉDIA
# ============================================================================

def q21_plataformas_trem(trains: list[tuple[int, int]]) -> int:
    """
    [Q21 ★★] Plataformas de trem — FONTE: Prova AS 2025.2, Questão 2

    Cada trem é (chegada, partida). Dois trens podem dividir uma plataforma se a
    partida de um for <= chegada do outro. Retorne o número mínimo de plataformas.
    O enunciado original exige O(n log n).

    Exemplos:
        [(1100,1130),(900,910),(950,1120),(940,1200)] -> 3
        [(100,200),(200,300)] -> 1
    """
    # escreva sua solução aqui
    raise NotImplementedError


def q22_menor_distancia_pontos(points: list[tuple[float, float]]) -> float:
    """
    [Q22 ★★] Par de pontos mais próximo — FONTE: Prova AS 2025.2, Questão 1 (e Slides 07)

    Retorne a menor distância euclidiana entre dois pontos distintos da lista
    (len(points) >= 2).
    """
    # escreva sua solução aqui
    raise NotImplementedError


def q23_tem_ciclo_dirigido(n: int, adj: list[list[int]]) -> bool:
    """
    [Q23 ★★] Detectar ciclo em grafo dirigido — FONTE: Slides 09 (Busca em grafos)

    Retorne True se o grafo dirigido (adj, vértices 0..n-1) possui um ciclo.
    """
    # escreva sua solução aqui
    raise NotImplementedError


def q24_classificar_arestas(n: int, adj: list[list[int]]) -> dict:
    """
    [Q24 ★★] Classificar arestas — FONTE: Slides 09 (Busca em grafos)

    Grafo DIRIGIDO. Rode a DFS iniciando nos vértices na ordem 0, 1, ..., n-1 e
    percorrendo cada adj[u] na ordem dada. Retorne um dicionário
    {(u, v): tipo} com tipo em {"arvore", "retorno", "avanco", "cruzada"}.

    Exemplo: n=6, adj=[[1,2],[3,4],[4],[4],[5,1],[]] ->
        {(0,1):'arvore',(1,3):'arvore',(3,4):'arvore',(4,5):'arvore',(4,1):'retorno',
         (1,4):'avanco',(0,2):'arvore',(2,4):'cruzada'}
    """
    # escreva sua solução aqui
    raise NotImplementedError


def q25_corte_minimo(n: int, edges: list[tuple[int, int, int]], s: int, t: int):
    """
    [Q25 ★★] Corte mínimo — FONTE: Slides 12 (Fluxo máximo)

    Mesma entrada da Q12. Retorne (capacidade_do_corte, arestas_do_corte), onde
    arestas_do_corte é uma lista de tuplas (u, v, c) da entrada cuja remoção
    separa s de t e cuja soma de capacidades é mínima.
    """
    # escreva sua solução aqui
    raise NotImplementedError


def q26_menor_caminho_dag(n: int, edges: list[tuple[int, int, int]], s: int) -> list:
    """
    [Q26 ★★] Caminho mais barato em DAG — FONTE: Slides 10 (Menor caminho em DAG)

    edges = [(u, v, w), ...] de um DAG (pesos podem ser negativos). Retorne dist com dist[v] = menor custo de s a v
    (float('inf') se inalcançável).
    """
    # escreva sua solução aqui
    raise NotImplementedError


def q27_bipartido(n: int, adj: list[list[int]]) -> bool:
    """
    [Q27 ★★] Grafo bipartido — FONTE: Slides 08 (definição) / ≈ LeetCode 785 "Is Graph Bipartite?"

    Grafo não dirigido (pode ser desconexo). Retorne True se for bipartido.
    """
    # escreva sua solução aqui
    raise NotImplementedError


def q28_tempo_atraso_rede(times: list[tuple[int, int, int]], n: int, k: int) -> int:
    """
    [Q28 ★★] Tempo de atraso da rede — FONTE EXTERNA: LeetCode 743 "Network Delay Time"

    Nós 1..n; times = [(u, v, w)] arestas dirigidas com tempo w >= 0. Um sinal
    sai do nó k. Retorne o tempo até TODOS os nós receberem o sinal, ou -1.

    Exemplo: times=[(2,1,1),(2,3,1),(3,4,1)], n=4, k=2 -> 2
    """
    # escreva sua solução aqui
    raise NotImplementedError


def q29_voos_k_escalas(n: int, flights: list[tuple[int, int, int]], src: int, dst: int, k: int) -> int:
    """
    [Q29 ★★] Voo mais barato com até k escalas — FONTE EXTERNA: LeetCode 787 "Cheapest Flights Within K Stops"

    Cidades 0..n-1, voos dirigidos (de, para, preço). Retorne o menor preço de
    src até dst usando no máximo k escalas (k+1 voos), ou -1.

    Exemplo: n=4, [(0,1,100),(1,2,100),(2,0,100),(1,3,600),(2,3,200)], 0, 3, 1 -> 700
    """
    # escreva sua solução aqui
    raise NotImplementedError


def q30_conectar_pontos(points: list[tuple[int, int]]) -> int:
    """
    [Q30 ★★] Custo mínimo para conectar todos os pontos — FONTE EXTERNA: LeetCode 1584 "Min Cost to Connect All Points"

    O custo de ligar dois pontos é a distância de Manhattan |x1-x2| + |y1-y2|.
    Retorne o custo mínimo para conectar todos.

    Exemplo: [(0,0),(2,2),(3,10),(5,2),(7,0)] -> 20
    """
    # escreva sua solução aqui
    raise NotImplementedError


def q31_pode_concluir_cursos(num_cursos: int, prerequisitos: list[tuple[int, int]]) -> bool:
    """
    [Q31 ★★] Grade de cursos — FONTE EXTERNA: LeetCode 207 "Course Schedule"

    Cursos 0..num_cursos-1. Cada par (a, b) significa "para fazer a é preciso ter
    feito b" (aresta b -> a). Retorne True se é possível concluir todos.
    """
    # escreva sua solução aqui
    raise NotImplementedError


def q32_numero_ilhas(grid: list[str]) -> int:
    """
    [Q32 ★★] Número de ilhas — FONTE EXTERNA: LeetCode 200 "Number of Islands" (≈ CSES 1192 "Counting Rooms")

    grid: lista de strings com '1' (terra) e '0' (água). Ilhas são grupos de
    '1' ligados na horizontal/vertical. Retorne a quantidade de ilhas.
    """
    # escreva sua solução aqui
    raise NotImplementedError


def q33_laranjas_podres(grid: list[list[int]]) -> int:
    """
    [Q33 ★★] Laranjas podres — FONTE EXTERNA: LeetCode 994 "Rotting Oranges"

    0 = vazio, 1 = laranja boa, 2 = laranja podre. A cada minuto, laranjas boas
    vizinhas (4 direções) de podres apodrecem. Retorne os minutos até não sobrar
    laranja boa, ou -1 se for impossível.

    Exemplo: [[2,1,1],[1,1,0],[0,1,1]] -> 4
    """
    # escreva sua solução aqui
    raise NotImplementedError


def q34_conexao_redundante(edges: list[tuple[int, int]]) -> tuple[int, int]:
    """
    [Q34 ★★] Conexão redundante — FONTE EXTERNA: LeetCode 684 "Redundant Connection"

    Uma árvore com nós 1..n recebeu UMA aresta extra. edges tem n arestas.
    Retorne a aresta que pode ser removida para voltar a ser árvore; se houver
    várias, a que aparece por último na entrada.

    Exemplo: [(1,2),(1,3),(2,3)] -> (2,3)
    """
    # escreva sua solução aqui
    raise NotImplementedError


def q35_menor_esforco(heights: list[list[int]]) -> int:
    """
    [Q35 ★★] Caminho com menor esforço — FONTE EXTERNA: LeetCode 1631 "Path With Minimum Effort"

    Vá de (0,0) até (n-1,m-1) andando em 4 direções. O esforço de um caminho é a
    MAIOR diferença absoluta de altura entre duas casas consecutivas. Retorne o
    menor esforço possível.

    Exemplo: [[1,2,2],[3,8,2],[5,3,5]] -> 2
    """
    # escreva sua solução aqui
    raise NotImplementedError


def q36_formas_menor_caminho(n: int, roads: list[tuple[int, int, int]]) -> int:
    """
    [Q36 ★★] Número de caminhos mais curtos — FONTE EXTERNA: LeetCode 1976 "Number of Ways to Arrive at Destination"

    Interseções 0..n-1, ruas bidirecionais (u, v, tempo > 0). Retorne quantos
    caminhos de 0 até n-1 têm o menor tempo possível, módulo 10**9 + 7.

    Exemplo: n=7, [(0,6,7),(0,1,2),(1,2,3),(1,3,3),(6,3,3),(3,5,1),(6,5,1),(2,5,1),(0,4,5),(4,6,2)] -> 4
    """
    # escreva sua solução aqui
    raise NotImplementedError


def q37_maior_pontuacao(n: int, tunnels: list[tuple[int, int, int]]) -> int:
    """
    [Q37 ★★] Maior pontuação — FONTE EXTERNA: CSES 1673 "High Score"

    Salas 1..n, túneis dirigidos (a, b, x): passar pelo túnel soma x pontos
    (x pode ser negativo). Vá de 1 até n (há pelo menos um caminho). Retorne a
    maior pontuação possível, ou -1 se ela puder ser arbitrariamente grande.

    Exemplo: n=4, [(1,2,3),(2,4,-1),(1,3,-2),(3,4,7)] -> 5
    """
    # escreva sua solução aqui
    raise NotImplementedError


def q38_ciclo_negativo(n: int, edges: list[tuple[int, int, int]]):
    """
    [Q38 ★★] Encontrar um ciclo negativo — FONTE EXTERNA: CSES 1197 "Cycle Finding"

    Vértices 1..n, arestas dirigidas (a, b, w). Se existir ciclo de custo
    negativo (em qualquer lugar do grafo), retorne-o como lista de vértices que
    começa e termina no mesmo vértice, ex.: [2, 3, 4, 2]. Senão, retorne None.
    """
    # escreva sua solução aqui
    raise NotImplementedError


def q39_rota_mais_longa_dag(n: int, flights: list[tuple[int, int]]):
    """
    [Q39 ★★] Rota com mais cidades — FONTE EXTERNA: CSES 1680 "Longest Flight Route"

    Cidades 1..n, voos dirigidos (a, b), grafo acíclico. Retorne a rota de 1 até
    n que visita o MAIOR número de cidades (lista de cidades), ou None se não existir.
    """
    # escreva sua solução aqui
    raise NotImplementedError


def q40_baile_escola(n_meninos: int, n_meninas: int, pares: list[tuple[int, int]]) -> int:
    """
    [Q40 ★★] Baile da escola — FONTE EXTERNA: CSES 1696 "School Dance"

    Meninos 1..n_meninos, meninas 1..n_meninas; pares (a, b) indicam que o
    menino a aceita dançar com a menina b. Cada pessoa dança com no máximo um
    par. Retorne o número máximo de pares formados.
    """
    # escreva sua solução aqui
    raise NotImplementedError


def q41_perseguicao_policial(n: int, ruas: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """
    [Q41 ★★] Perseguição policial — FONTE EXTERNA: CSES 1695 "Police Chase"

    Cruzamentos 1..n, ruas bidirecionais (a, b). Retorne uma lista com o MENOR
    número possível de ruas a bloquear para que não exista caminho de 1 até n.

    Exemplo: n=4, [(1,2),(1,3),(2,3),(3,4),(1,4)] -> 2 ruas, ex.: [(3,4),(1,4)]
    """
    # escreva sua solução aqui
    raise NotImplementedError


def q42_lucro_tarefas(start: list[int], end: list[int], profit: list[int]) -> int:
    """
    [Q42 ★★] Lucro máximo com tarefas — FONTE EXTERNA: LeetCode 1235 "Maximum Profit in Job Scheduling"

    Tarefa i ocupa [start[i], end[i]) e dá profit[i]. Pode começar uma tarefa no
    exato instante em que outra termina. Retorne o lucro máximo.

    Exemplo: start=[1,2,3,3], end=[3,4,5,6], profit=[50,10,40,70] -> 120
    """
    # escreva sua solução aqui
    raise NotImplementedError


# ============================================================================
# ★ PRIORIDADE BAIXA / COMPLEMENTAR
# ============================================================================

def q43_sisi_sorvete_2(A: list[int]) -> int:
    """
    [Q43 ★] Sisi e a sorveteria, parte 2 — FONTE: Lista 3, Questão 1 (≈ Codeforces 1139B)

    q_i <= A[i]; a sequência q é 0...0 e depois estritamente crescente.
    Retorne a soma máxima de q.

    Exemplos: [1,2,1,3,6] -> 10 ; [3,2,5,4,10] -> 20 ; [2,2,2,2] -> 3
    """
    # escreva sua solução aqui
    raise NotImplementedError


def q44_custo_reparo(n: int, k: int, C1: int, C2: int, A: list[int]) -> int:
    """
    [Q44 ★] Minimizando custos de reparo — FONTE: Lista 3, Questão 2 (≈ Codeforces 1111C "Creative Snap")

    Estrada [1, 2^n]; buracos nas posições A. Consertar um segmento de tamanho l
    custa C1 se não tem buracos e C2 · (nº de buracos) · l caso contrário; ou
    pode-se dividir o segmento ao meio (se l >= 2). Retorne o custo mínimo.

    Exemplos: (2, 2, 1, 2, [1,3]) -> 6 ; (3, 2, 1, 2, [1,7]) -> 8
    """
    # escreva sua solução aqui
    raise NotImplementedError


def q45_subsequencias_radicais(A: list[int]) -> int:
    """
    [Q45 ★] Subsequências radicais — FONTE: Lista 3, Questão 3 (≈ Codeforces 1061C "Multiplicity")

    Conte as subsequências não vazias b de A tais que b_i é divisível por i
    (1-indexado). Responda módulo 999999937.

    Exemplos: [1,2,2] -> 6 ; [1] -> 1 ; [1,2] -> 3 ; [2,2,1,5,3] -> 7
    (o PDF da lista diz 8 para o último, mas a contagem por força bruta dá 7:
     [2],[2],[1],[5],[3],[2,2],[2,2,3])
    """
    # escreva sua solução aqui
    raise NotImplementedError


def q46_eh_caminho(adj: list[list[int]], path: list[int]) -> tuple[bool, bool]:
    """
    [Q46 ★] Verificar caminho e caminho simples — FONTE: Slides 08/09 (Exercício 4)

    Retorne (eh_caminho, eh_simples). path precisa ter pelo menos 2 vértices e
    cada par consecutivo precisa ser uma aresta (u -> v em adj). Se não for
    caminho, retorne (False, False). Simples = sem vértices repetidos.
    """
    # escreva sua solução aqui
    raise NotImplementedError


def q47_biblioteca_pico(intervals: list[tuple[int, int]]) -> tuple[int, tuple[int, int]]:
    """
    [Q47 ★] Biblioteca de Alexandria (período de pico) — FONTE: Lista 2, Questão 1 (≈ CSES 1619)

    Tempos todos distintos. Retorne (k, (u, v)): k = máximo de pessoas ao mesmo
    tempo e (u, v) o intervalo de pico de MAIOR comprimento (empate: menor u).

    Exemplos: [(5,8),(2,4),(3,9)] -> (2, (5,8)) ; [(5,8),(2,6),(3,9)] -> (3, (5,6))
    """
    # escreva sua solução aqui
    raise NotImplementedError


def q48_sisi_sorvete(A: list[int]) -> int:
    """
    [Q48 ★] Sisi e a sorveteria — FONTE: Lista 2, Questão 2 (≈ CSES 1141 "Playlist")

    Retorne o tamanho do maior trecho contíguo sem valores repetidos.

    Exemplos: [1,2,1,4] -> 3 ; [11,22,11,33,22,77,44,22] -> 5 ; [3,3,3,3,3,3] -> 1
    """
    # escreva sua solução aqui
    raise NotImplementedError


def q49_hotel_hilbert(guests: list[tuple[int, int]]) -> tuple[int, list[int]]:
    """
    [Q49 ★] Hotel de Hilbert — FONTE: Lista 2, Questão 3 (≈ CSES 1164 "Room Allocation")

    Hóspede i = (chegada, partida). Dois hóspedes dividem um quarto se a partida
    de um for ESTRITAMENTE menor que a chegada do outro. Retorne (k, quartos)
    com k mínimo e quartos[i] em 1..k (qualquer distribuição válida).
    """
    # escreva sua solução aqui
    raise NotImplementedError


def q50_quadra(A: list[int], k: int) -> tuple[int, int, int, int]:
    """
    [Q50 ★] Quadra — FONTE: Lista 2, Questão 4 (≈ CSES 1642)

    Retorne (a, b, c, d) 1-indexados com a < b < c < d e A_a+A_b+A_c+A_d = k,
    ou (-1, -1, -1, -1).
    """
    # escreva sua solução aqui
    raise NotImplementedError


def q51_torres_blocos(A: list[int]) -> int:
    """
    [Q51 ★] Os blocos (torres) — FONTE: Lista 2, Questão 5 (≈ CSES 1073 "Towers")

    Um bloco só pode ir em cima de outro de tamanho >= ao dele; blocos chegam em
    ordem. Retorne o número mínimo de torres.

    Exemplos: [1,2,1,4] -> 3 ; [11,22,11,33,22,77,44,22] -> 4 ; [3,3,3,3,3,3] -> 1
    """
    # escreva sua solução aqui
    raise NotImplementedError


def q52_sistema_planetario(A: list[int], k: int) -> int:
    """
    [Q52 ★] O grande sistema planetário — FONTE: Lista 2, Questão 6 (≈ CSES 1620 "Factory Machines")

    Retorne o menor inteiro T tal que sum(T // A_i) >= k.

    Exemplos: ([3,2,6], 7) -> 8 ; ([3,2,6,5,8,2,1], 1234) -> 438
    """
    # escreva sua solução aqui
    raise NotImplementedError


def q53_otimizacao(A: list[int]) -> int:
    """
    [Q53 ★] Otimização (minimizar soma de |A_i - k|) — FONTE: Lista 2, Questão 7 (≈ CSES 1074 "Stick Lengths")

    Retorne o MENOR k que minimiza sum(|A_i - k|).
    """
    # escreva sua solução aqui
    raise NotImplementedError
