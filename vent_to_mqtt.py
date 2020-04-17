import paho.mqtt.client as mqttClient
from ecovent.host import Fan #bew name, because the original source not available for Python 3.5
import os
import datetime
import time


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to broker mit rc="+str(rc))
        global Connected
        Connected = True
        client.subscribe('Vent/Blauberg')
    elif rc == 1:
        print("Falsche Protokollversion")
    elif rc == 2:
        print("Identifizierung fehlgeschlagen")
    elif rc == 3:
        print("Server nicht erreichbar")
    elif rc == 4:
        print("Falscher Benutzername oder Passwort")
    elif rc == 5:
        print("Nicht autorisiert")
    else:
        print("Ungültiger Returncode")


def on_message(client, userdata, message):
    print("Messagetopc="+message.topic + " Message=" + str(message.payload))
    data = str(message.payload)
    data = data[2:len(data)-1]
    print("Message="+data)
    
    if str(message.topic) == "Vent/Blauberg/Command":
        if data == 'ON':
            print("Ventilator wird versucht zu aktivieren")
            fan.set_state_on()
        if data == 'OFF':
            print("Ventilator wird versucht zu deaktivieren")
            fan.set_state_off()
        


def on_subscribe(client, userdata, mid, granted_qos):
    print('Subscribe empfangen: ' + str(mid))
    print(client)


def on_unsubscribe(client, userdata, mid):
    print("Unsubscripe empfangen")


def send_mqtt(fan):
    client.publish("Vent/Blauberg/State", str(fan.state))
    client.publish("Vent/Blauberg/Fan_Speed", fan.speed)
    client.publish("Vent/Blauberg/man_Speed", fan.man_speed)
    client.publish("Vent/Blauberg/Humidity", fan.humidity)
    client.publish("Vent/Blauberg/Airflow", fan.airflow)
    client.publish("Vent/Blauberg/Update", "Online")


# ---------------------------------------------------------------------
Connected = False
fan = Fan(xxx.xxx.xxx.xx")  # Adresse des Ventilators
anzahl_fehler = 0  # Initialisierung
max_retries = 10  # Anzahl der Timeouts, bevor die Verbindung als OFFLINE gemeldet wird
sleeptime = 15  # Sekunden zwischen den Abfragen

broker_address = "127.0.0.1"  # Your MQTT broker IP address
port = 1883  # default port change as required
user = "username"  # mqtt user name change as required
password = "password"  # mqtt password change as required
client = mqttClient.Client("Vent")
client.username_pw_set(user, password=password)
client.on_connect = on_connect
client.on_message = on_message
client.on_subscribe = on_subscribe
client.on_unsubscribe = on_unsubscribe
client.connect(broker_address, port=port)
client.subscribe("Vent/Blauberg", 0)     
client.loop_start()


if (fan.update()) == 0:
    send_mqtt(fan)


while Connected != True:
    time.sleep(0.2)
try:
    while True:
        time.sleep(sleeptime)
        erfolg = fan.update()
        now = datetime.datetime.now()
        if erfolg == 0:
            send_mqtt(fan)
            anzahl_fehler = 0
            alterstatus = str(fan.state) + str(fan.speed) + \
                str(fan.man_speed) + str(fan.humidity) + str(fan.airflow)
            print(now.strftime('%d.%m.%Y - %H:%M:%S') + " - " + alterstatus)
        else:
            print(now.strftime('%d.%m.%Y - %H:%M:%S') +
                  " - Update fehlgeschlagen #" + str(anzahl_fehler))
            anzahl_fehler += 1


except KeyboardInterrupt:
    client.publish("Vent/Blauberg/Status", "Offline")
    print("exiting begin")
    client.disconnect()
    client.loop_stop()
    print("exiting")
