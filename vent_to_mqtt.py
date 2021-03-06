#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import paho.mqtt.client as mqttClient
import os
import datetime
import time
import socket
import signal
import sys


'''
        Dieses Programm ermöglicht es, einen Blauberg Ventilator per mqtt in eine Hausautomationsumgebung einzubinden.
        
        Hauptprogramm: Michael H. Bosch
        Routinen parsebytes und parse_response sind dem Modul pyEcovent entnommen, welches unter MIT Lizenz veröffentlicht wurde: https://github.com/aglehmann/pyEcovent


'''


class Ventilator:
    def __init__(self, name):
       self.name = name

    def parsebytes(self, bytestring, params):
        i = iter(bytestring)
        for param in i:
            value = [next(i) for _ in range(params[param][0])]
            yield(param,value)

    def parse_response(self, data):
        fan_params = {
        0x03: [1, 'state', None],
        0x04: [1, 'speed', None],
        0x05: [1, 'manual_speed', None],
        0x06: [1, 'air_flow_direction', None],
        0x08: [1, 'humidity_level', None],
        0x09: [1, 'operation_mode', None],
        0x0B: [1, 'humidity_sensor_threshold', None],
        0x0C: [1, 'alarm_status', None],
        0x0D: [1, 'relay_sensor_status', None],
        0x0E: [3, 'party_or_night_mode_countdown', None],
        0x0F: [3, 'night_mode_timer', None],
        0x10: [3, 'party_mode_timer', None],
        0x11: [3, 'deactivation_timer', None],
        0x12: [1, 'filter_eol_timer', None],
        0x13: [1, 'humidity_sensor_status', None],
        0x14: [1, 'boost_mode', None],
        0x15: [1, 'humidity_sensor', None],
        0x16: [1, 'relay_sensor', None],
        0x17: [1, '10V_sensor', None],
        0x19: [1, '10V_sensor_threshold', None],
        0x1A: [1, '10V_sensor_status', None],
        0x1B: [32, 'slave_device_search', None],
        0x1C: [4, 'response_slave_search', None],
        0x1F: [1, 'cloud_activation', None],
        0x25: [1, '10V_sensor_current_status', None]
        }

        for pair in self.parsebytes(data, fan_params):
            if pair[0] == 3:
                self.state = pair[1][0]
            elif pair[0] == 4:
                self.speed = pair[1][0]
            elif pair[0] == 5:
                self.man_speed = pair[1][0]
            elif pair[0] == 6:
                self.airflow = pair[1][0]
            elif pair[0] == 8:
                self.humidity = pair[1][0]


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to broker mit rc="+str(rc))
        global Connected
        Connected = True
        client.subscribe([("Vent/Blauberg/Command/State", 0),("Vent/Blauberg/Command/Speed", 0),("Vent/Blauberg/Command/Airflow", 0)])

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
    global Ventilator_state
    global Ventilator_speed
    global Ventilator_airflow
    global change_onoff
    global change_speed
    global change_airflow

    print("Messagetopic=" + message.topic + " Message=" + str(message.payload))
    data = str(message.payload)
    data = data[2:len(data)-1]
    print("Message="+data)

    if str(message.topic) == "Vent/Blauberg/Command/State":
        Ventilator_state = data
        change_onoff = True

    if str(message.topic) == "Vent/Blauberg/Command/Speed":
        Ventilator_speed = data
        change_speed = True

    if str(message.topic) == "Vent/Blauberg/Command/Airflow":
        Ventilator_airflow = data
        change_airflow = True



def on_subscribe(client, userdata, mid, granted_qos):
    print('Subscribe empfangen: ' + str(mid))


def on_unsubscribe(client, userdata, mid):
    print("Unsubscribe empfangen")


def on_disconnect(client, userdata, rc):
    if rc != 0:
        print("Ein Disconnect wurde empfangen, versuche einen Neuaufbau")
        client.reconnect()


def send_mqtt(msgs):
    client.publish("Vent/Blauberg/Status", str(msgs))
    client.publish("Vent/Blauberg/Service", "Online")


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
    global Ventilator_state
    global Ventilator_speed
    global Ventilator_airflow
    global Ventilator_IP
    global change_onoff
    global change_airflow
    global change_speed
    wait_vent = 1
    alterstatus = ""

    HEADER = bytes.fromhex('6D6F62696C65')
    FOOTER = bytes.fromhex('0D0A')

    # Voreinstellungen für Host und Port
    host = str(Ventilator_IP)
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
            Vent.parse_response(response[6:])
            status = str(Vent.state) + "-" + str(Vent.speed) + "-"  + str(Vent.man_speed) + "-" + str(Vent.humidity) + "-"  + str(Vent.airflow)
            if Ventilator_state == False:
                Ventilator_state = Vent.state
            if Ventilator_speed == False:
                Ventilator_speed = Vent.speed
            if Ventilator_airflow == False:
                Ventilator_airflow = Vent.airflow
 
            if int(Ventilator_state) != int(Vent.state):
                    if change_onoff == True:
                        print ("Der An/Aus Status ist verschieden! " + str(Ventilator_state ) + " - " + str(Vent.state) )
                        UDPSock.sendto(bytes.fromhex('6D6F62696C6503000D0A'), addr)
                    else:
                        Ventilator_state = Vent.state
            else:
                    change_onoff = False
            if int(Ventilator_speed) != int(Vent.speed):
                if change_speed == True:
                    print ("Der Geschwindigkeits Status ist verschieden! " + str(Ventilator_speed ) + " - " + str(Vent.speed) )
                    cmd= '04' + '{0:0{1}x}'.format(int(Ventilator_speed),2)
                    UDPSock.sendto((HEADER + bytes.fromhex(cmd) + FOOTER), addr)
                else:
                    Ventilator_speed = Vent.speed
            else:
                change_speed = False
            if int(Ventilator_airflow) != int(Vent.airflow):
                if change_airflow == True:
                    print ("Der Airflow Status ist verschieden! " + str(Ventilator_airflow ) + " - " + str(Vent.airflow) )
                    cmd= '06' + '{0:0{1}x}'.format(int(Ventilator_airflow),2)
                    UDPSock.sendto((HEADER + bytes.fromhex(cmd) + FOOTER), addr)
                else:
                    Ventilator_airflow = Vent.airflow
            else:
                change_airflow = False
            #print("Status = " + status) # + " Anzahl der gesamten Socket_Error = " + str(socket_fehler))
            payload = { 'State': str(Vent.state),'Humidity': str(Vent.humidity), 'Speed': str(Vent.speed), 'Airflow': str(Vent.airflow), 'Man_speed' : str(Vent.man_speed)}
            print (payload)
            if alterstatus != status:
                send_mqtt(payload)
            alterstatus = status
            client.publish("Vent/Blauberg/Service", "Online")
            wait_vent = 1
            signal.signal(signal.SIGTERM, exit_gracefully)
            time.sleep(sleeptime)
        except socket.timeout as error:
            print("Socket Error: %s" % error)
            client.publish("Vent/Blauberg/Service", "TimeOut")
            socket_fehler += 1
            time.sleep(sleeptime)
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
    client.publish("Vent/Blauberg/Service", "Service Down")
    print("Beende den Dienst aufgrund TERM Signal")
    client.disconnect()
    time.sleep(1)
    sys.exit(0)

# ---------------------------------------------------------------------
Connected = False
Vent = Ventilator("Bosch")
Ventilator_IP = "192.168.0.150"
anzahl_fehler   = 0  # Initialisierung
#max_retries     = 10  # Anzahl der Timeouts, bevor die Verbindung als OFFLINE gemeldet wird
sleeptime       = 5  # Sekunden zwischen den Abfragen
socket_fehler   = 0
Ventilator_state = False
Ventilator_speed = False
Ventilator_airflow = False
change_onoff = False
change_speed = False
change_airflow = False


broker_address = "127.0.0.1"  # Your MQTT broker IP address
port = 1883  # default port change as required
user = "youruser"  # mqtt user name change as required
password = "yourpassword"  # mqtt password change as required
client = mqttClient.Client("Vent")
client.username_pw_set(user, password=password)
client.on_connect = on_connect
client.on_message = on_message
client.on_subscribe = on_subscribe
client.on_unsubscribe = on_unsubscribe
client.on_disconnect = on_disconnect

connect_start(client)

# lauschen ob Befehle gesendet werden
client.subscribe([("Vent/Blauberg/Command/State", 0),("Vent/Blauberg/Command/Speed", 0),("Vent/Blauberg/Command/Airflow", 0)])
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
    client.publish("Vent/Blauberg/Service", "Service Down")
    print("Starte Cleanup")
    client.loop_stop()
    time.sleep(2)
    client.disconnect()
    print("Bye")
    sys.exit(0)
