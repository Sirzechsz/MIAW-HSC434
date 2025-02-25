import network
import time
import ujson
import urequests
from umqtt.simple import MQTTClient
from machine import Pin, ADC, reset
import dht

SSID = "RUANG 125-STI"  
PASSWORD = "12345678"  

TOKEN = "BBUS-d08rjiH786Cxj4wejfxaL4UodEnPkm"
MQTT_BROKER = "industrial.api.ubidots.com"
DEVICE_LABEL = "esp32"
MQTT_TOPIC = f"/v1.6/devices/{DEVICE_LABEL}"

API_URL = "http://172.16.200.181:5000/add_sensor_data" 

sensor = dht.DHT11(Pin(4)) 
ldr = ADC(Pin(34))  
ldr.atten(ADC.ATTN_11DB)  

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    
    print("🔄 Menghubungkan ke WiFi...")
    for _ in range(15):  
        if wlan.isconnected():
            print("✅ WiFi Terhubung:", wlan.ifconfig())
            return True
        time.sleep(1)
    
    print("❌ Gagal terhubung ke WiFi! Restart ESP32...")
    reset()

def connect_mqtt():
    try:
        client = MQTTClient("esp32", MQTT_BROKER, user=TOKEN, password="")
        client.connect()
        print("✅ Terhubung ke Ubidots MQTT!")
        return client
    except Exception as e:
        print("❌ Gagal koneksi ke MQTT:", e)
        return None

def send_data_to_api(temp, hum, light):
    try:
        data = ujson.dumps({"temperature": temp, "humidity": hum, "light_intensity": light})
        headers = {"Content-Type": "application/json"}
        
        print("📡 Mengirim data ke API Flask...", API_URL)
        response = urequests.post(API_URL, data=data, headers=headers, timeout=5)
        
        print("✅ Response API:", response.text)
        response.close()
        return True
    except Exception as e:
        print("❌ Gagal mengirim data ke API:", e)
        return False

def send_data(client):
    reconnect_attempts = 0

    while True:
        try:
            wlan = network.WLAN(network.STA_IF)
            if not wlan.isconnected():
                print("⚠ WiFi terputus, mencoba reconnect...")
                if connect_wifi():
                    client = connect_mqtt()

            sensor.measure()
            suhu = sensor.temperature()
            kelembaban = sensor.humidity()
            ldr_value = ldr.read()
            intensitas_cahaya = (ldr_value / 4095) * 100
            
            print(f"🌡 Suhu={suhu}°C, Kelembaban={kelembaban}%, Cahaya={intensitas_cahaya:.2f}%")

            if suhu is not None and kelembaban is not None and -40 <= suhu <= 80 and 0 <= kelembaban <= 100:
                data = ujson.dumps({
                    "temperature": suhu,
                    "humidity": kelembaban,
                    "light_intensity": intensitas_cahaya
                })
                print("📡 Mengirim data ke Ubidots:", data)

                try:
                    client.publish(MQTT_TOPIC, data)
                    print("✅ Data berhasil dikirim ke Ubidots!")
                    reconnect_attempts = 0  
                except Exception as e:
                    print("❌ Gagal mengirim ke Ubidots, reconnect MQTT...")
                    reconnect_attempts += 1
                    if reconnect_attempts > 3:
                        print("❌ Gagal reconnect MQTT lebih dari 3 kali. Restart ESP32...")
                        reset()
                    client = connect_mqtt()

                for _ in range(3):
                    if send_data_to_api(suhu, kelembaban, intensitas_cahaya):
                        break
                    print("🔄 Mengulangi pengiriman ke API Flask...")
                    time.sleep(2)

            else:
                print("⚠ Data sensor tidak valid, cek koneksi sensor!")

        except Exception as e:
            print("❌ Error membaca sensor atau mengirim data:", e)

        time.sleep(5)

try:
    if connect_wifi():
        mqtt_client = connect_mqtt()
        if mqtt_client:
            send_data(mqtt_client)
        else:
            print("❌ Gagal menghubungkan MQTT, restart ESP32...")
            reset()
    else:
        print("❌ Gagal terhubung ke WiFi, restart ESP32...")
        reset()
except Exception as e:
    print("❌ Kesalahan utama:", e)
    reset()
