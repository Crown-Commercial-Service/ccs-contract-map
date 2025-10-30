from passlib.context import CryptContext
import getpass

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password):
    return pwd_context.hash(password)

if __name__ == "__main__":
    password = getpass.getpass("Enter password to hash: ")
    hashed_password = hash_password(password)
    print("\nYour hashed password is:")
    print(hashed_password)
    print("\nSet this value as the HASHED_PASSWORD environment variable.")
