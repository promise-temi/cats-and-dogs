import sqlite3

def main():
    create_database()

def create_database():    
    # Connexion (ou création du fichier users.db)
    conn = sqlite3.connect("src/api/database.db")
    cur = conn.cursor()

    # Charger le script SQL
    with open("src/api/database.sql", "r", encoding="utf-8") as f:
        sql_script = f.read()

    cur.executescript(sql_script)

    conn.close()
    print('base de donnée crée...')

if __name__ == "__main__":
    main()