from _sha2 import sha256

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

class Hasher:
    @staticmethod
    def hash_password(password):
        return pwd_context.hash(password)
    @staticmethod
    def verify_password(plain_password, hashed_password):
        return pwd_context.verify(plain_password, hashed_password)