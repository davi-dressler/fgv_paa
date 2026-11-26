
def binary_search(v: list, x: int, left= 0, right= None):
    if right == None:
         right = len(v) - 1

    if left > right:
         return - 1
    
    mid = (left + right)//2

    if v[mid] == x:
        return mid

    if v[left] <= v[mid]: #A metade esquerda está ordenada
        if v[left] <= x < v[mid]:
            return binary_search(v, x, left, mid-1)
        else:
            return binary_search(v, x, mid+1, right)

    else:
            #A metade esquerda está ordenada
        if v[mid] < x <= v[right]:
            return binary_search(v, x, mid+1, right)
        else:
            return binary_search(v, x, left, mid-1)



# print(binary_search([40, 50, 60, 10, 20, 30], 10))
# print(binary_search([4, 5, 6, 7, 0, 1, 2] , 0))
# print(binary_search([30, 40, 50, 10, 20], 35))

events = [5, 1, 2, 1, 3, 2, 1, 4, 2, 1] 

def process_music(v: list, k: int):
    freq = {}
    heap = []
    pos = {}

    def swap(i, j):
        temp = heap[i]
        heap[i] = heap[j]
        heap[j] = temp

        pos[heap[i]] = i
        pos[heap[j]] = j

    def heapify_up(i):
        while i > 0:
            p = (i-1)//2

            if freq[heap[p]] <= freq[heap[i]]:
                break
            
            swap(i,p)
            i = p

    def heapify_down(i, size):

        while True:
            left, right = 2*i + 1, 2*i + 2
            menor = i

            if left < size and freq[heap[i]] > freq[heap[left]]:
                menor = left

            if right < size and freq[heap[menor]] > freq[heap[right]]:
                menor = right

            if menor == i:
                break

            swap(i, menor)
            i = menor

    for id in v:
        freq[id] = freq.get(id, 0) + 1

        if id in pos:
            heapify_down(pos[id], len(heap) - 1)

        elif len(heap) < k:
            heap.append(id)
            pos[id] = len(heap) - 1
            heapify_up(pos[id])

        elif freq[id] > freq[heap[0]]:
            del pos[heap[0]]
            heap[0] = id
            pos[id] = 0
            heapify_down(0, len(heap) - 1)

    for fim in range(len(heap) - 1, 0, -1):
        swap(0, fim)
        heapify_down(0, fim)

    return [(id, freq[id]) for id in heap]

# print(process_music(events, 3))


