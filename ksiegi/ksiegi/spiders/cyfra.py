kod = [1, 3, 7, 1, 3, 7, 1, 3, 7, 1, 3, 7]
mapper = {
    "0": 0, "1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "X": 10, "A": 11, "B": 12, "C": 13,
    "D": 14, "E": 15, "F": 16, "G": 17, "H": 18, "I": 19, "J": 20, "K": 21, "L": 22, "M": 23, "N": 24, "O": 25, "P": 26,
    "R": 27, "S": 28, "T": 29, "U": 30, "W": 31, "Y": 32, "Z": 33,
}


def znajdzCyfreKontrolna(ksiega):
    sum = 0
    for char, code in zip(ksiega, kod):
        sum += mapper[char] * code
    return str(sum % 10)
