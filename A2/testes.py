"""
PAA 2025.2 — Corretor automático das questões práticas
======================================================
Uso (no terminal, na pasta dos arquivos):

    python testes.py                 # testa todas as questões de praticas.py
    python testes.py 1 4 17          # testa só Q01, Q04 e Q17
    python testes.py --prioridade 3  # só as ★★★ (alta)
    python testes.py -v 8            # mostra também os casos que passaram
    python testes.py --sem-desempenho      # pula os testes de tempo
    python testes.py --gabarito      # roda os testes contra gabarito.py (sanidade)

Legenda:  ✅ passou tudo   ❌ falhou algum caso   ⏭  ainda não implementada
          ⏱  LENTO = estourou o limite de tempo (sinal de complexidade errada)

Os testes de desempenho rodam em um processo separado, com limite de tempo.
O arquivo gabarito.py precisa estar na mesma pasta (é usado como oráculo nos
testes aleatórios e de desempenho). Só biblioteca padrão.
"""
from __future__ import annotations

import argparse
import copy
import importlib
import math
import multiprocessing as mp
import random
import sys
import time
import traceback
from collections import deque, Counter
from itertools import combinations

import os

# funciona rodando de dentro de A2/ ou da raiz do repositório (python A2/testes.py)
PASTA = os.path.dirname(os.path.abspath(__file__))
if PASTA not in sys.path:
    sys.path.insert(0, PASTA)

import gabarito as G  # type: ignore

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

INF = math.inf
TESTES = {}          # num -> (fn_teste, titulo, fonte, prioridade)
DESEMPENHO = {}      # num -> [(descricao, limite_s, gerador)]
MOD = None           # módulo sendo testado (praticas ou gabarito)


# ---------------------------------------------------------------------------
# Infraestrutura
# ---------------------------------------------------------------------------
class NaoImplementada(Exception):
    pass


def teste(num, titulo, fonte, prio):
    def deco(fn):
        TESTES[num] = (fn, titulo, fonte, prio)
        return fn
    return deco


def desempenho(num, descricao, limite):
    def deco(gen):
        DESEMPENHO.setdefault(num, []).append((descricao, limite, gen))
        return gen
    return deco


def curto(x, lim=160):
    s = repr(x)
    return s if len(s) <= lim else s[:lim] + " ..."


class Ctx:
    """Executa casos de uma questão e acumula os resultados."""

    def __init__(self, f):
        self.f = f
        self.res = []            # (ok, descricao, mensagem)

    def chama(self, args):
        try:
            return True, self.f(*copy.deepcopy(args))
        except NotImplementedError:
            raise NaoImplementada()
        except RecursionError:
            return False, "RecursionError: recursão profunda demais"
        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)[-1]
            return False, f"{type(e).__name__}: {e}  (linha {tb.lineno})"

    def eq(self, desc, args, esperado, normaliza=None):
        ok, out = self.chama(args)
        if not ok:
            self.res.append((False, desc, f"erro: {out}\n        entrada: {curto(args)}"))
            return
        try:
            a, b = (normaliza(out), normaliza(esperado)) if normaliza else (out, esperado)
        except Exception as e:
            self.res.append((False, desc, f"saída em formato inesperado: {curto(out)}"))
            return
        if a == b:
            self.res.append((True, desc, ""))
        else:
            self.res.append((False, desc, f"esperado {curto(esperado)}, obtido {curto(out)}"
                                          f"\n        entrada: {curto(args)}"))

    def valida(self, desc, args, validador):
        ok, out = self.chama(args)
        if not ok:
            self.res.append((False, desc, f"erro: {out}\n        entrada: {curto(args)}"))
            return
        try:
            v, msg = validador(out)
        except Exception as e:
            v, msg = False, f"saída em formato inesperado ({type(e).__name__}: {e}): {curto(out)}"
        self.res.append((v, desc, "" if v else f"{msg}\n        entrada: {curto(args)}"))

    def aleatorio(self, desc, qtd, gerar, comparar):
        """gerar(rng) -> args ; comparar(args, out) -> (ok, msg)"""
        rng = random.Random(12345)
        for k in range(qtd):
            args = gerar(rng)
            ok, out = self.chama(args)
            if not ok:
                self.res.append((False, f"{desc} #{k + 1}", f"erro: {out}\n        entrada: {curto(args)}"))
                return
            try:
                v, msg = comparar(args, out)
            except Exception as e:
                v, msg = False, f"saída em formato inesperado ({type(e).__name__}: {e}): {curto(out)}"
            if not v:
                self.res.append((False, f"{desc} #{k + 1}", f"{msg}\n        entrada: {curto(args)}"))
                return
        self.res.append((True, f"{desc} ({qtd} casos)", ""))


def compara_gabarito(nome_g, normaliza=None):
    """Comparador: saída == saída do gabarito (após normalização opcional)."""
    def comp(args, out):
        esp = getattr(G, nome_g)(*copy.deepcopy(args))
        a, b = (normaliza(out), normaliza(esp)) if normaliza else (out, esp)
        return a == b, f"esperado {curto(esp)}, obtido {curto(out)}"
    return comp


# ---------------------------------------------------------------------------
# Geradores e auxiliares de grafos
# ---------------------------------------------------------------------------
def grafo_aleatorio(rng, n, m, dirigido=True, wmin=1, wmax=20, conexo=False):
    edges = set()
    lista = []
    if conexo:
        for v in range(1, n):
            u = rng.randrange(v)
            lista.append((u, v, rng.randint(wmin, wmax)))
            edges.add((u, v)); edges.add((v, u))
    tent = 0
    while len(lista) < m and tent < 50 * m + 100:
        tent += 1
        u, v = rng.randrange(n), rng.randrange(n)
        if u == v or (u, v) in edges or (not dirigido and (v, u) in edges):
            continue
        edges.add((u, v))
        if not dirigido:
            edges.add((v, u))
        lista.append((u, v, rng.randint(wmin, wmax)))
    return lista


def dag_aleatorio(rng, n, m, wmin=1, wmax=20):
    perm = list(range(n))
    rng.shuffle(perm)                      # numeração NÃO topológica
    vistos, lista = set(), []
    tent = 0
    while len(lista) < m and tent < 50 * m + 100:
        tent += 1
        i, j = rng.randrange(n), rng.randrange(n)
        if i >= j:
            continue
        u, v = perm[i], perm[j]
        if (u, v) in vistos:
            continue
        vistos.add((u, v))
        lista.append((u, v, rng.randint(wmin, wmax)))
    return lista


def adj_de(n, edges, dirigido=True, peso=True):
    adj = [[] for _ in range(n)]
    for e in edges:
        u, v = e[0], e[1]
        if peso:
            adj[u].append((v, e[2]))
            if not dirigido:
                adj[v].append((u, e[2]))
        else:
            adj[u].append(v)
            if not dirigido:
                adj[v].append(u)
    return adj


def min_peso(edges):
    w = {}
    for u, v, c in edges:
        w[(u, v)] = min(w.get((u, v), INF), c)
    return w


def conecta_todos(vertices, arestas):
    pai = {v: v for v in vertices}

    def f(x):
        while pai[x] != x:
            pai[x] = pai[pai[x]]
            x = pai[x]
        return x
    for u, v in arestas:
        pai[f(u)] = f(v)
    return len({f(v) for v in vertices}) <= 1


def alcanca(n, arcos, s, t):
    adj = [[] for _ in range(n)]
    for u, v in arcos:
        adj[u].append(v)
    vis = [False] * n
    vis[s] = True
    fila = deque([s])
    while fila:
        u = fila.popleft()
        for v in adj[u]:
            if not vis[v]:
                vis[v] = True
                fila.append(v)
    return vis[t]


def perto(a, b, eps=1e-6):
    if a == INF or b == INF:
        return a == b
    return abs(a - b) <= eps * max(1, abs(a), abs(b))


# ===========================================================================
# ★★★ ALTA
# ===========================================================================
EX_Q01 = [(1, 2, 1), (1, 4, 2), (2, 3, 7), (2, 5, 1), (3, 6, 9), (4, 5, 3),
          (4, 7, 2), (5, 6, 1), (5, 8, 2), (6, 9, 10), (7, 8, 1), (8, 9, 1)]


@teste(1, "Orçamento para adaptar ruas", "Prova A2 2025.2 — Q1", 3)
def t01(c):
    c.eq("exemplo da prova, C=16", (EX_Q01, 16), True)
    c.eq("exemplo da prova, C=21", (EX_Q01, 21), True)
    c.eq("exemplo da prova, C=10", (EX_Q01, 10), False)
    c.eq("exemplo, C=15", (EX_Q01, 15), False)
    c.eq("cidade desconexa nunca dá", ([(1, 2, 1), (3, 4, 1)], 100), False)
    c.eq("caso extra", ([(1, 2, 1), (2, 3, 1), (1, 3, 100)], 2), True)

    def gera(rng):
        n = rng.randint(2, 25)
        e = [(u + 1, v + 1, w) for u, v, w in grafo_aleatorio(rng, n, rng.randint(n - 1, 3 * n),
                                                                dirigido=False, conexo=rng.random() < .85)]
        return (e, rng.randint(0, 20 * n))
    c.aleatorio("aleatórios vs gabarito", 150, gera, compara_gabarito("q01_orcamento_adaptacao"))


@desempenho(1, "20.000 cruzamentos, 100.000 segmentos", 6)
def d01(seed):
    rng = random.Random(seed)
    e = [(u, v, w) for u, v, w in grafo_aleatorio(rng, 20000, 100000, False, 1, 10 ** 6, conexo=True)]
    esp = G.q01_orcamento_adaptacao(e, 10 ** 9)
    return (e, 10 ** 9), lambda out: (out == esp, f"esperado {esp}, obtido {out}")


def valida_q02(edges, o, d, esperado_custo):
    w = min_peso(edges)

    def v(out):
        if esperado_custo is None:
            return out is None, f"destino inalcançável: esperado None, obtido {curto(out)}"
        if out is None:
            return False, "retornou None, mas existe caminho"
        out = [tuple(e) for e in out]
        if o == d:
            return out == [], f"origem == destino: esperado [], obtido {curto(out)}"
        if not out or out[0][0] != o or out[-1][1] != d:
            return False, f"caminho deve começar em {o} e terminar em {d}: {curto(out)}"
        for (a, b), (x, y) in zip(out, out[1:]):
            if b != x:
                return False, f"arestas não encadeadas: {(a, b)} seguida de {(x, y)}"
        custo = 0
        for e in out:
            if e not in w:
                return False, f"aresta {e} não existe (lembre: arestas dirigidas)"
            custo += w[e]
        return custo == esperado_custo, f"custo do caminho = {custo}, ótimo = {esperado_custo}"
    return v


def custo_q02(edges, o, d):
    p = G.q02_caminho_energia(edges, o, d)
    if p is None:
        return None
    w = min_peso(edges)
    return sum(w[e] for e in p)


@teste(2, "Caminho de menor saldo de bateria", "Prova A2 2025.2 — Q2 (versão dirigida)", 3)
def t02(c):
    ex = [(3, 2, 2), (2, 1, 2), (1, 4, -2), (4, 7, 2), (7, 8, -2), (8, 9, 1), (2, 5, -3), (5, 6, 3), (5, 8, 5)]
    c.eq("exemplo da prova (caminho único ótimo)", (ex, 3, 9), [(3, 2), (2, 1), (1, 4), (4, 7), (7, 8), (8, 9)],
         normaliza=lambda p: None if p is None else [tuple(e) for e in p])
    c.valida("inalcançável -> None", ([(1, 2, 1), (3, 4, 1)], 1, 4), valida_q02([(1, 2, 1), (3, 4, 1)], 1, 4, None))
    c.valida("origem == destino -> []", (ex, 3, 3), valida_q02(ex, 3, 3, 0))
    arm = [(0, 1, 1), (0, 2, 5), (2, 1, -10), (1, 3, 1)]
    c.valida("caso com aresta negativa", (arm, 0, 3), valida_q02(arm, 0, 3, -4))

    def gera(rng):
        n = rng.randint(2, 15)
        e = dag_aleatorio(rng, n, rng.randint(1, 3 * n), -10, 15)
        return (e, rng.randrange(n), rng.randrange(n))

    def comp(args, out):
        e, o, d = args
        return valida_q02(e, o, d, custo_q02(e, o, d))(out)
    c.aleatorio("aleatórios com pesos negativos", 150, gera, comp)


@desempenho(2, "1.000 cruzamentos, 5.000 segmentos", 8)
def d02(seed):
    rng = random.Random(seed)
    e = dag_aleatorio(rng, 1000, 5000, -50, 100)
    o, d = 0, 999
    return (e, o, d), valida_q02(e, o, d, custo_q02(e, o, d))


def valida_q03(coins, value, esperado):
    def v(out):
        if esperado == -1:
            return out == -1, f"esperado -1, obtido {curto(out)}"
        if out == -1 or out is None:
            return False, f"retornou {out}, mas é possível (ótimo usa {len(esperado)} moedas)"
        out = list(out)
        if any(x not in coins for x in out):
            return False, f"usou moeda que não existe: {curto(out)}"
        if sum(out) != value:
            return False, f"moedas somam {sum(out)}, deveria ser {value}"
        return len(out) == len(esperado), f"usou {len(out)} moedas, o mínimo é {len(esperado)}"
    return v


@teste(3, "Troco com menor número de moedas", "Prova A2 2025.2 — Q3", 3)
def t03(c):
    for coins, val, esp in [([1, 5, 6, 9], 11, [5, 6]), ([2], 3, -1), ([1, 2, 5], 11, [1, 5, 5]),
                            ([1, 3, 4], 6, [3, 3]), ([3, 7], 1, -1), ([5, 1], 0, [])]:
        c.valida(f"coins={coins}, value={val}", (coins, val), valida_q03(coins, val, esp))

    def gera(rng):
        return (rng.sample(range(1, 30), rng.randint(1, 5)), rng.randint(0, 120))

    def comp(args, out):
        return valida_q03(args[0], args[1], G.q03_troco_minimo(*args))(out)
    c.aleatorio("aleatórios vs gabarito", 200, gera, comp)


@desempenho(3, "value = 20.000, 40 moedas", 8)
def d03(seed):
    rng = random.Random(seed)
    coins = rng.sample(range(7, 500), 40)
    val = 20000
    return (coins, val), valida_q03(coins, val, G.q03_troco_minimo(coins, val))


def valida_q04(sensors, si, sf):
    pos = {s.id: s for s in sensors}

    def d(a, b):
        return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)

    def menor(o, t):
        dist = {s.id: INF for s in sensors}
        dist[o] = 0
        feito = set()
        while True:
            u = min((v for v in dist if v not in feito), key=lambda v: dist[v], default=None)
            if u is None or dist[u] == INF:
                break
            feito.add(u)
            for b in sensors:
                if b.id != u and d(pos[u], b) <= pos[u].r:
                    dist[b.id] = min(dist[b.id], dist[u] + d(pos[u], b))
        return dist[t]

    ida, volta = menor(si, sf), menor(sf, si)

    def v(out):
        if ida == INF or volta == INF:
            return out is None, f"comunicação impossível: esperado None, obtido {curto(out)}"
        if out is None:
            return False, "retornou None, mas a comunicação é possível"
        out = list(out)
        if out[0] != si or out[-1] != si or sf not in out:
            return False, f"deve começar e terminar em {si} passando por {sf}: {curto(out)}"
        k = out.index(sf)
        tot = []
        for trecho in (out[:k + 1], out[k:]):
            soma = 0
            for a, b in zip(trecho, trecho[1:]):
                if d(pos[a], pos[b]) > pos[a].r + 1e-9:
                    return False, f"{a} não alcança {b} (dist > raio de {a})"
                soma += d(pos[a], pos[b])
            tot.append(soma)
        if not perto(tot[0], ida):
            return False, f"ida tem {tot[0]:.4f} m, a menor é {ida:.4f} m"
        return perto(tot[1], volta), f"volta tem {tot[1]:.4f} m, a menor é {volta:.4f} m"
    return v


@teste(4, "Rede de sensores (ida e volta)", "Simulado A2 2025.2 — Q1", 3)
def t04(c):
    S = G.Sensor
    ex = [S(0, 0, 0, 30), S(1, 25, 0, 25), S(2, 50, 0, 30), S(3, 15, 20, 35), S(4, 35, 25, 25),
          S(5, 75, 10, 15), S(6, 70, 20, 20), S(7, 55, 25, 25)]
    c.eq("exemplo do simulado", (ex, 0, 5), [0, 1, 2, 5, 6, 7, 4, 3, 0])
    iso = ex + [S(8, 500, 500, 1000)]
    c.valida("sensor distante com raio grande", (iso, 8, 0), valida_q04(iso, 8, 0))
    c.valida("sensor isolado", (ex + [S(9, 900, 900, 1)], 0, 9), valida_q04(ex + [S(9, 900, 900, 1)], 0, 9))

    def gera(rng):
        n = rng.randint(2, 12)
        ss = [S(i, rng.randint(0, 60), rng.randint(0, 60), rng.randint(5, 35)) for i in range(n)]
        a, b = rng.sample(range(n), 2)
        return (ss, a, b)

    def comp(args, out):
        return valida_q04(*args)(out)
    c.aleatorio("aleatórios", 120, gera, comp)


@teste(5, "A aresta é uma ponte?", "Simulado A2 2025.2 — Q2(b)", 3)
def t05(c):
    def adj(n, e):
        g = [[] for _ in range(n)]
        for u, v in e:
            g[u].append(v); g[v].append(u)
        return g
    g = adj(5, [(0, 1), (0, 3), (1, 2), (1, 4), (3, 4)])
    c.eq("exemplo (1,2)", (g, 5, 1, 2), True)
    c.eq("exemplo (4,3)", (g, 5, 4, 3), False)
    c.eq("exemplo (0,1)", (g, 5, 0, 1), False)
    ciclo = adj(6, [(i, (i + 1) % 6) for i in range(6)])
    c.eq("ciclo", (ciclo, 6, 2, 3), False)
    arv = adj(4, [(0, 1), (1, 2), (1, 3)])
    c.eq("árvore", (arv, 4, 3, 1), True)

    def gera(rng):
        n = rng.randint(2, 14)
        e = [(u, v) for u, v, _ in grafo_aleatorio(rng, n, rng.randint(n - 1, 2 * n), False, conexo=True)]
        u, v = rng.choice(e)
        return (adj(n, e), n, u, v)
    c.aleatorio("aleatórios vs gabarito", 200, gera, compara_gabarito("q05_eh_ponte"))


@desempenho(5, "100.000 vértices, 150.000 arestas", 6)
def d05(seed):
    rng = random.Random(seed)
    n = 100000
    e = [(u, v) for u, v, _ in grafo_aleatorio(rng, n, 150000, False, conexo=True)]
    g = [[] for _ in range(n)]
    for u, v in e:
        g[u].append(v); g[v].append(u)
    u, v = e[rng.randrange(len(e))]
    esp = G.q05_eh_ponte(copy.deepcopy(g), n, u, v)
    return (g, n, u, v), lambda out: (out == esp, f"esperado {esp}, obtido {out}")


@teste(6, "Rota alternativa após interditar uma rua", "Prova AS 2025.2 — Q3", 3)
def t06(c):
    c.eq("exemplo da prova", (5, [(0, 1), (1, 2), (2, 0), (2, 3), (3, 4)], [(0, 1), (2, 3), (3, 4)]), [2, -1, -1])
    c.eq("ciclo grande", (6, [(i, (i + 1) % 6) for i in range(6)], [(0, 1), (5, 0)]), [5, 5])
    c.eq("consulta na ordem invertida (b, a)", (3, [(0, 1), (1, 2), (0, 2)], [(1, 0)]), [2])

    def gera(rng):
        n = rng.randint(2, 15)
        e = [(u, v) for u, v, _ in grafo_aleatorio(rng, n, rng.randint(1, 2 * n), False)]
        q = [rng.choice(e) for _ in range(rng.randint(1, 5))]
        return (n, e, q)
    c.aleatorio("aleatórios vs gabarito", 150, gera, compara_gabarito("q06_rota_alternativa"))


@desempenho(6, "3.000 cruzamentos, 6.000 ruas, 300 consultas", 10)
def d06(seed):
    rng = random.Random(seed)
    e = [(u, v) for u, v, _ in grafo_aleatorio(rng, 3000, 6000, False, conexo=True)]
    q = [rng.choice(e) for _ in range(300)]
    esp = G.q06_rota_alternativa(3000, e, q)
    return (3000, e, q), lambda out: (list(out) == esp, "resposta diferente do gabarito")


def valida_q07(tasks, otimo):
    def v(out):
        val, nomes = out
        por_nome = {t.name: t for t in tasks}
        if len(set(nomes)) != len(nomes) or any(x not in por_nome for x in nomes):
            return False, f"nomes inválidos/repetidos: {curto(nomes)}"
        esc = sorted((por_nome[x] for x in nomes), key=lambda t: t.start)
        for a, b in zip(esc, esc[1:]):
            if a.end > b.start:
                return False, f"tarefas {a.name} e {b.name} se sobrepõem"
        soma = sum(t.value for t in esc)
        if soma != val:
            return False, f"valor retornado {val} ≠ soma das escolhidas {soma}"
        return val == otimo, f"valor {val}, o ótimo é {otimo}"
    return v


@teste(7, "Agendamento de tarefas com valor", "Simulado A2 2025.2 — Q3", 3)
def t07(c):
    T = G.Task
    ex = [T(1, 3, 50, "A"), T(4, 6, 30, "B"), T(7, 9, 30, "C"), T(2, 5, 20, "D"), T(5, 7, 40, "E"), T(6, 8, 60, "F")]
    c.valida("exemplo do simulado (140: A, B, F)", (ex,), valida_q07(ex, 140))
    c.valida("caso extra", ([T(0, 10, 100, "X"), T(0, 3, 30, "a"), T(3, 6, 30, "b"),
                                                       T(6, 10, 30, "c")],),
             valida_q07([T(0, 10, 100, "X"), T(0, 3, 30, "a"), T(3, 6, 30, "b"), T(6, 10, 30, "c")], 100))

    def gera(rng):
        n = rng.randint(1, 12)
        ts = []
        for i in range(n):
            s = rng.randint(0, 20)
            ts.append(T(s, s + rng.randint(1, 8), rng.randint(1, 50), f"t{i}"))
        return (ts,)

    def comp(args, out):
        return valida_q07(args[0], G.q07_agendamento_tarefas(copy.deepcopy(args[0]))[0])(out)
    c.aleatorio("aleatórios", 200, gera, comp)


@desempenho(7, "3.000 tarefas", 10)
def d07(seed):
    rng = random.Random(seed)
    ts = []
    for i in range(3000):
        s = rng.randint(0, 10 ** 6)
        ts.append(G.Task(s, s + rng.randint(1, 5000), rng.randint(1, 100), f"t{i}"))
    ot = G.q07_agendamento_tarefas(copy.deepcopy(ts))[0]
    return (ts,), valida_q07(ts, ot)


def valida_dij(n, adj, s, dist_esp):
    def v(out):
        dist, parent = out
        dist, parent = list(dist), list(parent)
        for i in range(n):
            if not perto(dist[i], dist_esp[i]):
                return False, f"dist[{i}] = {dist[i]}, correto = {dist_esp[i]}"
        if parent[s] != s:
            return False, f"parent[s] deveria ser s={s}, obtido {parent[s]}"
        for x in range(n):
            if x == s:
                continue
            if dist_esp[x] == INF:
                if parent[x] != -1:
                    return False, f"vértice {x} inalcançável deveria ter parent -1"
                continue
            p = parent[x]
            if not any(v2 == x and perto(dist_esp[p] + w, dist_esp[x]) for v2, w in adj[p]):
                return False, f"parent[{x}] = {p} não é um predecessor num caminho mínimo"
        return True, ""
    return v


def dist_bf(n, adj, s):
    edges = [(u, v, w) for u in range(n) for v, w in adj[u]]
    return G.q09_custos_com_negativos(n, edges, s)[1]


@teste(8, "Menores custos a partir de uma origem", "Slides 10 — Menor caminho", 3)
def t08(c):
    adj = [[(1, 4), (2, 1)], [(3, 1)], [(1, 2), (3, 5)], [], []]
    c.valida("grafo pequeno + vértice inalcançável", (5, adj, 0), valida_dij(5, adj, 0, [0, 3, 1, 4, INF]))
    adj0 = [[(1, 0)], [(2, 0)], [(0, 0)]]
    c.valida("pesos zero", (3, adj0, 0), valida_dij(3, adj0, 0, [0, 0, 0]))

    def gera(rng):
        n = rng.randint(1, 20)
        e = grafo_aleatorio(rng, n, rng.randint(0, 4 * n), True, 0, 30)
        return (n, adj_de(n, e), rng.randrange(n))

    def comp(args, out):
        return valida_dij(*args, dist_bf(*args))(out)
    c.aleatorio("aleatórios vs referência", 200, gera, comp)


@desempenho(8, "100.000 vértices, 300.000 arestas", 10)
def d08(seed):
    rng = random.Random(seed)
    n = 100000
    e = grafo_aleatorio(rng, n, 300000, True, 1, 10 ** 6, conexo=True)
    adj = adj_de(n, e)
    esp = G.q08_menores_custos(n, adj, 0)[0]
    return (n, adj, 0), valida_dij(n, adj, 0, esp)


@teste(9, "Menores custos com pesos negativos", "Slides 10 — Menor caminho", 3)
def t09(c):
    e = [(0, 1, 4), (0, 2, 5), (2, 1, -3), (1, 3, 2)]
    c.eq("aresta negativa sem ciclo", (4, e, 0), (True, [0, 2, 5, 4]))
    e2 = [(0, 1, 1), (1, 2, -2), (2, 1, 1), (2, 3, 1)]
    c.eq("ciclo negativo alcançável", (4, e2, 0), False, normaliza=lambda r: r if r is False else r[0])
    e3 = [(0, 1, 2), (2, 3, -5), (3, 2, 1)]
    c.eq("ciclo negativo NÃO alcançável -> ok", (4, e3, 0), (True, [0, 2, INF, INF]))

    def gera(rng):
        n = rng.randint(1, 12)
        return (n, grafo_aleatorio(rng, n, rng.randint(0, 3 * n), True, -4, 12), rng.randrange(n))

    def comp(args, out):
        ok_e, d_e = G.q09_custos_com_negativos(*args)
        ok_o, d_o = out
        if ok_o != ok_e:
            return False, f"ok esperado {ok_e}, obtido {ok_o}"
        return (not ok_e) or list(d_o) == d_e, f"dist esperado {d_e}, obtido {curto(d_o)}"
    c.aleatorio("aleatórios vs gabarito", 250, gera, comp)


@desempenho(9, "1.000 vértices, 6.000 arestas", 10)
def d09(seed):
    rng = random.Random(seed)
    e = dag_aleatorio(rng, 1000, 6000, -20, 50)
    esp = G.q09_custos_com_negativos(1000, e, 0)
    return (1000, e, 0), lambda out: (out[0] == esp[0] and list(out[1]) == esp[1], "dist diferente do esperado")


def valida_mst(n, edges, custo_otimo):
    pool = Counter((min(u, v), max(u, v), w) for u, v, w in edges)

    def v(out):
        if custo_otimo is None:
            return out is None, "grafo desconexo: esperado None"
        if out is None:
            return False, "retornou None mas o grafo é conexo"
        custo, arestas = out
        arestas = [tuple(a) for a in arestas]
        if len(arestas) != n - 1:
            return False, f"a árvore deve ter n-1 = {n - 1} arestas, tem {len(arestas)}"
        usado = Counter((min(u, v), max(u, v), w) for u, v, w in arestas)
        if any(usado[k] > pool[k] for k in usado):
            return False, "usou aresta que não existe na entrada"
        if not conecta_todos(range(n), [(u, v) for u, v, _ in arestas]):
            return False, "as arestas não formam uma árvore geradora"
        if sum(w for _, _, w in arestas) != custo:
            return False, "custo retornado ≠ soma das arestas"
        return custo == custo_otimo, f"custo {custo}, ótimo {custo_otimo}"
    return v


def custo_mst(n, edges):
    r = G.q10_arvore_minima_arestas(n, edges)
    return None if r is None else r[0]


EX_MST = [(u - 1, v - 1, w) for u, v, w in EX_Q01]


@teste(10, "Árvore geradora mínima (lista de arestas)", "Slides 11 — Árvore geradora mínima", 3)
def t10(c):
    c.valida("grafo da prova A2 (custo 16)", (9, EX_MST), valida_mst(9, EX_MST, 16))
    c.valida("desconexo -> None", (4, [(0, 1, 1), (2, 3, 1)]), valida_mst(4, [(0, 1, 1), (2, 3, 1)], None))
    c.valida("um vértice", (1, []), valida_mst(1, [], 0))
    neg = [(0, 1, -5), (1, 2, 3), (0, 2, -1)]
    c.valida("custos negativos", (3, neg), valida_mst(3, neg, -6))

    def gera(rng):
        n = rng.randint(1, 20)
        return (n, grafo_aleatorio(rng, n, rng.randint(0, 3 * n), False, -5, 30, conexo=rng.random() < .85))

    def comp(args, out):
        return valida_mst(*args, custo_mst(*args))(out)
    c.aleatorio("aleatórios", 200, gera, comp)


@desempenho(10, "100.000 vértices, 200.000 arestas", 8)
def d10(seed):
    rng = random.Random(seed)
    e = grafo_aleatorio(rng, 100000, 200000, False, 1, 10 ** 6, conexo=True)
    return (100000, e), valida_mst(100000, e, custo_mst(100000, e))


def valida_prim(n, adj, custo_otimo):
    def v(out):
        if custo_otimo is None:
            return out is None, "grafo desconexo: esperado None"
        if out is None:
            return False, "retornou None mas o grafo é conexo"
        custo, parent = out
        parent = list(parent)
        if parent[0] != 0:
            return False, "parent[0] deveria ser 0"
        soma, arestas = 0, []
        for x in range(1, n):
            p = parent[x]
            ws = [w for y, w in adj[p] if y == x] if 0 <= p < n else []
            if not ws:
                return False, f"aresta ({p}, {x}) não existe"
            soma += min(ws)
            arestas.append((p, x))
        if not conecta_todos(range(n), arestas):
            return False, "parent não define uma árvore"
        if soma != custo:
            return False, f"custo retornado {custo} ≠ soma das arestas do parent {soma}"
        return custo == custo_otimo, f"custo {custo}, ótimo {custo_otimo}"
    return v


@teste(11, "Árvore geradora mínima (lista de adjacência)", "Slides 11 — Árvore geradora mínima", 3)
def t11(c):
    adj = adj_de(9, EX_MST, dirigido=False)
    c.valida("grafo da prova A2 (custo 16)", (9, adj), valida_prim(9, adj, 16))
    a2 = adj_de(4, [(0, 1, 1), (2, 3, 1)], dirigido=False)
    c.valida("desconexo -> None", (4, a2), valida_prim(4, a2, None))

    def gera(rng):
        n = rng.randint(1, 20)
        e = grafo_aleatorio(rng, n, rng.randint(0, 3 * n), False, -5, 30, conexo=rng.random() < .85)
        return (n, adj_de(n, e, dirigido=False))

    def comp(args, out):
        n, adj = args
        e = [(u, v, w) for u in range(n) for v, w in adj[u] if u < v]
        return valida_prim(n, adj, custo_mst(n, e))(out)
    c.aleatorio("aleatórios", 200, gera, comp)


@desempenho(11, "100.000 vértices, 200.000 arestas", 8)
def d11(seed):
    rng = random.Random(seed)
    e = grafo_aleatorio(rng, 100000, 200000, False, 1, 10 ** 6, conexo=True)
    adj = adj_de(100000, e, dirigido=False)
    return (100000, adj), valida_prim(100000, adj, custo_mst(100000, e))


CLRS = [(0, 1, 16), (0, 2, 13), (1, 3, 12), (2, 1, 4), (2, 4, 14), (3, 2, 9), (3, 5, 20), (4, 3, 7), (4, 5, 4)]


@teste(12, "Fluxo máximo", "Slides 12 — Fluxo máximo", 3)
def t12(c):
    c.eq("rede clássica do Cormen (23)", (6, CLRS, 0, 5), 23)
    c.eq("caso-armadilha", (4, [(0, 1, 1), (0, 2, 1), (1, 2, 1), (1, 3, 1), (2, 3, 1)], 0, 3), 2)
    c.eq("arestas paralelas", (2, [(0, 1, 3), (0, 1, 4)], 0, 1), 7)
    c.eq("arestas antiparalelas", (3, [(0, 1, 5), (1, 0, 5), (1, 2, 3)], 0, 2), 3)
    c.eq("sem caminho", (3, [(0, 1, 5)], 0, 2), 0)

    def gera(rng):
        n = rng.randint(2, 10)
        return (n, grafo_aleatorio(rng, n, rng.randint(0, 4 * n), True, 1, 15), 0, n - 1)
    c.aleatorio("aleatórios vs gabarito", 200, gera, compara_gabarito("q12_fluxo_maximo"))


@desempenho(12, "capacidades enormes", 6)
def d12a(seed):
    C = 10 ** 9
    e = [(0, 1, C), (0, 2, C), (1, 2, 1), (1, 3, C), (2, 3, C)]
    return (4, e, 0, 3), lambda out: (out == 2 * C, f"esperado {2 * C}, obtido {out}")


@desempenho(12, "500 vértices, 5.000 arestas", 10)
def d12b(seed):
    rng = random.Random(seed)
    e = grafo_aleatorio(rng, 500, 5000, True, 1, 1000)
    esp = G.q12_fluxo_maximo(500, e, 0, 499)
    return (500, e, 0, 499), lambda out: (out == esp, f"esperado {esp}, obtido {out}")


def valida_topo(n, adj, existe):
    def v(out):
        if not existe:
            return out is None, f"há ciclo: esperado None, obtido {curto(out)}"
        if out is None:
            return False, "retornou None, mas o grafo é um DAG"
        out = list(out)
        if sorted(out) != list(range(n)):
            return False, "não é uma permutação dos vértices"
        pos = {v2: i for i, v2 in enumerate(out)}
        for u in range(n):
            for w in adj[u]:
                if pos[u] > pos[w]:
                    return False, f"aresta {u}->{w} aponta para trás na ordem"
        return True, ""
    return v


@teste(13, "Ordem topológica", "Slides 09 — Busca em grafos", 3)
def t13(c):
    adj = [[1, 2], [3], [3], [4], []]
    c.valida("DAG pequeno", (5, adj), valida_topo(5, adj, True))
    cic = [[1], [2], [0]]
    c.valida("ciclo -> None", (3, cic), valida_topo(3, cic, False))
    c.valida("laço (u->u) -> None", (2, [[0], []]), valida_topo(2, [[0], []], False))
    c.valida("sem arestas", (3, [[], [], []]), valida_topo(3, [[], [], []], True))

    def gera(rng):
        n = rng.randint(1, 15)
        if rng.random() < .6:
            e = dag_aleatorio(rng, n, rng.randint(0, 3 * n))
        else:
            e = grafo_aleatorio(rng, n, rng.randint(0, 2 * n))
        return (n, adj_de(n, e, peso=False))

    def comp(args, out):
        return valida_topo(*args, G.q13_ordem_topologica(*args) is not None)(out)
    c.aleatorio("aleatórios", 250, gera, comp)


@desempenho(13, "100.000 vértices, 300.000 arestas", 6)
def d13(seed):
    rng = random.Random(seed)
    e = dag_aleatorio(rng, 100000, 300000)
    adj = adj_de(100000, e, peso=False)
    return (100000, adj), valida_topo(100000, adj, True)


@teste(14, "Viagem intergaláctica com cupom", "Lista 3 — Q6", 3)
def t14(c):
    c.eq("exemplo 1", (3, [(1, 2, 3), (2, 3, 1), (1, 3, 7)]), 2)
    c.eq("exemplo 2", (3, [(1, 2, 3), (2, 3, 3), (1, 3, 7)]), 3)
    c.eq("caso extra", (3, [(1, 2, 1), (2, 3, 100), (1, 3, 60)]), 30)
    c.eq("inalcançável -> -1", (3, [(1, 2, 5)]), -1)

    def gera(rng):
        n = rng.randint(2, 15)
        return (n, [(u + 1, v + 1, w) for u, v, w in grafo_aleatorio(rng, n, rng.randint(1, 4 * n), True, 1, 50)])
    c.aleatorio("aleatórios vs gabarito", 200, gera, compara_gabarito("q14_viagem_cupom"))


@desempenho(14, "100.000 planetas, 200.000 rotas", 12)
def d14(seed):
    rng = random.Random(seed)
    e = [(u + 1, v + 1, w) for u, v, w in grafo_aleatorio(rng, 100000, 200000, True, 1, 10 ** 9, conexo=True)]
    esp = G.q14_viagem_cupom(100000, e)
    return (100000, e), lambda out: (out == esp, f"esperado {esp}, obtido {out}")


@teste(15, "Reparo das estradas", "Lista 3 — Q7", 3)
def t15(c):
    c.eq("exemplo 1", (5, [(1, 2, 3), (2, 3, 5), (2, 4, 2), (3, 4, 8), (5, 1, 7), (5, 4, 4)]), 14)
    c.eq("exemplo 2", (5, [(1, 2, 3), (2, 3, 5), (2, 4, 2), (3, 4, 0), (5, 1, 7), (5, 4, 4)]), 9)
    c.eq("exemplo 3", (2, [(1, 2, 0)]), 0)
    c.eq("impossível -> -1", (4, [(1, 2, 1), (3, 4, 1)]), -1)

    def gera(rng):
        n = rng.randint(1, 20)
        e = grafo_aleatorio(rng, n, rng.randint(0, 3 * n), False, 0, 30, conexo=rng.random() < .8)
        return (n, [(u + 1, v + 1, w) for u, v, w in e])
    c.aleatorio("aleatórios vs gabarito", 200, gera, compara_gabarito("q15_reparo_estradas"))


@desempenho(15, "100.000 cidades, 200.000 estradas", 8)
def d15(seed):
    rng = random.Random(seed)
    e = [(u + 1, v + 1, w) for u, v, w in grafo_aleatorio(rng, 100000, 200000, False, 0, 10 ** 9, conexo=True)]
    esp = G.q15_reparo_estradas(100000, e)
    return (100000, e), lambda out: (out == esp, f"esperado {esp}, obtido {out}")


@teste(16, "Quantas formas de zerar o jogo", "Lista 3 — Q8", 3)
def t16(c):
    c.eq("exemplo 1", (3, [(1, 2), (2, 3)]), 1)
    c.eq("exemplo 2", (5, [(1, 3), (3, 4), (1, 2), (2, 5), (1, 4), (4, 5), (3, 5)]), 4)
    c.eq("exemplo 3", (3, [(1, 2), (3, 2)]), 0)
    c.eq("n = 1", (1, []), 1)

    def gera(rng):
        n = rng.randint(1, 12)
        perm = list(range(1, n + 1))
        rng.shuffle(perm)
        e = [(perm[u], perm[v]) for u, v, _ in dag_aleatorio(rng, n, rng.randint(0, 3 * n))]
        return (n, e)

    def comp(args, out):
        n, e = args
        adj = {}
        for a, b in e:
            adj.setdefault(a, []).append(b)

        def conta(u):
            return 1 if u == n else sum(conta(v) for v in adj.get(u, []))
        esp = conta(1)
        return out == esp, f"esperado {esp}, obtido {out}"
    c.aleatorio("aleatórios vs força bruta", 200, gera, comp)


@desempenho(16, "100.000 estados, 200.000 transições", 6)
def d16(seed):
    rng = random.Random(seed)
    n, K = 100000, 50000
    e = [(i, i + 1) for i in range(1, K)] + [(K, n)]
    while len(e) < 200000:
        a = rng.randint(1, n - 1)
        b = rng.randint(max(a + 1, K + 1), n - 1) if a < n - 1 else None
        if b and b > a:
            e.append((a, b))
    rng.shuffle(e)
    return (n, e), lambda out: (out == 1, f"esperado 1, obtido {out}")


Q17_EX = [
    (["########", "#A..V..#", "#.#.A#.#", "#A#..#..", "#.######"], 5),
    (["########", "#...V..#", "#.#..#.#", "#.A..A..", "#.######"], -1),
    (["########", "#A..#..#", "#.#.A#.#", "#A#..#.V", "#.######"], 0),
]


@teste(17, "Escape se for possível", "Lista 3 — Q5", 3)
def t17(c):
    for i, (g, esp) in enumerate(Q17_EX, 1):
        c.eq(f"exemplo {i}", (g,), esp)
    c.eq("caso-armadilha", (["#####", "#V.A#", "##.##"],), -1)
    c.eq("sem água", (["#####", "#V..#", "####."],), -1)
    c.eq("sem água, com saída", (["#####", "#V...", "#####"],), 3)

    def gera(rng):
        n, m = rng.randint(1, 8), rng.randint(1, 8)
        g = [[rng.choice("..#") for _ in range(m)] for _ in range(n)]
        cel = [(i, j) for i in range(n) for j in range(m)]
        vi, vj = rng.choice(cel)
        g[vi][vj] = 'V'
        for _ in range(rng.randint(0, 2)):
            i, j = rng.choice(cel)
            if g[i][j] != 'V':
                g[i][j] = 'A'
        return (["".join(r) for r in g],)
    c.aleatorio("aleatórios vs gabarito", 300, gera, compara_gabarito("q17_escape_caverna"))


@desempenho(17, "grid 600 x 600", 10)
def d17(seed):
    n = 600
    g = [["."] * n for _ in range(n)]
    for i in range(n):
        g[i][0] = g[i][n - 1] = "#"
        g[0][i] = g[n - 1][i] = "#"
    g[n - 1][n // 2] = "."
    g[n // 2][n // 2] = "V"
    g[1][1] = "A"
    g = ["".join(r) for r in g]
    esp = G.q17_escape_caverna(g)
    return (g,), lambda out: (out == esp, f"esperado {esp}, obtido {out}")


@teste(18, "Cavalo no tabuleiro", "Lista 3 — Q4", 3)
def t18(c):
    c.eq("exemplo n = 8", (8,), G.q18_cavalo(8))
    c.eq("n = 3", (3,), [[0, 3, 2], [3, -1, 1], [2, 1, 4]])
    for n in (4, 5, 11):
        c.eq(f"n = {n}", (n,), G.q18_cavalo(n))


@desempenho(18, "n = 700", 12)
def d18(seed):
    esp = G.q18_cavalo(700)
    return (700,), lambda out: (out == esp, "matriz diferente do esperado")


def norm_pontes(L):
    return sorted((min(a, b), max(a, b)) for a, b in L)


@teste(19, "Todas as pontes (conexões críticas)", "Externa — LeetCode 1192", 3)
def t19(c):
    c.eq("exemplo", (4, [(0, 1), (1, 2), (2, 0), (1, 3)]), [(1, 3)], normaliza=norm_pontes)
    c.eq("árvore", (4, [(0, 1), (1, 2), (1, 3)]), [(0, 1), (1, 2), (1, 3)], normaliza=norm_pontes)
    c.eq("ciclo", (4, [(0, 1), (1, 2), (2, 3), (3, 0)]), [], normaliza=norm_pontes)
    c.eq("dois ciclos ligados por ponte", (6, [(0, 1), (1, 2), (2, 0), (2, 3), (3, 4), (4, 5), (5, 3)]),
         [(2, 3)], normaliza=norm_pontes)

    def gera(rng):
        n = rng.randint(2, 15)
        return (n, [(u, v) for u, v, _ in grafo_aleatorio(rng, n, rng.randint(n - 1, 2 * n), False, conexo=True)])

    def comp(args, out):
        n, e = args
        g = [[] for _ in range(n)]
        for u, v in e:
            g[u].append(v); g[v].append(u)
        esp = [(u, v) for u, v in e if G.q05_eh_ponte(copy.deepcopy(g), n, u, v)]
        return norm_pontes(out) == norm_pontes(esp), f"esperado {norm_pontes(esp)}, obtido {curto(out)}"
    c.aleatorio("aleatórios vs força bruta", 200, gera, comp)


@desempenho(19, "50.000 vértices, 70.000 arestas", 8)
def d19(seed):
    rng = random.Random(seed)
    e = [(u, v) for u, v, _ in grafo_aleatorio(rng, 50000, 70000, False, conexo=True)]
    esp = norm_pontes(G.q19_todas_as_pontes(50000, e))
    return (50000, e), lambda out: (norm_pontes(out) == esp, "conjunto de pontes diferente")


@teste(20, "Velocidade de download", "Externa — CSES 1694", 3)
def t20(c):
    c.eq("exemplo", (4, [(1, 2, 3), (2, 4, 2), (1, 3, 4), (3, 4, 5), (4, 1, 3)]), 6)
    c.eq("sem conexão", (3, [(1, 2, 5)]), 0)

    def gera(rng):
        n = rng.randint(2, 10)
        return (n, [(u + 1, v + 1, w) for u, v, w in grafo_aleatorio(rng, n, rng.randint(0, 4 * n), True, 1, 20)])
    c.aleatorio("aleatórios vs gabarito", 200, gera, compara_gabarito("q20_velocidade_download"))


@desempenho(20, "500 computadores, 1.000 conexões", 8)
def d20(seed):
    rng = random.Random(seed)
    e = [(u + 1, v + 1, w) for u, v, w in grafo_aleatorio(rng, 500, 1000, True, 1, 10 ** 9)]
    esp = G.q20_velocidade_download(500, e)
    return (500, e), lambda out: (out == esp, f"esperado {esp}, obtido {out}")


# ===========================================================================
# ★★ MÉDIA
# ===========================================================================
@teste(21, "Plataformas de trem", "Prova AS 2025.2 — Q2", 2)
def t21(c):
    c.eq("exemplo 1", ([(1100, 1130), (900, 910), (950, 1120), (940, 1200)],), 3)
    c.eq("exemplo 2 (partida == chegada compartilha)", ([(100, 200), (200, 300)],), 1)
    c.eq("todos ao mesmo tempo", ([(1, 5)] * 4,), 4)

    def gera(rng):
        ts = []
        for _ in range(rng.randint(1, 10)):
            a = rng.randint(0, 20)
            ts.append((a, a + rng.randint(1, 6)))
        return (ts,)

    def comp(args, out):
        ts = args[0]
        pts = sorted({t for p in ts for t in p})
        esp = 0
        for t in pts:      # força bruta: trens ocupando o instante t (chegada <= t < partida)
            esp = max(esp, sum(1 for a, b in ts if a <= t < b))
        return out == esp, f"esperado {esp}, obtido {out}"
    c.aleatorio("aleatórios vs força bruta", 300, gera, comp)


@desempenho(21, "200.000 trens", 6)
def d21(seed):
    rng = random.Random(seed)
    ts = []
    for _ in range(200000):
        a = rng.randint(0, 10 ** 6)
        ts.append((a, a + rng.randint(1, 1000)))
    esp = G.q21_plataformas_trem(ts)
    return (ts,), lambda out: (out == esp, f"esperado {esp}, obtido {out}")


@teste(22, "Par de pontos mais próximo", "Prova AS 2025.2 — Q1 / Slides 07", 2)
def t22(c):
    c.valida("pequeno", ([(0, 0), (5, 5), (1, 1), (9, 0), (5, 6)],), lambda o: (perto(o, 1.0), f"esperado 1.0, obtido {o}"))
    c.valida("pontos repetidos", ([(2, 2), (7, 1), (2, 2)],), lambda o: (perto(o, 0.0), f"esperado 0, obtido {o}"))

    def gera(rng):
        return ([(rng.uniform(-50, 50), rng.uniform(-50, 50)) for _ in range(rng.randint(2, 40))],)

    def comp(args, out):
        P = args[0]
        esp = min(math.dist(p, q) for p, q in combinations(P, 2))
        return perto(out, esp), f"esperado {esp}, obtido {out}"
    c.aleatorio("aleatórios vs força bruta", 200, gera, comp)


@desempenho(22, "50.000 pontos", 10)
def d22(seed):
    rng = random.Random(seed)
    P = [(rng.uniform(0, 10 ** 6), rng.uniform(0, 10 ** 6)) for _ in range(50000)]
    esp = G.q22_menor_distancia_pontos(P)
    return (P,), lambda out: (perto(out, esp), f"esperado {esp}, obtido {out}")


@teste(23, "Detectar ciclo em grafo dirigido", "Slides 09 — Busca em grafos", 2)
def t23(c):
    c.eq("ciclo", (3, [[1], [2], [0]]), True)
    c.eq("losango", (4, [[1, 2], [3], [3], []]), False)
    c.eq("laço", (1, [[0]]), True)
    c.eq("ciclo em componente que não é a primeira", (4, [[], [2], [3], [1]]), True)

    def gera(rng):
        n = rng.randint(1, 12)
        e = dag_aleatorio(rng, n, rng.randint(0, 2 * n)) if rng.random() < .5 else grafo_aleatorio(rng, n, rng.randint(0, 2 * n))
        return (n, adj_de(n, e, peso=False))
    c.aleatorio("aleatórios vs gabarito", 250, gera, compara_gabarito("q23_tem_ciclo_dirigido"))


@desempenho(23, "caminho de 100.000 vértices", 6)
def d23(seed):
    n = 100000
    adj = [[i + 1] for i in range(n - 1)] + [[]]
    return (n, adj), lambda out: (out is False, f"esperado False, obtido {out}")


@teste(24, "Classificar arestas", "Slides 09 — Busca em grafos", 2)
def t24(c):
    adj = [[1, 2], [3, 4], [4], [4], [5, 1], []]
    c.eq("exemplo", (6, adj), G.q24_classificar_arestas(6, adj))
    adj2 = [[1], [2], [0, 3], [], [3, 1]]
    c.eq("caso extra", (5, adj2), G.q24_classificar_arestas(5, adj2))

    def gera(rng):
        n = rng.randint(1, 10)
        return (n, adj_de(n, grafo_aleatorio(rng, n, rng.randint(0, 3 * n)), peso=False))
    c.aleatorio("aleatórios vs gabarito", 250, gera, compara_gabarito("q24_classificar_arestas"))


def valida_corte(n, edges, s, t, otimo):
    pool = Counter(tuple(e) for e in edges)

    def v(out):
        val, corte = out
        corte = [tuple(e) for e in corte]
        if val != otimo:
            return False, f"capacidade {val}, o fluxo máximo é {otimo}"
        usado = Counter(corte)
        if any(usado[k] > pool[k] for k in usado):
            return False, "corte contém aresta que não existe"
        if sum(cc for _, _, cc in corte) != otimo:
            return False, f"soma das capacidades do corte = {sum(cc for _, _, cc in corte)} ≠ {otimo}"
        resto = pool - usado
        arcos = [(u, v2) for (u, v2, cc), k in resto.items() if cc > 0 for _ in range(k)]
        return not alcanca(n, arcos, s, t), "removendo o corte, t ainda é alcançável a partir de s"
    return v


@teste(25, "Corte mínimo", "Slides 12 — Fluxo máximo", 2)
def t25(c):
    c.valida("rede do Cormen", (6, CLRS, 0, 5), valida_corte(6, CLRS, 0, 5, 23))

    def gera(rng):
        n = rng.randint(2, 9)
        return (n, grafo_aleatorio(rng, n, rng.randint(0, 4 * n), True, 1, 15), 0, n - 1)

    def comp(args, out):
        return valida_corte(*args, G.q12_fluxo_maximo(*args))(out)
    c.aleatorio("aleatórios", 200, gera, comp)


@teste(26, "Caminho mais barato em DAG", "Slides 10 — Menor caminho em DAG", 2)
def t26(c):
    e = [(3, 1, 2), (3, 2, 6), (1, 2, -3), (2, 0, 1), (1, 0, 5)]
    c.eq("peso negativo", (4, e, 3), [0, 2, -1, 0])
    c.eq("inalcançáveis", (3, [(1, 2, 1)], 0), [0, INF, INF])

    def gera(rng):
        n = rng.randint(1, 15)
        return (n, dag_aleatorio(rng, n, rng.randint(0, 3 * n), -10, 20), rng.randrange(n))

    def comp(args, out):
        esp = G.q09_custos_com_negativos(*args)[1]
        return list(out) == esp, f"esperado {esp}, obtido {curto(out)}"
    c.aleatorio("aleatórios vs referência", 250, gera, comp)


@desempenho(26, "100.000 vértices, 300.000 arestas", 6)
def d26(seed):
    rng = random.Random(seed)
    e = dag_aleatorio(rng, 100000, 300000, -100, 100)
    esp = G.q26_menor_caminho_dag(100000, e, e[0][0])
    return (100000, e, e[0][0]), lambda out: (list(out) == esp, "dist diferente do esperado")


@teste(27, "Grafo bipartido", "Slides 08 / LeetCode 785", 2)
def t27(c):
    def und(n, e):
        return adj_de(n, [(u, v, 0) for u, v in e], dirigido=False, peso=False)
    c.eq("ciclo par", (4, und(4, [(0, 1), (1, 2), (2, 3), (3, 0)])), True)
    c.eq("ciclo ímpar", (3, und(3, [(0, 1), (1, 2), (2, 0)])), False)
    c.eq("desconexo", (5, und(5, [(0, 1), (2, 3), (3, 4), (4, 2)])), False)

    def gera(rng):
        n = rng.randint(1, 12)
        return (n, adj_de(n, grafo_aleatorio(rng, n, rng.randint(0, 2 * n), False), dirigido=False, peso=False))

    def comp(args, out):
        n, adj = args
        e = {(u, v) for u in range(n) for v in adj[u]}
        esp = any(all(((m >> u) & 1) != ((m >> v) & 1) for u, v in e) for m in range(1 << n))
        return out == esp, f"esperado {esp}, obtido {out}"
    c.aleatorio("aleatórios vs força bruta", 200, gera, comp)


@teste(28, "Tempo de atraso da rede", "Externa — LeetCode 743", 2)
def t28(c):
    c.eq("exemplo", ([(2, 1, 1), (2, 3, 1), (3, 4, 1)], 4, 2), 2)
    c.eq("inalcançável", ([(1, 2, 1)], 2, 2), -1)

    def gera(rng):
        n = rng.randint(1, 12)
        return ([(u + 1, v + 1, w) for u, v, w in grafo_aleatorio(rng, n, rng.randint(0, 4 * n), True, 0, 30)],
                n, rng.randint(1, n))
    c.aleatorio("aleatórios vs gabarito", 200, gera, compara_gabarito("q28_tempo_atraso_rede"))


@teste(29, "Voo mais barato com até k escalas", "Externa — LeetCode 787", 2)
def t29(c):
    c.eq("exemplo", (4, [(0, 1, 100), (1, 2, 100), (2, 0, 100), (1, 3, 600), (2, 3, 200)], 0, 3, 1), 700)
    c.eq("k = 0", (3, [(0, 1, 100), (1, 2, 100), (0, 2, 500)], 0, 2, 0), 500)
    c.eq("k = 1", (3, [(0, 1, 100), (1, 2, 100), (0, 2, 500)], 0, 2, 1), 200)

    def gera(rng):
        n = rng.randint(2, 9)
        return (n, grafo_aleatorio(rng, n, rng.randint(0, 3 * n), True, 1, 50), 0, n - 1, rng.randint(0, 4))

    def comp(args, out):
        n, fl, s, d, k = args
        best = INF
        pilha = [(s, 0, 0)]
        while pilha:                       # força bruta por profundidade limitada
            u, cst, voos = pilha.pop()
            if u == d:
                best = min(best, cst)
            if voos == k + 1:
                continue
            for a, b, w in fl:
                if a == u:
                    pilha.append((b, cst + w, voos + 1))
        esp = -1 if best == INF else best
        return out == esp, f"esperado {esp}, obtido {out}"
    c.aleatorio("aleatórios vs força bruta", 150, gera, comp)


@teste(30, "Custo mínimo para conectar todos os pontos", "Externa — LeetCode 1584", 2)
def t30(c):
    c.eq("exemplo", ([(0, 0), (2, 2), (3, 10), (5, 2), (7, 0)],), 20)
    c.eq("um ponto", ([(4, 4)],), 0)

    def gera(rng):
        return ([(rng.randint(-20, 20), rng.randint(-20, 20)) for _ in range(rng.randint(1, 15))],)

    def comp(args, out):
        P = args[0]
        e = [(i, j, abs(P[i][0] - P[j][0]) + abs(P[i][1] - P[j][1])) for i in range(len(P)) for j in range(i)]
        esp = custo_mst(len(P), e)
        return out == esp, f"esperado {esp}, obtido {out}"
    c.aleatorio("aleatórios vs referência", 150, gera, comp)


@desempenho(30, "1.500 pontos", 10)
def d30(seed):
    rng = random.Random(seed)
    P = [(rng.randint(-10 ** 6, 10 ** 6), rng.randint(-10 ** 6, 10 ** 6)) for _ in range(1500)]
    esp = G.q30_conectar_pontos(P)
    return (P,), lambda out: (out == esp, f"esperado {esp}, obtido {out}")


@teste(31, "Grade de cursos", "Externa — LeetCode 207", 2)
def t31(c):
    c.eq("possível", (2, [(1, 0)]), True)
    c.eq("ciclo", (2, [(1, 0), (0, 1)]), False)

    def gera(rng):
        n = rng.randint(1, 12)
        e = dag_aleatorio(rng, n, rng.randint(0, 2 * n)) if rng.random() < .5 else grafo_aleatorio(rng, n, rng.randint(0, 2 * n))
        return (n, [(v, u) for u, v, _ in e])
    c.aleatorio("aleatórios vs gabarito", 200, gera, compara_gabarito("q31_pode_concluir_cursos"))


@teste(32, "Número de ilhas", "Externa — LeetCode 200", 2)
def t32(c):
    c.eq("exemplo 1", (["11110", "11010", "11000", "00000"],), 1)
    c.eq("exemplo 2", (["11000", "11000", "00100", "00011"],), 3)
    c.eq("caso extra", (["101", "010", "101"],), 5)

    def gera(rng):
        n, m = rng.randint(1, 8), rng.randint(1, 8)
        return (["".join(rng.choice("01") for _ in range(m)) for _ in range(n)],)
    c.aleatorio("aleatórios vs gabarito", 200, gera, compara_gabarito("q32_numero_ilhas"))


@teste(33, "Laranjas podres", "Externa — LeetCode 994", 2)
def t33(c):
    c.eq("exemplo 1", ([[2, 1, 1], [1, 1, 0], [0, 1, 1]],), 4)
    c.eq("impossível", ([[2, 1, 1], [0, 1, 1], [1, 0, 1]],), -1)
    c.eq("nenhuma laranja boa", ([[0, 2]],), 0)

    def gera(rng):
        n, m = rng.randint(1, 7), rng.randint(1, 7)
        return ([[rng.choice([0, 1, 1, 2]) for _ in range(m)] for _ in range(n)],)
    c.aleatorio("aleatórios vs gabarito", 200, gera, compara_gabarito("q33_laranjas_podres"))


@teste(34, "Conexão redundante", "Externa — LeetCode 684", 2)
def t34(c):
    c.eq("exemplo 1", ([(1, 2), (1, 3), (2, 3)],), (2, 3), normaliza=tuple)
    c.eq("exemplo 2", ([(1, 2), (2, 3), (3, 4), (1, 4), (1, 5)],), (1, 4), normaliza=tuple)

    def gera(rng):
        n = rng.randint(3, 15)
        e = [(rng.randint(1, v - 1), v) for v in range(2, n + 1)]
        while True:
            a, b = rng.sample(range(1, n + 1), 2)
            if (a, b) not in e and (b, a) not in e:
                break
        e.insert(rng.randint(0, len(e)), (a, b))
        return (e,)
    c.aleatorio("aleatórios vs gabarito", 200, gera, compara_gabarito("q34_conexao_redundante", tuple))


@teste(35, "Caminho com menor esforço", "Externa — LeetCode 1631", 2)
def t35(c):
    c.eq("exemplo 1", ([[1, 2, 2], [3, 8, 2], [5, 3, 5]],), 2)
    c.eq("exemplo 2", ([[1, 2, 3], [3, 8, 4], [5, 3, 5]],), 1)
    c.eq("uma casa", ([[7]],), 0)

    def gera(rng):
        n, m = rng.randint(1, 6), rng.randint(1, 6)
        return ([[rng.randint(1, 30) for _ in range(m)] for _ in range(n)],)

    def comp(args, out):
        H = args[0]
        n, m = len(H), len(H[0])
        for lim in range(0, 31):      # menor limiar que conecta (força bruta por BFS)
            vis = {(0, 0)}
            fila = deque([(0, 0)])
            while fila:
                a, b = fila.popleft()
                for x, y in ((a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)):
                    if 0 <= x < n and 0 <= y < m and (x, y) not in vis and abs(H[x][y] - H[a][b]) <= lim:
                        vis.add((x, y)); fila.append((x, y))
            if (n - 1, m - 1) in vis:
                return out == lim, f"esperado {lim}, obtido {out}"
        return False, "?"
    c.aleatorio("aleatórios vs força bruta", 150, gera, comp)


@teste(36, "Número de caminhos mais curtos", "Externa — LeetCode 1976", 2)
def t36(c):
    c.eq("exemplo", (7, [(0, 6, 7), (0, 1, 2), (1, 2, 3), (1, 3, 3), (6, 3, 3), (3, 5, 1), (6, 5, 1), (2, 5, 1),
                         (0, 4, 5), (4, 6, 2)]), 4)
    c.eq("n = 2", (2, [(1, 0, 10)]), 1)

    def gera(rng):
        n = rng.randint(2, 9)
        return (n, grafo_aleatorio(rng, n, rng.randint(n - 1, 3 * n), False, 1, 4, conexo=True))

    def comp(args, out):
        n, roads = args
        adj = adj_de(n, roads, dirigido=False)
        d = dist_bf(n, [[(v, w) for v, w in adj[u]] for u in range(n)], 0)
        memo = {}

        def conta(u):          # caminhos mínimos de 0 até u (DAG de arestas "tight")
            if u == 0:
                return 1
            if u not in memo:
                memo[u] = sum(conta(p) for p in range(n) for v, w in adj[p] if v == u and d[p] + w == d[u])
            return memo[u]
        esp = conta(n - 1) % (10 ** 9 + 7)
        return out == esp, f"esperado {esp}, obtido {out}"
    c.aleatorio("aleatórios vs referência", 150, gera, comp)


@teste(37, "Maior pontuação", "Externa — CSES 1673", 2)
def t37(c):
    c.eq("exemplo", (4, [(1, 2, 3), (2, 4, -1), (1, 3, -2), (3, 4, 7)]), 5)
    c.eq("caso extra 1", (3, [(1, 2, 1), (2, 1, 1), (2, 3, 1)]), -1)
    c.eq("caso extra 2", (4, [(1, 4, 5), (1, 2, 1), (2, 3, 1), (3, 2, 1)]), 5)

    def gera(rng):
        n = rng.randint(2, 10)
        e = [(u + 1, v + 1, w) for u, v, w in grafo_aleatorio(rng, n, rng.randint(0, 3 * n), True, -10, 6)]
        e.append((1, n, rng.randint(-5, 5)))
        return (n, e)
    c.aleatorio("aleatórios vs gabarito", 200, gera, compara_gabarito("q37_maior_pontuacao"))


def valida_ciclo_neg(n, edges, existe):
    w = min_peso(edges)

    def v(out):
        if not existe:
            return out is None, f"não há ciclo negativo: esperado None, obtido {curto(out)}"
        if out is None:
            return False, "retornou None, mas existe ciclo negativo"
        out = list(out)
        if len(out) < 2 or out[0] != out[-1]:
            return False, "o ciclo deve começar e terminar no mesmo vértice"
        tot = 0
        for a, b in zip(out, out[1:]):
            if (a, b) not in w:
                return False, f"aresta {a}->{b} não existe"
            tot += w[(a, b)]
        return tot < 0, f"custo do ciclo = {tot}, não é negativo"
    return v


@teste(38, "Encontrar um ciclo negativo", "Externa — CSES 1197", 2)
def t38(c):
    e = [(1, 2, 1), (2, 4, 1), (3, 1, 1), (4, 1, -3), (4, 3, -2)]
    c.valida("exemplo", (4, e), valida_ciclo_neg(4, e, True))
    c.valida("sem ciclo negativo", (3, [(1, 2, -5), (2, 3, -5)]), valida_ciclo_neg(3, [(1, 2, -5), (2, 3, -5)], False))
    c.valida("caso extra", (4, [(1, 2, 3), (3, 4, -1), (4, 3, -1)]),
             valida_ciclo_neg(4, [(1, 2, 3), (3, 4, -1), (4, 3, -1)], True))

    def gera(rng):
        n = rng.randint(1, 10)
        return (n, [(u + 1, v + 1, w) for u, v, w in grafo_aleatorio(rng, n, rng.randint(0, 3 * n), True, -6, 12)])

    def comp(args, out):
        return valida_ciclo_neg(*args, G.q38_ciclo_negativo(*args) is not None)(out)
    c.aleatorio("aleatórios", 250, gera, comp)


def valida_rota_longa(n, flights, esp):
    E = set(map(tuple, flights))

    def v(out):
        if esp is None:
            return out is None, f"impossível: esperado None, obtido {curto(out)}"
        if out is None:
            return False, "retornou None, mas existe rota"
        out = list(out)
        if out[0] != 1 or out[-1] != n:
            return False, f"a rota deve ir de 1 a {n}"
        if any((a, b) not in E for a, b in zip(out, out[1:])):
            return False, "rota usa voo inexistente"
        return len(out) == len(esp), f"rota com {len(out)} cidades, o máximo é {len(esp)}"
    return v


@teste(39, "Rota com mais cidades", "Externa — CSES 1680", 2)
def t39(c):
    f = [(1, 2), (2, 5), (1, 3), (3, 4), (4, 5)]
    c.valida("exemplo", (5, f), valida_rota_longa(5, f, [1, 3, 4, 5]))
    c.valida("impossível", (3, [(2, 3)]), valida_rota_longa(3, [(2, 3)], None))

    def gera(rng):
        n = rng.randint(2, 12)
        perm = list(range(2, n))
        rng.shuffle(perm)
        perm = [1] + perm + [n]
        return (n, [(perm[a], perm[b]) for a, b, _ in dag_aleatorio(rng, n, rng.randint(0, 3 * n))
                    if perm.index(perm[a]) < perm.index(perm[b])])

    def comp(args, out):
        return valida_rota_longa(*args, G.q39_rota_mais_longa_dag(*args))(out)
    c.aleatorio("aleatórios", 200, gera, comp)


@teste(40, "Baile da escola", "Externa — CSES 1696", 2)
def t40(c):
    c.eq("pequeno", (3, 2, [(1, 1), (1, 2), (2, 1), (3, 1)]), 2)
    c.eq("caso extra", (2, 2, [(1, 1), (1, 2), (2, 1)]), 2)

    def gera(rng):
        a, b = rng.randint(1, 7), rng.randint(1, 7)
        return (a, b, list({(rng.randint(1, a), rng.randint(1, b)) for _ in range(rng.randint(0, a * b))}))

    def comp(args, out):
        a, b, P = args
        arcos = [(0, x, 1) for x in range(1, a + 1)] + [(x, a + y, 1) for x, y in P] + \
                [(a + y, a + b + 1, 1) for y in range(1, b + 1)]
        esp = G.q12_fluxo_maximo(a + b + 2, arcos, 0, a + b + 1)
        return out == esp, f"esperado {esp}, obtido {out}"
    c.aleatorio("aleatórios vs referência", 200, gera, comp)


def valida_policia(n, ruas, otimo):
    def v(out):
        out = [tuple(e) for e in out]
        pool = Counter(tuple(sorted(r)) for r in ruas)
        usado = Counter(tuple(sorted(r)) for r in out)
        if any(usado[k] > pool[k] for k in usado):
            return False, "bloqueou rua que não existe"
        if len(out) != otimo:
            return False, f"bloqueou {len(out)} ruas, o mínimo é {otimo}"
        resto = pool - usado
        arcos = []
        for (a, b), k in resto.items():
            arcos += [(a - 1, b - 1), (b - 1, a - 1)] * k
        return not alcanca(n, arcos, 0, n - 1), "ainda existe caminho de 1 até n"
    return v


@teste(41, "Perseguição policial", "Externa — CSES 1695", 2)
def t41(c):
    r = [(1, 2), (1, 3), (2, 3), (3, 4), (1, 4)]
    c.valida("exemplo", (4, r), valida_policia(4, r, 2))

    def gera(rng):
        n = rng.randint(2, 10)
        return (n, [(u + 1, v + 1) for u, v, _ in grafo_aleatorio(rng, n, rng.randint(0, 3 * n), False)])

    def comp(args, out):
        return valida_policia(*args, len(G.q41_perseguicao_policial(*args)))(out)
    c.aleatorio("aleatórios", 200, gera, comp)


@teste(42, "Lucro máximo com tarefas", "Externa — LeetCode 1235", 2)
def t42(c):
    c.eq("exemplo 1", ([1, 2, 3, 3], [3, 4, 5, 6], [50, 10, 40, 70]), 120)
    c.eq("exemplo 2", ([1, 2, 3, 4, 6], [3, 5, 10, 6, 9], [20, 20, 100, 70, 60]), 150)
    c.eq("exemplo 3", ([1, 1, 1], [2, 3, 4], [5, 6, 4]), 6)

    def gera(rng):
        n = rng.randint(1, 12)
        s = [rng.randint(0, 20) for _ in range(n)]
        return (s, [x + rng.randint(1, 8) for x in s], [rng.randint(1, 50) for _ in range(n)])

    def comp(args, out):
        s, e, p = args
        n = len(s)
        best = 0
        for mask in range(1 << n):      # força bruta
            idx = [i for i in range(n) if mask >> i & 1]
            idx.sort(key=lambda i: s[i])
            if all(e[a] <= s[b] for a, b in zip(idx, idx[1:])):
                best = max(best, sum(p[i] for i in idx))
        return out == best, f"esperado {best}, obtido {out}"
    c.aleatorio("aleatórios vs força bruta", 100, gera, comp)


@desempenho(42, "50.000 tarefas", 6)
def d42(seed):
    rng = random.Random(seed)
    s = [rng.randint(0, 10 ** 9) for _ in range(50000)]
    e = [x + rng.randint(1, 10 ** 6) for x in s]
    p = [rng.randint(1, 10 ** 4) for _ in s]
    esp = G.q42_lucro_tarefas(s, e, p)
    return (s, e, p), lambda out: (out == esp, f"esperado {esp}, obtido {out}")


# ===========================================================================
# ★ BAIXA / COMPLEMENTAR
# ===========================================================================
@teste(43, "Sisi e a sorveteria, parte 2", "Lista 3 — Q1", 1)
def t43(c):
    c.eq("exemplo 1", ([1, 2, 1, 3, 6],), 10)
    c.eq("exemplo 2", ([3, 2, 5, 4, 10],), 20)
    c.eq("exemplo 3", ([2, 2, 2, 2],), 3)

    def gera(rng):
        return ([rng.randint(1, 6) for _ in range(rng.randint(1, 6))],)

    def comp(args, out):
        A = args[0]
        best = 0

        def rec(i, ant, soma):
            nonlocal best
            if i == len(A):
                best = max(best, soma)
                return
            for q in range(0, A[i] + 1):
                if ant == 0 or q > ant:
                    if ant > 0 and q == 0:
                        continue
                    rec(i + 1, q, soma + q)
        rec(0, 0, 0)
        return out == best, f"esperado {best}, obtido {out}"
    c.aleatorio("aleatórios vs força bruta", 200, gera, comp)


@teste(44, "Minimizando custos de reparo", "Lista 3 — Q2", 1)
def t44(c):
    c.eq("exemplo 1", (2, 2, 1, 2, [1, 3]), 6)
    c.eq("exemplo 2", (3, 2, 1, 2, [1, 7]), 8)

    def gera(rng):
        n = rng.randint(1, 6)
        k = rng.randint(1, 8)
        return (n, k, rng.randint(1, 10), rng.randint(1, 10), [rng.randint(1, 2 ** n) for _ in range(k)])

    def comp(args, out):
        n, k, C1, C2, A = args

        def r(l, h):
            nb = sum(1 for a in A if l <= a <= h)
            c0 = C1 if nb == 0 else C2 * nb * (h - l + 1)
            if l == h:
                return c0
            m = (l + h) // 2
            return min(c0, r(l, m) + r(m + 1, h))
        esp = r(1, 2 ** n)
        return out == esp, f"esperado {esp}, obtido {out}"
    c.aleatorio("aleatórios vs força bruta", 200, gera, comp)


@desempenho(44, "n = 30, 100.000 buracos", 10)
def d44(seed):
    rng = random.Random(seed)
    A = [rng.randint(1, 2 ** 30) for _ in range(100000)]
    esp = G.q44_custo_reparo(30, 100000, 7, 3, A)
    return (30, 100000, 7, 3, A), lambda out: (out == esp, f"esperado {esp}, obtido {out}")


@teste(45, "Subsequências radicais", "Lista 3 — Q3", 1)
def t45(c):
    c.eq("exemplo [1,2,2]", ([1, 2, 2],), 6)
    c.eq("exemplo [1]", ([1],), 1)
    c.eq("exemplo [1,2]", ([1, 2],), 3)
    c.eq("exemplo [2,2,1,5,3] (o PDF diz 8; força bruta dá 7)", ([2, 2, 1, 5, 3],), 7)

    def gera(rng):
        n = rng.randint(1, 12)
        return ([rng.randint(1, n) for _ in range(n)],)

    def comp(args, out):
        A = args[0]
        esp = 0
        for r in range(1, len(A) + 1):
            for cmb in combinations(range(len(A)), r):
                if all(A[ix] % (i + 1) == 0 for i, ix in enumerate(cmb)):
                    esp += 1
        esp %= 999999937
        return out == esp, f"esperado {esp}, obtido {out}"
    c.aleatorio("aleatórios vs força bruta", 150, gera, comp)


@desempenho(45, "n = 100.000", 12)
def d45(seed):
    rng = random.Random(seed)
    A = [rng.randint(1, 100000) for _ in range(100000)]
    esp = G.q45_subsequencias_radicais(A)
    return (A,), lambda out: (out == esp, f"esperado {esp}, obtido {out}")


@teste(46, "Verificar caminho e caminho simples", "Slides 08 — Exercício 4", 1)
def t46(c):
    adj = [[1, 2], [3], [4], [4], [1, 5], []]
    c.eq("caminho simples", (adj, [0, 1, 3, 4, 5]), (True, True), normaliza=tuple)
    c.eq("caminho com repetição", (adj, [0, 1, 3, 4, 1, 3]), (True, False), normaliza=tuple)
    c.eq("aresta inexistente", (adj, [0, 3]), (False, False), normaliza=tuple)
    c.eq("aresta no sentido errado (dirigido)", (adj, [1, 0]), (False, False), normaliza=tuple)
    c.eq("um vértice só", (adj, [2]), (False, False), normaliza=tuple)


@teste(47, "Biblioteca de Alexandria (período de pico)", "Lista 2 — Q1", 1)
def t47(c):
    norm = lambda r: (r[0], tuple(r[1]))
    c.eq("exemplo 1", ([(5, 8), (2, 4), (3, 9)],), (2, (5, 8)), normaliza=norm)
    c.eq("exemplo 2", ([(5, 8), (2, 6), (3, 9)],), (3, (5, 6)), normaliza=norm)
    c.eq("uma pessoa", ([(1, 10)],), (1, (1, 10)), normaliza=norm)

    def gera(rng):
        n = rng.randint(1, 8)
        ts = rng.sample(range(1, 40), 2 * n)
        return ([tuple(sorted(ts[2 * i:2 * i + 2])) for i in range(n)],)
    c.aleatorio("aleatórios vs gabarito", 200, gera, compara_gabarito("q47_biblioteca_pico", norm))


@teste(48, "Sisi e a sorveteria", "Lista 2 — Q2", 1)
def t48(c):
    c.eq("exemplo 1", ([1, 2, 1, 4],), 3)
    c.eq("exemplo 2", ([11, 22, 11, 33, 22, 77, 44, 22],), 5)
    c.eq("exemplo 3", ([3, 3, 3, 3, 3, 3],), 1)

    def gera(rng):
        return ([rng.randint(1, 6) for _ in range(rng.randint(1, 15))],)

    def comp(args, out):
        A = args[0]
        esp = max(j - i for i in range(len(A)) for j in range(i + 1, len(A) + 1) if len(set(A[i:j])) == j - i)
        return out == esp, f"esperado {esp}, obtido {out}"
    c.aleatorio("aleatórios vs força bruta", 200, gera, comp)


def valida_hotel(guests, kmin):
    def v(out):
        k, quartos = out
        quartos = list(quartos)
        if k != kmin:
            return False, f"k = {k}, o mínimo é {kmin}"
        if len(quartos) != len(guests) or any(not 1 <= r <= k for r in quartos):
            return False, "quartos fora de 1..k ou tamanho errado"
        por_q = {}
        for (a, b), r in zip(guests, quartos):
            por_q.setdefault(r, []).append((a, b))
        for r, L in por_q.items():
            L.sort()
            for (a1, b1), (a2, b2) in zip(L, L[1:]):
                if not b1 < a2:
                    return False, f"quarto {r}: estadias {(a1, b1)} e {(a2, b2)} conflitam"
        return True, ""
    return v


@teste(49, "Hotel de Hilbert", "Lista 2 — Q3", 1)
def t49(c):
    for g, k in [([(1, 2), (3, 3), (4, 5)], 1), ([(2, 4), (1, 2), (4, 4)], 2), ([(1, 2), (2, 4), (4, 4)], 2),
                 ([(1, 4), (1, 2), (2, 4)], 3)]:
        c.valida(f"exemplo {g}", (g,), valida_hotel(g, k))

    def gera(rng):
        gs = []
        for _ in range(rng.randint(1, 10)):
            a = rng.randint(1, 20)
            gs.append((a, a + rng.randint(0, 5)))
        return (gs,)

    def comp(args, out):
        gs = args[0]
        kmin = max(sum(1 for a, b in gs if a <= t <= b) for t in range(0, 30))
        return valida_hotel(gs, kmin)(out)
    c.aleatorio("aleatórios", 200, gera, comp)


@desempenho(49, "200.000 hóspedes", 6)
def d49(seed):
    rng = random.Random(seed)
    gs = []
    for _ in range(200000):
        a = rng.randint(1, 10 ** 9)
        gs.append((a, a + rng.randint(0, 10 ** 5)))
    return (gs,), valida_hotel(gs, G.q49_hotel_hilbert(gs)[0])


def valida_quadra(A, k, existe):
    def v(out):
        out = tuple(out)
        if not existe:
            return out == (-1, -1, -1, -1), f"não existe: esperado (-1,-1,-1,-1), obtido {out}"
        if out == (-1, -1, -1, -1):
            return False, "retornou (-1,...) mas existe solução"
        a, b, cc, d = out
        if not 1 <= a < b < cc < d <= len(A):
            return False, f"índices inválidos (precisam ser 1-indexados e crescentes): {out}"
        return A[a - 1] + A[b - 1] + A[cc - 1] + A[d - 1] == k, "a soma não dá k"
    return v


@teste(50, "Quadra", "Lista 2 — Q4", 1)
def t50(c):
    c.valida("exemplo 1", ([3, 2, 6, 1], 7), valida_quadra([3, 2, 6, 1], 7, False))
    c.valida("exemplo 2", ([3, 2, 6, 1], 12), valida_quadra([3, 2, 6, 1], 12, True))
    c.valida("exemplo 3", ([3, 2, 5, 8, 1, 3, 2, 3], 15), valida_quadra([3, 2, 5, 8, 1, 3, 2, 3], 15, True))

    def gera(rng):
        n = rng.randint(1, 10)
        return ([rng.randint(1, 10) for _ in range(n)], rng.randint(4, 30))

    def comp(args, out):
        A, k = args
        ex = any(sum(A[i] for i in q) == k for q in combinations(range(len(A)), 4))
        return valida_quadra(A, k, ex)(out)
    c.aleatorio("aleatórios vs força bruta", 200, gera, comp)


@desempenho(50, "n = 1.000 sem solução", 10)
def d50(seed):
    A = [2 * i + 1 for i in range(1000)]          # soma de 4 ímpares é par
    return (A, 10 ** 6 + 1), valida_quadra(A, 10 ** 6 + 1, False)


@teste(51, "Os blocos (torres)", "Lista 2 — Q5", 1)
def t51(c):
    c.eq("exemplo 1", ([1, 2, 1, 4],), 3)
    c.eq("exemplo 2", ([11, 22, 11, 33, 22, 77, 44, 22],), 4)
    c.eq("exemplo 3", ([3, 3, 3, 3, 3, 3],), 1)

    def gera(rng):
        return ([rng.randint(1, 6) for _ in range(rng.randint(1, 15))],)
    c.aleatorio("aleatórios vs gabarito", 200, gera, compara_gabarito("q51_torres_blocos"))


@desempenho(51, "200.000 blocos", 6)
def d51(seed):
    rng = random.Random(seed)
    A = [rng.randint(1, 10 ** 9) for _ in range(200000)]
    esp = G.q51_torres_blocos(A)
    return (A,), lambda out: (out == esp, f"esperado {esp}, obtido {out}")


@teste(52, "O grande sistema planetário", "Lista 2 — Q6", 1)
def t52(c):
    c.eq("exemplo 1", ([3, 2, 6], 7), 8)
    c.eq("exemplo 2", ([3, 2, 6, 5, 8, 2, 1], 1234), 438)
    c.eq("valores enormes", ([10 ** 9], 10 ** 9), 10 ** 18)

    def gera(rng):
        return ([rng.randint(1, 10) for _ in range(rng.randint(1, 5))], rng.randint(1, 50))

    def comp(args, out):
        A, k = args
        T = 0
        while sum(T // a for a in A) < k:
            T += 1
        return out == T, f"esperado {T}, obtido {out}"
    c.aleatorio("aleatórios vs força bruta", 200, gera, comp)


@teste(53, "Otimização (minimizar soma de |A_i - k|)", "Lista 2 — Q7", 1)
def t53(c):
    c.eq("exemplo 1", ([3, 2, 6, 1],), 2)
    c.eq("exemplo 2", ([3, 2, 5, 8, 1, 3, 2, 3],), 3)
    c.eq("exemplo 3", ([33, 10],), 10)

    def gera(rng):
        return ([rng.randint(-20, 20) for _ in range(rng.randint(1, 12))],)

    def comp(args, out):
        A = args[0]
        esp = min(range(-21, 22), key=lambda k: (sum(abs(a - k) for a in A), k))
        return out == esp, f"esperado {esp}, obtido {out}"
    c.aleatorio("aleatórios vs força bruta", 200, gera, comp)


# ---------------------------------------------------------------------------
# Execução
# ---------------------------------------------------------------------------
def _filho(modname, num, idx, fila):
    try:
        sys.setrecursionlimit(10000)
        mod = importlib.import_module(modname)
        f = getattr(mod, nome_funcao(mod, num))
        desc, lim, gen = DESEMPENHO[num][idx]
        args, check = gen(2024 + idx)
        t0 = time.perf_counter()
        out = f(*args)
        dt = time.perf_counter() - t0
        ok, msg = check(out)
        fila.put((ok, msg, dt))
    except NotImplementedError:
        fila.put((None, "não implementada", 0))
    except RecursionError:
        fila.put((False, "RecursionError: recursão profunda demais", 0))
    except Exception as e:
        fila.put((False, f"{type(e).__name__}: {e}", 0))


def roda_desempenho(modname, num):
    res = []
    for idx, (desc, lim, _) in enumerate(DESEMPENHO.get(num, [])):
        fila = mp.Queue()
        p = mp.Process(target=_filho, args=(modname, num, idx, fila))
        p.start()
        p.join(lim + 15)          # tempo extra para gerar os dados
        if p.is_alive():
            p.terminate()
            p.join()
            res.append((False, f"[desempenho] {desc}", f"⏱  LENTO: passou de {lim}s "))
            continue
        try:
            ok, msg, dt = fila.get(timeout=2)
        except Exception:
            res.append((False, f"[desempenho] {desc}", "o processo terminou sem resposta (estouro de pilha/memória?)"))
            continue
        if ok is None:
            continue
        if ok and dt > lim:
            res.append((False, f"[desempenho] {desc}", f"⏱  LENTO: {dt:.2f}s (limite {lim}s)"))
        else:
            res.append((ok, f"[desempenho] {desc} — {dt:.2f}s (limite {lim}s)", "" if ok else msg))
    return res


def nome_funcao(mod, num):
    pref = f"q{num:02d}_"
    for nome in dir(mod):
        if nome.startswith(pref) and callable(getattr(mod, nome)):
            return nome
    raise AttributeError(f"função {pref}... não encontrada em {mod.__name__}")


ESTRELAS = {3: "★★★", 2: "★★ ", 1: "★  "}


def _desempenho_local(num, f):
    """Testes de tempo no próprio processo (usado pelo notebook).
    Em macOS/Linux o tempo é cortado com SIGALRM; no Windows só mede."""
    import signal
    res = []
    tem_alarme = hasattr(signal, "setitimer") and \
        __import__("threading").current_thread() is __import__("threading").main_thread()

    class _Estourou(Exception):
        pass

    def _alarme(*_):
        raise _Estourou()

    for idx, (desc, lim, gen) in enumerate(DESEMPENHO.get(num, [])):
        args, check = gen(2024 + idx)
        antigo = None
        try:
            if tem_alarme:
                antigo = signal.signal(signal.SIGALRM, _alarme)
                signal.setitimer(signal.ITIMER_REAL, lim)
            t0 = time.perf_counter()
            out = f(*args)
            dt = time.perf_counter() - t0
        except _Estourou:
            res.append((False, f"[desempenho] {desc}", f"⏱  LENTO: passou de {lim}s"))
            continue
        except NotImplementedError:
            return []
        except RecursionError:
            res.append((False, f"[desempenho] {desc}", "RecursionError: recursão profunda demais"))
            continue
        except Exception as e:
            res.append((False, f"[desempenho] {desc}", f"{type(e).__name__}: {e}"))
            continue
        finally:
            if tem_alarme:
                signal.setitimer(signal.ITIMER_REAL, 0)
                if antigo is not None:
                    signal.signal(signal.SIGALRM, antigo)
        ok, msg = check(out)
        if ok and dt > lim:
            res.append((False, f"[desempenho] {desc}", f"⏱  LENTO: {dt:.2f}s (limite {lim}s)"))
        else:
            res.append((ok, f"[desempenho] {desc} — {dt:.2f}s (limite {lim}s)", "" if ok else msg))
    return res


def _avalia(num, f, desempenho_fn, verbose):
    """Roda os testes da questão `num` na função `f`, imprime e devolve 'ok'/'falha'/'pend'."""
    fn, titulo, fonte, prio = TESTES[num]
    c = Ctx(f)
    try:
        fn(c)
    except NaoImplementada:
        print(f"Q{num:02d} {ESTRELAS[prio]} {titulo}  [{fonte}]\n     ⏭  ainda não implementada")
        return "pend"
    if desempenho_fn and num in DESEMPENHO and all(ok for ok, _, _ in c.res):
        c.res += desempenho_fn(num, f)
    ok_n = sum(1 for ok, _, _ in c.res if ok)
    tudo = ok_n == len(c.res)
    print(f"Q{num:02d} {ESTRELAS[prio]} {titulo}  [{fonte}]\n     "
          f"{'✅' if tudo else '❌'} {ok_n}/{len(c.res)} casos")
    for ok, desc, msg in c.res:
        if not ok:
            print(f"       ✗ {desc}: {msg}")
        elif verbose:
            print(f"       ✓ {desc}")
    return "ok" if tudo else "falha"


def testar(num, f, desempenho=True, verbose=False):
    """Uso no notebook:  testar(4, q04_rota_sensores)"""
    sys.setrecursionlimit(max(sys.getrecursionlimit(), 3000))
    return _avalia(num, f, _desempenho_local if desempenho else None, verbose) == "ok"


def testar_todas(ns, desempenho=False, prioridade=None):
    """Uso no notebook:  testar_todas(globals())  — resumo de todas as questões."""
    resumo = {"ok": [], "falha": [], "pend": []}
    nums = [n for n in sorted(TESTES) if prioridade is None or TESTES[n][3] == prioridade]
    for num in nums:
        pref = f"q{num:02d}_"
        f = next((v for k, v in ns.items() if k.startswith(pref) and callable(v)), None)
        if f is None:
            print(f"Q{num:02d}: função {pref}... não encontrada (rode a célula dela antes)")
            resumo["falha"].append(num)
            continue
        resumo[_avalia(num, f, _desempenho_local if desempenho else None, False)].append(num)
    _imprime_resumo(resumo, nums)


def _imprime_resumo(resumo, nums):
    print("=" * 78)
    print(f"✅ {len(resumo['ok'])} completas   ❌ {len(resumo['falha'])} com falha   "
          f"⏭  {len(resumo['pend'])} pendentes")
    if resumo["falha"]:
        print("   Com falha:", " ".join(f"Q{n:02d}" for n in resumo["falha"]))
    for p in (3, 2, 1):
        tot = [n for n in nums if TESTES[n][3] == p]
        if tot:
            feitas = sum(1 for n in tot if n in resumo["ok"])
            print(f"   {ESTRELAS[p]} {feitas}/{len(tot)} completas")


def main():
    ap = argparse.ArgumentParser(description="Corretor das questões práticas de PAA")
    ap.add_argument("questoes", nargs="*", type=int, help="números das questões (padrão: todas)")
    ap.add_argument("--prioridade", type=int, choices=[1, 2, 3], help="só questões com essa prioridade")
    ap.add_argument("--gabarito", action="store_true", help="testa gabarito.py em vez de praticas.py")
    ap.add_argument("--modulo", default=None, help="nome de outro módulo para testar")
    ap.add_argument("--sem-desempenho", action="store_true", help="pula os testes de tempo")
    ap.add_argument("-v", "--verbose", action="store_true", help="mostra também os casos que passaram")
    a = ap.parse_args()

    modname = a.modulo or ("gabarito" if a.gabarito else "praticas")
    mod = importlib.import_module(modname)
    nums = a.questoes or sorted(TESTES)
    if a.prioridade:
        nums = [n for n in nums if TESTES[n][3] == a.prioridade]

    resumo = {"ok": [], "falha": [], "pend": []}
    print(f"\nTestando {modname}.py — {len(nums)} questão(ões)\n" + "=" * 78)
    for num in nums:
        try:
            f = getattr(mod, nome_funcao(mod, num))
        except AttributeError as e:
            print(f"Q{num:02d} {ESTRELAS[TESTES[num][3]]} {TESTES[num][1]}\n     ❌ {e}")
            resumo["falha"].append(num)
            continue
        perf = None if a.sem_desempenho else (lambda n, _f: roda_desempenho(modname, n))
        resumo[_avalia(num, f, perf, a.verbose)].append(num)
    _imprime_resumo(resumo, nums)


if __name__ == "__main__":
    mp.freeze_support()
    main()
