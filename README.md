# vent_to_mqtt

Die py. Datei auf dem openhab System als Dienst starten lassen.
Diese sendet permanent den Status in den einzelnen Bereichen.
Über den Command Bereich kann der Ventilator ein/ausgeschaltet werden.

Meine Konfiguration im Openhab:

.Things

Bridge mqtt:broker:xxxhome [ host="localhost", secure=false, username="xxxx", password="xxx" ]
{
Thing topic FF_Bedroom_Vent "Ventilator" @ "Schlafzimmer"{
    Channels:
            Type switch : vent_state [ stateTopic="Vent/Blauberg/State", transformationPattern="map:blauberg.map" , commandTopic="Vent/Blauberg/Command", on="ON", off="OFF"]
            Type number : luftfeuchtigkeit[ stateTopic="Vent/Blauberg/Humidity" ]
            Type string : geschwindigkeit [ stateTopic="Vent/Blauberg/Fan_Speed" ]
            Type string : Airflow [ stateTopic="Vent/Blauberg/Airflow" ]	
}
}  

.items
Switch FF_Bedroom_Ventilation_State "Ventilator TEST" (gContact, FF_Bedroom) {channel="mqtt:topic:boschhome:FF_Bedroom_Vent:vent_state "}
Number FF_Bedroom_Ventilation_Luftfeuchtigkeit "Luftfeuchtigkeit Ventilation" (gHumidity,FF_Bedroom)  {channel="mqtt:topic:boschhome:FF_Bedroom_Vent:luftfeuchtigkeit"}
String FF_Bedroom_Ventilation_Geschwindigkeit "Geschwindigkeit" (FF_Bedroom)  {channel="mqtt:topic:boschhome:FF_Bedroom_Vent:geschwindigkeit"}
String FF_Bedroom_Ventilation_Airflow "Modus" (FF_Bedroom)  {channel="mqtt:topic:boschhome:FF_Bedroom_Vent:Airflow"}



blauberg.map
on=ON
off=OFF

