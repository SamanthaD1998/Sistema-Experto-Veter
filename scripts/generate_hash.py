# script para generar hash: generate_hash.py
from werkzeug.security import generate_password_hash

def main():
    password = "admin"  # utiliza una contraseña más segura en un entorno de producción
    hashed_password = generate_password_hash(password, method='sha256')
    print(f"El hash de tu contraseña es: {hashed_password}")

if __name__ == "__main__":
    main()
