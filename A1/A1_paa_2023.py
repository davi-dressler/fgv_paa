def questao_2(A: list):
    left = 0
    right = len(A) - 1

    while left <= right:
        mid = (left+right)//2
        if A[mid] == mid:
            return mid
        if A[mid] > mid: 
            right = mid - 1
        else:
            left = mid + 1

    return -1

# Aqui, utilizamos a lógica do Binary Search para conseguir um desempenho 
# de O(log n), comparamos os valores procurados e retornamos o valor do índice
# para qual A[i] = i se houver. Caso contrário, retornamos -1