# app.py (en la raíz, al mismo nivel que la carpeta app/)
from app import create_app

app = create_app("development")

if __name__ == "__main__":
    app.run(debug=True)