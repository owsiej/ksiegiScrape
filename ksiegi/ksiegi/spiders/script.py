import re
import csv
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()


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


def find_missing_books_by_database():
    client = MongoClient(os.getenv("MONGO_URL"))
    db = client[os.getenv("MONGO_DATABASE_NAME")]
    collection = db[os.getenv("MONGO_DATABASE_COLLECTION_NAME")]

    missingBooks = []
    allScrapedBooks = []
    for ksiega in collection.find():
        allScrapedBooks.append(int(ksiega['numerKsiegi'].split('/')[1]))

    allScrapedBooks.sort()
    print(f"Last book in database: {allScrapedBooks[-1]}")
    for i in range(len(allScrapedBooks) - 1):
        differenceOfAdjacentNumbs = abs(allScrapedBooks[i] - allScrapedBooks[i + 1])
        if differenceOfAdjacentNumbs != 1:
            for y in range(1, differenceOfAdjacentNumbs):
                missingBooks.append(allScrapedBooks[i] + y)
    return missingBooks


def find_missing_books_by_error_file():
    file_path = find_file_in_parents(os.getenv("LOG_FILE"))
    if file_path:
        print(f"Found file at: {file_path}")
    else:
        print("File not found in any parent directory.")
    missingBooks = []

    with open(file_path, 'r', encoding="utf-8") as reader:
        csv_reader = csv.reader(reader, delimiter='\n')
        for obj in csv_reader:
            try:
                missingBooks.append(int(obj[0].split(" ")[-1].split("/")[1]))
            except Exception as e:
                print("Błąd przy odczycie pozycji z error file", e)
                continue
    missingBooks.sort()

    return missingBooks


def find_duplicates_and_remove_them_from_database():
    client = MongoClient(os.getenv("MONGO_URL"))
    db = client[os.getenv("MONGO_DATABASE_NAME")]
    collection = db[os.getenv("MONGO_DATABASE_COLLECTION_NAME")]

    unique = set()
    duplicates = []
    allScrapedBooks = []
    for ksiega in collection.find():
        allScrapedBooks.append(ksiega['numerKsiegi'])

    for ksiega in allScrapedBooks:
        if ksiega in unique:
            duplicates.append(ksiega)
        else:
            unique.add(ksiega)

    for dupli in duplicates:
        myDeleteQuery = {"numerKsiegi": f"{dupli}"}
        print(myDeleteQuery)
        collection.delete_one(myDeleteQuery)

    return duplicates


def are_duplicates_in_database():
    client = MongoClient(os.getenv("MONGO_URL"))
    db = client[os.getenv("MONGO_DATABASE_NAME")]
    collection = db[os.getenv("MONGO_DATABASE_COLLECTION_NAME")]

    allRecords = [int(ksiega['numerKsiegi'].split('/')[1]) for ksiega in collection.find()]
    return len(allRecords) != len(set(allRecords))
