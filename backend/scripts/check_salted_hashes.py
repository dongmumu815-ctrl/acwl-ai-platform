import hashlib

pwd = b"Harbor12345"
salt = b"XkXfpTGWeMaHa7ara0dZiw9ipTUrFn3K"

print(f"MD5(salt + pwd): {hashlib.md5(salt + pwd).hexdigest()}")
print(f"MD5(pwd + salt): {hashlib.md5(pwd + salt).hexdigest()}")
print(f"SHA256(salt + pwd): {hashlib.sha256(salt + pwd).hexdigest()}")
