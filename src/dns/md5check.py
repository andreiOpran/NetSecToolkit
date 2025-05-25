import hashlib
import sys

def calculate_md5(filename):
    md5_hash = hashlib.md5()
    with open(filename, 'rb') as file:
        for chunk in iter(lambda: file.read(4096), b""):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()

def compare_files(file1, file2):
    '''Compare two files by their MD5 hashes'''
    try: 
        hash1 = calculate_md5(file1)
        hash2 = calculate_md5(file2)
        if hash1 == hash2:
            print("Files are identical.")
            return True
        else:
            print("Files are different.")
            return False
    except FileNotFoundError as e:
        print(f"File \"{e.filename}\" not found.")
        return False
    
if __name__ == "__main__":
    if len(sys.argv) == 2:
        filename = sys.argv[1]
        compare_files(f'tunnel_files/{filename}.txt', f'received_files/{filename}_received.txt')
    else:
        print("Usage: python md5check.py <filename>")
        print("Example: python md5check.py example")
        print("This will compare 'tunnel_files/example.txt' with 'received_files/example_received.txt'")