import hashlib

pwd = b"Harbor12345"
pwd_nl = b"Harbor12345\n"

print(f"MD5(pwd): {hashlib.md5(pwd).hexdigest()}")
print(f"MD5(pwd_nl): {hashlib.md5(pwd_nl).hexdigest()}")
print(f"SHA1(pwd): {hashlib.sha1(pwd).hexdigest()}")
print(f"SHA256(pwd): {hashlib.sha256(pwd).hexdigest()}")
