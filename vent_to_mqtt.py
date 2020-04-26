#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import paho.mqtt.client as mqttClient
from ecovent.host import Fan
#import paho.mqtt.publish as mqttPublish
import os
import datetime
import time
import socket
import signal
import sys


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to broker mit rc="+str(rc))
        global Connected
        Connected = True
        # client.subscribe('Vent/Blauberg')
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
    global Ventilator_aus
    global Ventilator_an
    print("Messagetopc="+message.topic + " Message=" + str(message.payload))
    data = str(message.payload)
    data = data[2:len(data)-1]
    print("Message="+data)

    if str(message.topic) == "Vent/Blauberg/Command":
        if data == 'ON':
            print("Ventilator anschalten!")
            Ventilator_aus = False
            Ventilator_an = True
        if data == 'OFF':
            print("Ventilator ausschalten!")
            Ventilator_an = False
            Ventilator_aus = True

def on_subscribe(client, userdata, mid, granted_qos):
    print('Subscribe empfangen: ' + str(mid))


def on_unsubscribe(client, userdata, mid):
    print("Unsubscripe empfangen")


def on_disconnect(client, userdata, rc):
    if rc != 0:
        print("Ein Disconnect wurde empfangen, versuche einen Neuaufbau")
        client.reconnect()


def send_mqtt(fan):
    client.publish("Vent/Blauberg/State", str(fan.state))
    client.publish("Vent/Blauberg/Fan_Speed", fan.speed)
    client.publish("Vent/Blauberg/man_Speed", fan.man_speed)
    client.publish("Vent/Blauberg/Humidity", fan.humidity)
    client.publish("Vent/Blauberg/Airflow", fan.airflow)
    client.publish("Vent/Blauberg/Update", "Online")


def connect_start(client):
    try:
        client.connect(broker_address, port=port)
    except socket.error as error:
        print("Es ist ein Socket Fehler bei der Verbindung zum MQTT Broker aufgetreten! = %s" % error)
        time.sleep(2)
        now = datetime.datetime.now()
        print(now.strftime('%d.%m.%Y - %H:%M:%S') +
              " - Warte auf Verbindung zum Broker")
        connect_start(client)



def abfragenloop():
    global socket_fehler
    global sleeptime
    global Ventilator_aus
    global Ventilator_an
    wait_vent = 0
    alterstatus = ""
    # Voreinstellungen für Host und Port
    host = str(vent.host)
    port = 4000
    # Die zu sendenden Daten
    data = bytes.fromhex('6D6F62696C6501000D0A')
    print(data)
    # # UDP-Socket oeffnen
    addr = (host, port)
    UDPSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    UDPSock.settimeout(5)
    UDPSock.connect((host, port))
    while True:
        try:
            # Nachricht senden
            UDPSock.sendto(data, addr)
            response = UDPSock.recv(98)
            now = datetime.datetime.now()
            print(now.strftime('%d.%m.%Y - %H:%M:%S') +
                  " Antwort=" + str(response))
            vent.parse_response(response[6:])
            status = str(vent.state) + str(vent.speed) + str(vent.man_speed) + str(vent.humidity) + str(vent.airflow)
            if (Ventilator_aus == True) and (vent.state == "on"):
                print("Vent aus:")
                UDPSock.sendto(bytes.fromhex('6D6F62696C6503000D0A'), addr)
            if (Ventilator_aus == True) and (vent.state == "off"):
                    Ventilator_aus = False
                    print("Die Variable Ventilator_aus wird auf False gesetzt")
            if (Ventilator_an == True) and (vent.state == "off"):
                print("Vent an:")
                UDPSock.sendto(bytes.fromhex('6D6F62696C6503000D0A'), addr)
            if (Ventilator_an == True) and (vent.state == "on"):
                    Ventilator_an = False
                    print("Die Variable Ventilator_an wird auf False gesetzt")
            print(status + " Anzahl der gesamten Socket_Error = " + str(socket_fehler))
            if alterstatus != status:
                send_mqtt(vent)
            alterstatus = status
            client.publish("Vent/Blauberg/Status", "Online")
            wait_vent = 0
            signal.signal(signal.SIGTERM, exit_gracefully)
            time.sleep(sleeptime)
        except socket.timeout as error:
            print("Socket Error: %s" % error)
            client.publish("Vent/Blauberg/Status", "Offline")
            socket_fehler += 1
            time.sleep(sleeptime )
            now = datetime.datetime.now()
            print(now.strftime('%d.%m.%Y - %H:%M:%S') +
                  " - Warte auf eine Antwort vom Ventilationssystem #" + str(wait_vent))
            wait_vent += 1
            pass
        except socket.error as error:
            print("Unbehandelter Socket Fehler: %s" % error)
            UDPSock.close()
            time.sleep(5)
            UDPSock.connect((host, port))
            pass
        except (KeyboardInterrupt, SystemExit):
            print("Beende Loop")
            UDPSock.close()
            sys.exit(0)



def exit_gracefully(signum, frame):
    client.publish("Vent/Blauberg/Status", "Offline")
    print("Beende den Dienst aufgrund TERM Signal")
    client.disconnect()
    time.sleep(1)
    sys.exit(0)

# ---------------------------------------------------------------------
Connected = False
fan = Fan("192.168.x.xxx")  # Adresse des Ventilators
vent = fan  # Adresse des Ventilators, nur zum parsen des Sockets ohne Close des Sockets
anzahl_fehler = 0  # Initialisierung
max_retries = 10  # Anzahl der Timeouts, bevor die Verbindung als OFFLINE gemeldet wird
sleeptime = 5  # Sekunden zwischen den Abfragen
socket_fehler = 0
Ventilator_an = False
Ventilator_aus= False

broker_address = "127.0.0.1"  # Your MQTT broker IP address
port = 1883  # default port change as required
user = "dein_user"  # mqtt user name change as required
password = "dein_passwort"  # mqtt password change as required
client = mqttClient.Client("Vent")
client.username_pw_set(user, password=password)
client.on_connect = on_connect
client.on_message = on_message
client.on_subscribe = on_subscribe
client.on_unsubscribe = on_unsubscribe
client.on_disconnect = on_disconnect

connect_start(client)

# lauschen ob Befehle gesendet werden
client.subscribe("Vent/Blauberg/Command", 0)
client.loop_start()

while Connected != True:
    time.sleep(2)
    now = datetime.datetime.now()
    print(now.strftime('%d.%m.%Y - %H:%M:%S') +
          " - Warte!")
    client.connect(broker_address, port=port)

try:
    while True:
        signal.signal(signal.SIGTERM, exit_gracefully)
        abfragenloop()

except (KeyboardInterrupt, SystemExit):
    client.publish("Vent/Blauberg/Status", "Offline")
    print("Starte Cleanup")
    client.loop_stop()
    time.sleep(2)
    client.disconnect()
    print("Bye")
    sys.exit(0)
