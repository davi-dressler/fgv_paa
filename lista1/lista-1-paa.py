"""
Projeto e Análise de Algoritmos — Lista 1
FGV - EMAp — 2026

Preencha o corpo de cada função/classe abaixo.
NÃO altere nomes de arquivo, assinaturas de funções/classes ou nomes de métodos.
Código auxiliar (classes, funções) deve ser definido DENTRO do escopo da questão
correspondente (ex: dentro de question_2, ou dentro do __init__ da classe, etc).
"""



def question_1():
    """
    Recorrência com Busca Embutida.

    int solve(int v[], int left, int right) {
        int n = right - left + 1;
        if (n <= 1) return 0;
        int mid = (left + right) / 2;
        int count = solve(v, left, mid) + solve(v, mid + 1, right);
        for (int i = left; i <= mid; i++) {
            count += binarySearchCount(v, mid + 1, right, v[i]);
        }
        merge(v, left, mid, right);
        return count;
    }

    binarySearchCount roda em O(log n) e merge roda em O(n).

    RESPONDA AQUI:
    """

    # Árvore de recorrência:
    
    # T(n) = 2T(n/2) + O(n log n)
    
    # Nível 0: 1 nó de tamanho n        ->      custo   O(n log n)
    # Nível 1: 2 nós de tamanho n/2     ->      custo   2 * O((n/2) log(n/2)) = O(n log(n/2))
    # Nível 2: 4 nós de tamanho n/4     ->      custo   4 * O((n/4) log(n/4)) = O(n log(n/4))
    # ...
    # Nível k: 2^k nós de tamanho n/2^k -> custo 2^k * O((n/2^k) log(n/2^k))
    #          = O(n log(n/2^k)) = O(n (log n - k))
    
    # A árvore tem altura log n (até os subproblemas chegarem a tamanho 1).
    
    # Somando o custo de todos os níveis:
    #   O(n (log n - 0)) + O(n (log n - 1)) + ... + O(n (log n - log n))
    # = O(n * (log n + (log n - 1) + ... + 1 + 0))
    # = O(n * (log n)(log n + 1)/2)
    # = O(n log^2 n)
    
    # Portanto, T(n) = Θ(n log^2 n).

    pass


def question_2(grade: list, k: int) -> int:
    """
    Painel de Sensores.

    grade: matriz n x n (lista de listas/tuplas) com linhas e colunas
           ordenadas de forma crescente.
    k: inteiro, 1 <= k <= n^2.

    Retorna a k-ésima menor leitura da grade.
    Complexidade exigida: O(n log D), onde D = max(grade) - min(grade).
    """

    # Intenção aqui é conseguir O(n log d) da seguinte maneira:
    # Vamos aproveitar a ordenação que possuimos por linha e coluna,
    # Dessa forma, sabemos que a entrada na ponta esquerda superior é o menor, e a entrada
    # na ponta direita inferior é o maior. Portanto, nosso espaço de busca é D = max(grade) - min(grade).
    # Dessa forma, fazemos uma busca binária nesse intervalo, comparando quantos valores há menores do que a entrada
    # analisada a cada iteração da busca binária.

    n = len(grade)
    
    def conta_menores(x):
        """Conta quantas entradas são menores que o registro informado, aproveitando a ordenação da 
        matriz de sensores. Dessa forma, percorremos no máximo n entradas para cima e n entradas para a direita.
        Percorremos no máximo, 2n entradas."""

        col = 0
        line = n - 1
        total = 0

        while line >= 0 and col <= n - 1:
            if grade[line][col] <= x:
                total += line + 1
                col += 1
            else:
                line -= 1


        return total

    left = grade[0][0]
    right = grade[n-1][n-1]

    def binary_search(left, right):

        while left < right:
            mid =  (left + right)//2

            if conta_menores(mid) >= k:
                right = mid
            else:
                left = mid + 1

        return left

    return binary_search(left, right)


def question_3(categorias: list, k: int) -> int:
    """
    Maratona de Podcasts.

    categorias: lista de n inteiros (categoria de cada episódio, em ordem
                de publicação).
    k: número máximo de categorias distintas permitidas no trecho.

    Retorna o tamanho do maior trecho contínuo com no máximo k categorias
    distintas.
    Complexidade exigida: O(n).
    """

    # A intenção aqui é conseguir O(n) da seguinte maneira:
    # Vamos aproveitar que queremos o maior trecho contínuo com no máximo k categorias distintas.
    # Dessa forma, mantemos uma janela deslizante [left, idx] que sempre respeita a restrição
    # de ter no máximo k categorias diferentes. Para controlar quantas vezes cada categoria
    # aparece dentro da janela, usamos um dicionário que mapeia categoria -> contagem.

    # A cada iteração, adiciono a categoria do índice atual (idx) ao dicionário.
    # Se, com isso, a janela passar a ter mais de k categorias distintas, avançamos o ponteiro
    # left e diminuimos a contagem da categoria que está saindo. Quando a contagem de uma
    # categoria chega a zero, removemos ela do dicionário.
    
    # Assim, cada elemento entra e sai da janela no máximo uma vez, pois left só avança.
    # Portanto, percorremos a lista uma única vez, resultando em O(n).

    # A cada passo, calculamos o tamanho da janela (idx - left + 1) e atualizamos o máximo.

    categorias_count = {} #Dicionário (Categoria: Num vexes que aparece na sequência)
    left = 0
    seq_max = 0

    for idx in range(len(categorias)):
        categorias_count[categorias[idx]] = categorias_count.get(categorias[idx], 0) + 1

        while len(categorias_count.keys()) > k:
            categorias_count[categorias[left]] -= 1
            
            if categorias_count[categorias[left]] == 0:
                del categorias_count[categorias[left]]

            left += 1

        seq = idx - left + 1
        if seq > seq_max:
            seq_max = seq

    return seq_max


def question_4(inicial: str, final: str, banco: list) -> int:
    """
    Central de Senhas.

    inicial, final: strings de tamanho L, compostas por dígitos '0'-'9'.
    banco: lista de N strings (todas de tamanho L) representando senhas
           seguras cadastradas. inicial e final estão garantidamente em banco.

    Retorna o menor número de trocas de um único caractere por vez, passando
    sempre por senhas do banco, para transformar inicial em final.
    Retorna -1 se não for possível.
    Complexidade exigida: O(N * L).
    """

    # Nesse problema, a modelagem se assemelha a um grafo: cada senha do banco é um vértice,
    # e existe uma aresta entre duas senhas quando elas diferem em um caractere exatamente, para cumprir
    # a condição pedida de troca de apenas um caractere entre as senhas.
    # Queremos a menor distância (ou seja, número de trocas) entre 'inicial' e 'final' nesse grafo.
    

    if inicial == final:
            return 0
    
    banco_ = set(banco)

    if final not in banco_:
        return -1

    L = len(inicial)

    padroes = {}
    for senha in banco_:
        for i in range(L):
            chave = senha[:i] + "*" + senha[i+1:]
            if chave not in padroes:
                padroes[chave] = []
            padroes[chave].append(senha)

    visitados = {inicial}
    fila = [(inicial, 0)]
    head = 0

    while head < len(fila):
        atual, distancia = fila[head]
        head += 1

        for i in range(L):
            chave = atual[:i] + "*" + atual[i+1:]
            for vizinho in padroes.get(chave, []):
                if vizinho in visitados:
                    continue
                if vizinho == final:
                    return distancia + 1

                visitados.add(vizinho)
                fila.append((vizinho, distancia + 1))

    return -1


class Cache:
    """
    Cache Inteligente (Q5).

    Cache(capacidade): cria um cache com capacidade fixa `capacidade`.
    consultar(chave): retorna o valor associado à chave (e marca como mais
                       recentemente usada) ou -1 se a chave não existir.
    atualizar(chave, valor): insere/atualiza o valor associado à chave,
                              marcando-a como mais recentemente usada.
                              Se o cache estiver cheio e a chave for nova,
                              remove antes a entrada menos recentemente usada.

    Ambas as operações devem custar O(1) no caso médio.
    """

    def __init__(self, capacidade: int):
        self.capacidade = capacidade
        self.nodes = {}

        self.head = [None, None, None, None] # [0: Chave, 1: Valor, 2: Prev, 3: Prox]
        self.tail = [None, None, None, None]

        self.head[3] = self.tail
        self.tail[2] = self.head

    def _remover(self, node):
        node[2][3] = node[3]
        node[3][2] = node[2]

    def _inserir_fim(self, node):
        node[2] = self.tail[2]
        node[3] = self.tail
        self.tail[2][3] = node
        self.tail[2] = node

    def consultar(self, chave):
        if chave in self.nodes:
            node = self.nodes[chave]
            self._remover(node)
            self._inserir_fim(node)
            return node[1]
        else:
            return -1

    def atualizar(self, chave, valor) -> None:
        if chave in self.nodes:
            node = self.nodes[chave]
            node[1] = valor
            self._remover(node)
            self._inserir_fim(node)
            return

        else:
            c = len(self.nodes.keys())
            if c >= self.capacidade:
                node = self.head[3]
                self._remover(node)
                del self.nodes[node[0]]

            novo = [chave, valor, None, None]
            self.nodes[chave] = novo
            self._inserir_fim(novo)


def question_6(reproducoes: list, k: int) -> list:
    """
    Rádio Digital.

    reproducoes: lista com n identificadores de música (podem se repetir
                 livremente), representando o histórico de reproduções do dia.
    k: número de músicas mais tocadas a retornar.

    Retorna uma lista com as k músicas mais tocadas, em ordem DECRESCENTE
    de número de reproduções (em caso de empate na frequência, qualquer
    ordem entre elas é aceita).

    Caso o número de músicas distintas tocadas seja menor que k, retorne
    todas as músicas distintas (nesse caso a lista de retorno terá menos
    de k elementos).

    Complexidade exigida: O(n) no total — não é permitido ordenar por
    frequência com um algoritmo O(n log n) ou O(n log k) (nem sequer usar
    uma heap para isso). Pense em como o fato de a frequência de qualquer
    música estar sempre entre 0 e n pode ser explorado.
    """

    n = len(reproducoes)
    
    num_reproducoes = [0] * (n+1) # no índice correspondente a cada id vamos guardar exatamente o número de reproduções da música
    for id in reproducoes:
        num_reproducoes[id] += 1

    num_reproducoes_id = [[] for _ in range(n+1)]
    for id, total_repr in enumerate(num_reproducoes):
        if total_repr > 0:
            num_reproducoes_id[total_repr].append(id)

    top_k = []
    for total_repr in range(n, 0, -1):
        for id in num_reproducoes_id[total_repr]:
            top_k.append(id)
            if len(top_k) == k:
                return top_k

    return top_k

import random

def question_7_a(scores: list, k: int) -> int:
    """
    Análise de Crédito - item (a).

    scores: lista não ordenada de n inteiros.
    k: 1 <= k <= n.

    Retorna o k-ésimo menor score.
    Complexidade exigida: tempo esperado O(n) (caso médio).
    """

    # Nessa questão a ideia foi implementar o quickselect para a procura do k-menor score,
    # como a questão bem fala, a aleatoriedade da escolha do pivô para realizar o particionamento
    # pode degenerar o algoritmo que para O(nˆ2) caso a escolha do pivô esteja sempre muito próximo às extremidades, 
    # ou talvez, exatamente as extremidades, o particionamento ficaria muito desbalanceado, um lado com poucos
    # registros ou 0 e o outro com muitos. 

    if len(scores) == 1:
        return scores[0]

    p = random.choice(scores)

    menores = [x for x in scores if x < p]
    iguais  = [x for x in scores if x == p]
    maiores = [x for x in scores if x > p]

    if k <= len(menores):
        return question_7_a(menores, k)
    elif k <= len(menores) + len(iguais):
        return p
    else:
        return question_7_a(maiores, k - len(menores) - len(iguais))


def question_7_b(scores: list, k: int) -> int:
    """
    Análise de Crédito - item (b).

    Mesmo problema do item (a), mas agora a complexidade deve ser O(n)
    também no pior caso.
    """

    if len(scores) <= 5:
        return sorted(scores)[k-1]

    grupos = [scores[i:i+5] for i in range(0, len(scores), 5)]

    medianas = [sorted(g)[len(g)//2] for g in grupos]

    pivo = question_7_b(medianas, len(medianas)//2 + 1)

    menores = [x for x in scores if x < pivo]
    iguais  = [x for x in scores if x == pivo]
    maiores = [x for x in scores if x > pivo]

    if k <= len(menores):
        return question_7_b(menores, k)
    elif k <= len(menores) + len(iguais):
        return pivo
    else:
        return question_7_b(maiores, k - len(menores) - len(iguais))


def question_8(comunidades: list) -> list:
    """
    Feed Consolidado.

    comunidades: lista com k listas de inteiros, cada uma já ordenada de
                 forma crescente. O total de elementos somando todas as
                 listas é n.

    Retorna uma única lista com todos os elementos, ordenada de forma
    crescente.
    Complexidade exigida: O(n log k).
    """

    def heap_push(heap, item):
        heap.append(item)
        i = len(heap) - 1
        while i > 0:
            pai = (i - 1) // 2
            if heap[pai][0] <= heap[i][0]:
                break
            heap[pai], heap[i] = heap[i], heap[pai]
            i = pai

    def heap_pop(heap):
        topo = heap[0]
        ultimo = heap.pop()
        if heap:
            heap[0] = ultimo
            i = 0
            n = len(heap)
            while True:
                esq = 2 * i + 1
                dir = 2 * i + 2
                menor = i

                if esq < n and heap[esq][0] < heap[menor][0]:
                    menor = esq
                if dir < n and heap[dir][0] < heap[menor][0]:
                    menor = dir

                if menor == i:
                    break

                heap[i], heap[menor] = heap[menor], heap[i]
                i = menor
        return topo

    heap = []
    for i, lista in enumerate(comunidades):
        if lista:
            heap_push(heap, (lista[0], i, 0))

    resultado = []

    while heap:
        valor, i, j = heap_pop(heap)
        resultado.append(valor)

        # Insere o próximo elemento da mesma lista, se houver
        if j + 1 < len(comunidades[i]):
            heap_push(heap, (comunidades[i][j + 1], i, j + 1))

    return resultado


def question_9_a(energia: list, consumo: list) -> int:
    """
    Autonomia Elétrica — item (a).

    energia[i]: energia recarregada na estação i.
    consumo[i]: energia gasta para ir da estação i até a estação (i+1) mod n.

    Retorna o índice de uma estação de partida a partir da qual é possível
    completar o circuito inteiro sem a bateria ficar negativa em nenhum
    trecho, ou -1 se não existir tal estação.

    Descreva (em comentário) uma solução por froça bruta que teste, para
    cada possível estação de partida, se o circuito completo é viável.
    Qual a complexidade dessa abordagem?
    """

    # Nessa abordagem de força bruta precisamos analisar cada estação (n) como ponto de início
    # e para cada um, percorrer o trajeto (n). Portanto, O(nˆ2)

    num_est = len(energia) # número de estações

    for est_inicial in range(num_est):
        armazenado = 0
        circuito_valido = True

        for trajeto in range(num_est):
            id_est = (est_inicial + trajeto) % num_est
            armazenado += energia[id_est]
            armazenado -= consumo[id_est]

            if armazenado < 0:
                circuito_valido = False
                break

        if circuito_valido == True:
            return est_inicial

    return -1


def question_9_b(energia: list, consumo: list) -> int:
    """
    Autonomia Elétrica — item (b).

    Mesmo problema do item (a), mas sabendo que a solução (quando existe)
    é única, resolva com complexidade O(n).
    """

    num_est = len(energia)
    
    total = 0
    for i in range(num_est):
        total += energia[i] - consumo[i]

    if total < 0:
        return -1

    est_inicial = 0
    armazenado = 0

    for i in range(num_est):
        armazenado += energia[i] - consumo[i]

        if armazenado < 0:
            est_inicial = i + 1
            armazenado = 0

    return est_inicial


def question_10(altitudes: list) -> int:
    """
    Trilha de Picos de Montanha.

    altitudes: lista de n inteiros (podem se repetir), na ordem em que
               aparecem na trilha.

    Retorna o tamanho da maior subsequência estritamente crescente.
    Complexidade exigida: O(n log n).
    """

    # Intenção: O(n log n).
    # Mantemos 'finais', onde finais[i] é o menor valor que termina uma
    # subsequência estritamente crescente de comprimento i + 1.
    # Para cada altitude x, fazemos busca binária pela 1ª posição com finais[pos] >= x.
    # Se pos == len(finais), adicionamos x; senão, substituímos finais[pos] = x.
    # Isso preserva a ordem original e garante crescimento estrito.

    finais = []  
    
    for x in altitudes:
        inicio = 0
        fim = len(finais)

        while inicio < fim:
            meio = (inicio + fim) // 2
            if finais[meio] < x:
                inicio = meio + 1
            else:
                fim = meio


        if inicio == len(finais):
            finais.append(x)
        else:
            finais[inicio] = x

    return len(finais)
