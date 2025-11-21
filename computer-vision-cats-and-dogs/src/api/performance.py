import sqlite3

conn = sqlite3.connect("src/api/database.db")
cur = conn.cursor()

# Nombre total de feedback
cur.execute("SELECT COUNT(*) FROM Feedback")
total_feedback = cur.fetchone()[0]

# Nombre de feedback positifs (status = 'oui')
cur.execute("SELECT COUNT(*) FROM Feedback WHERE status = 'OUI'")
total_positifs = cur.fetchone()[0]

# Nombre de feedback négatifs (status = 'non')
cur.execute("SELECT COUNT(*) FROM Feedback WHERE status = 'NON'")
total_negatifs = cur.fetchone()[0]

# Nombre de prédictions chien (détail oui/non)
cur.execute("SELECT COUNT(*) FROM Feedback WHERE predicted_class = 'Dog' AND status = 'OUI'")
chien_positifs = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM Feedback WHERE predicted_class = 'Dog' AND status = 'NON'")
chien_negatifs = cur.fetchone()[0]

# Nombre de prédictions chat (détail oui/non)
cur.execute("SELECT COUNT(*) FROM Feedback WHERE predicted_class = 'Cat' AND status = 'NON'")
chat_positifs = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM Feedback WHERE predicted_class = 'Cat' AND status = 'Oui'")
chat_negatifs = cur.fetchone()[0]

conn.close()

bad_feedback_pourcentage = (total_negatifs / total_feedback * 100) if total_feedback > 0 else 0

feedback_message = "Ce modèle est plutôt bon"
if bad_feedback_pourcentage >= 30:
    feedback_message = "Ce modèle est plutôt bon, mais laisse à désirer."
if bad_feedback_pourcentage >= 50:
    feedback_message = "Ce modèle n'est pas performant, un nouvel entraînement est nécessaire."

result_final =  {
    "total_feedback": total_feedback,
    "positifs": total_positifs,
    "negatifs": total_negatifs,
    "chien": {
        "positifs": chien_positifs,
        "negatifs": chien_negatifs
    },
    "chat": {
        "positifs": chat_positifs,
        "negatifs": chat_negatifs
    },
    "bad_feedback_pourcentage": bad_feedback_pourcentage,
    "message": feedback_message
}

print(result_final)