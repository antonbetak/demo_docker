import os
import time
from flask import Flask, jsonify, request
import psycopg2
import redis

app = Flask(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")


def wait_for_db(max_retries=20):
    for _ in range(max_retries):
        try:
            conn = psycopg2.connect(DATABASE_URL)
            conn.close()
            return
        except Exception:
            time.sleep(1)

    raise RuntimeError("DB no responde")


def init_db():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """
    )
    conn.commit()
    cur.close()
    conn.close()


@app.get("/")
def home():
    return jsonify(
        {
            "message": "Hola desde docker compose!",
            "service": {
                "/health": "Verifica salud de app/db/redis",
                "/visits": "Contador con redis",
                "/users POST": "Crear usuario en postgres",
                "/users GET": "Listar usuarios de postgres",
            },
        }
    )


@app.get("/health")
def health():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT NOW();")
        now = cur.fetchone()[0]
        cur.close()
        conn.close()

        r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)
        pong = r.ping()

        return jsonify({"status": "ok", "db_time": str(now), "redis_ping": pong})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.get("/visits")
def visits():
    try:
        r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)
        count = r.incr("visits")
        return jsonify({"visits": int(count)})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.post("/users")
def create_user():
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    email = data.get("email")

    if not name:
        return jsonify({"error": "name es obligatorio"}), 400

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (name, email) VALUES (%s, %s) RETURNING id, name, email, created_at;",
            (name, email),
        )
        row = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()

        return jsonify(
            {
                "id": row[0],
                "name": row[1],
                "email": row[2],
                "created_at": str(row[3]),
            }
        ), 201

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.get("/users")
def list_users():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT id, name, email, created_at FROM users ORDER BY id;")
        rows = cur.fetchall()
        cur.close()
        conn.close()

        users = []
        for row in rows:
            users.append(
                {
                    "id": row[0],
                    "name": row[1],
                    "email": row[2],
                    "created_at": str(row[3]),
                }
            )

        return jsonify({"count": len(users), "users": users})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    wait_for_db()
    init_db()
    app.run(host="0.0.0.0", port=8000)
