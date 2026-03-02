import os
import time
from flask import Flask,jsonify
import psycopg2
import redis
app=Flask(__name__)

DATABASE_URL=os.getenv("DATABASE_URL")
REDIS_HOST=os.getenv("REDIS_HOST","redis")


def wait_for_db(max_retries=20):
    for _ in range(max_retries):
        try:
            conn=psycopg2.connect(DATABASE_URL)
            conn.close()
            return
        except Exception:
            time.sleep(1)

    raise RuntimeError("DB no responde")


@app.get("/")
def home():
    return jsonify ({
        "message":"Hola desde docker compose!",
        "service": {
            "/health": "Verifica la salud de la aplicación",
            "visits": "Muestra el número de visitas de redis"
        }
        
        })


@app.get("/health")
def health():
    try:
        
        conn=psycopg2.connect(DATABASE_URL)
        cur=conn.cursor()
        cur.execute("SELECT NOW();")
        now=cur.fetchone()[0]
        cur.close()

        r=redis.Redis(host=REDIS_HOST,port=6379,decode_responses=True)
        pong=r.ping()


        return jsonify({
            "status":"ok",
            "db_time":str(now),
            "redis_ping":pong

        })
    
    except Exception as e:
        return jsonify({
            "status":"error",
            "message":str(e)
        }),500
    

@app.get("/visits")
def visits():
    try:
        r=redis.Redis(host=REDIS_HOST,port=6379,decode_responses=True)
        count=r.incr("visits")
        return jsonify({
            "visits":int (count),

        })
    
    except Exception as e:
        return jsonify({
            "status":"error",
            "message":str(e)
        }),500
    

if __name__=="__main__":
    wait_for_db()
    app.run(host="0.0.0.0",port=8000)
   