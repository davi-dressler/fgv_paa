def questao_2(v: list, k: int, x: int):
    n = len(v)
    alvo = v[x]
    k_prox = []
    menor_left = x-1
    menor_right = x+1

    while len(k_prox) < k:

        if menor_left < 0 and menor_right > n-1:
            break

        if menor_left >= 0:
            abs_left = abs(v[menor_left] - alvo)

            if menor_right <= n-1:
                abs_right = abs(v[menor_right] - alvo)
        
                if abs_left <= abs_right:
                    k_prox.append(v[menor_left])
                    menor_left -= 1
                else:
                    k_prox.append(v[menor_right])
                    menor_right += 1

            else:
                k_prox.append(v[menor_left])
                menor_left -= 1

        else:
            if menor_right <= n-1:
                k_prox.append(v[menor_right])
                menor_right += 1

    return k_prox


lista = [1,2,3,4,5,6,7,8,9]
print(questao_2(lista, 2, 2))
            

    