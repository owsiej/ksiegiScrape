import re
import os
import jsonlines


def clear_list(lista):
    nowaLista = list(filter(lambda x: x, map(lambda x: re.sub(r'\s+', " ", x.replace("\n", "").strip()), lista)))
    return nowaLista


def find_file_in_parents(filename, start_directory='.'):
    current_dir = os.path.abspath(start_directory)

    while True:
        file_path = os.path.join(current_dir, filename)

        if os.path.isfile(file_path):
            return file_path  # Found the file

        # Move to the parent directory
        parent_dir = os.path.dirname(current_dir)

        # Check if we have reached the root directory
        if parent_dir == current_dir:
            return None  # File not found in any parent directory

        current_dir = parent_dir


def find_missing_books():
    file_path = find_file_in_parents('ksiegi.jsonl')
    if file_path:
        print(f"Found file at: {file_path}")
    else:
        print("File not found in any parent directory.")
    missingBooks = []
    allScrapedBooks = []

    with jsonlines.open(file_path, 'r') as reader:
        for obj in reader:
            allScrapedBooks.append(int(obj['numerKsiegi'].split('/')[1]))
    allScrapedBooks.sort()
    for i in range(len(allScrapedBooks) - 1):
        differenceOfAdjacentNumbs = abs(allScrapedBooks[i] - allScrapedBooks[i + 1])
        if differenceOfAdjacentNumbs != 1:
            for y in range(1, differenceOfAdjacentNumbs):
                missingBooks.append(allScrapedBooks[i] + y)
    return missingBooks
