from flask import Flask, request, jsonify
from flask_cors import CORS  
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)
CORS(app)  

MONGO_URI = "mongodb+srv://MIAWW:roby2727@miaww.g4xdg.mongodb.net/?retryWrites=true&w=majority&appName=MIAWW"

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client["iot_data"]
    collection = db["sensor_data"]
    
    client.server_info()
    print("✅ Koneksi MongoDB Berhasil!")
except Exception as e:
    print("❌ Gagal koneksi MongoDB:", e)
    collection = None

@app.route('/')
def home():
    return jsonify({"message": "API IoT Sensor Data"}), 200

@app.route('/add_sensor_data', methods=['POST'])
def add_sensor_data():
    if collection is None:
        return jsonify({"error": "Database tidak terkoneksi"}), 500

    try:
        data = request.json
        data["timestamp"] = datetime.utcnow()  

        result = collection.insert_one(data)
        print(f"📥 Data diterima: {data}")

        return jsonify({"message": "Data berhasil disimpan", "id": str(result.inserted_id)}), 201
    except Exception as e:
        print("❌ Error saat menyimpan data:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/get_sensor_data', methods=['GET'])
def get_sensor_data():
    if collection is None:
        return jsonify({"error": "Database tidak terkoneksi"}), 500

    try:
        data = list(collection.find({}, {"_id": 0})) 
        return jsonify(data), 200
    except Exception as e:
        print("❌ Error saat mengambil data:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
