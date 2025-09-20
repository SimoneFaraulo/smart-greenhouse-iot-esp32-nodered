import time
import ujson
import network
import json
from time import sleep
from pump import PUMP
from environment_sensor import ENVIRONMENT_SENSOR
from cistern import CISTERN
from machine import Pin, PWM
from oled import OLED
from ldr import LDR
from fan import FAN
from door import DOOR
from ground_sensor import GROUND_SENSOR
from mqtt_client import MQTT

"""DEFINIZIONE DEI PARAMETRI UTILIZZATI DAL SISTEMA"""

#WI-FI PARAMETERS
WIFI_SSID = 'Simone'
WIFI_PASSWORD = 'simonefaraulo'

# MQTT SERVER PARAMETERS
MQTT_CLIENT_ID = "gruppo09"
MQTT_BROKER    = "test.mosquitto.org"
MQTT_USER      = ""
MQTT_PASSWORD  = ""

#MQTT topic a cui il client deve pubblicare i dati letti dai vari sensori
# e lo stato dei vari attuatori del sistema.
# STRUTTURA DEI TOPIC:
# I topic sono suddivisi per area tematica Es: Ground, Irrigation, Environment ecc,
# ad ogni sensore/attuatore appartenete ad un area tematica viene assegnato un topic univoco
MQTT_GROUND_HUMIDITY = "SmartGreenhouse/Ground/Humidity"
MQTT_ENVIRONMENT_TEMP = "SmartGreenhouse/Environment/Temp"
MQTT_ENVIRONMENT_HUMIDITY = "SmartGreenhouse/Environment/Humidity"
MQTT_CISTERN_LEVEL = "SmartGreenhouse/Irrigation/Cistern"
MQTT_OUTSIDE_LUX = "SmartGreenhouse/External/Lum"
MQTT_FAN_STATE = "SmartGreenhouse/Ventilation/Fan"
MQTT_PUMP_STATE = "SmartGreenhouse/Irrigation/Pump"
MQTT_LED_STATE = "SmartGreenhouse/Lights/LED"
MQTT_DOOR_STATE = "SmartGreenhouse/DoorState"

#MQTT topic a cui il client deve sottoscriversi per ricevere 
#i dati dal broker mqtt.
#I topic di sottoscrizione sono strutturati allo stesso modo dei topic per la publicazione
MQTT_SUBSCRIBE_TOPIC =  { 
    "MQTT_IRRIGATION_MANUALCONTROL" : b'SmartGreenhouse/Irrigation/ManualState',
    "MQTT_IRRIGATION_MANUALPUMP" : b'SmartGreenhouse/Irrigation/ManualPump',
    "MQTT_IRRIGATION_HUMIDITY" : b'SmartGreenhouse/Irrigation/Humidity',
    "MQTT_FAN_MANUALSTATE" : b'SmartGreenhouse/Ventilation/ManualFan',
    "MQTT_FAN_MANUALCONTROL" : b'SmartGreenhouse/Ventilation/ManualState',
    "MQTT_FAN_ACTIVATIONTEMP" : b'SmartGreenhouse/Ventilation/Temp',
    "MQTT_LIGHTS_MANUALCONTROL" : b'SmartGreenhouse/Lights/ManualState',
    "MQTT_LIGHTS_MANUALLED" : b'SmartGreenhouse/Lights/ManualLED',
    "MQTT_LIGHTS_LEVEL" : b'SmartGreenhouse/Lights/Lum',
    "MQTT_RESET_SYSTEM" : b'SmartGreenhouse/Restart'
}

#Dizionario di valori che arrivano dai sensori e dallo stato degli attuatori da pubblicare sul rispettivo topic
#k = topic di pubblicazione, v = value da pubblicare sul topic
MQTT_PUBLISH_VALUE = {
    MQTT_GROUND_HUMIDITY :  None,
    MQTT_ENVIRONMENT_TEMP :  None,
    MQTT_ENVIRONMENT_HUMIDITY :  None,
    MQTT_CISTERN_LEVEL:  None,
    MQTT_OUTSIDE_LUX :  None,
    MQTT_FAN_STATE :  None,
    MQTT_PUMP_STATE : None,
    MQTT_LED_STATE : None,
    MQTT_DOOR_STATE : None
}

#Dizionario che contiene i valori aggiornati prelevati dai sensori ad ogni ciclo di lettura 
#k = topic associato al sensore, v = value letto dal sensore durante il ciclo di lettura
SENSORS_ACTUAL_VALUE = {
    MQTT_GROUND_HUMIDITY :  None,
    MQTT_ENVIRONMENT_TEMP :  None,
    MQTT_ENVIRONMENT_HUMIDITY :  None,
    MQTT_CISTERN_LEVEL:  None,
    MQTT_OUTSIDE_LUX :  None,
}

#Dizionario di parametri che sono settati sulla base delle informazioni che arrivano dal broker e dalla computazione del sistema
#il dizionario ha lo scopo di mantenere dei valori sulla base dei quali saranno effettuate delle specifiche operazioni.
#I parametri di default del sistema rappresentano lo stato del sistema subito dopo l'avviamento
#le modifiche apportate su questi parametri comportano variazioni nel flusso di esecuzione della logica del sistema
#queste variazioni possono essere causate da eventuali input
#possono provenire sia dal broker mqtt che dai sensori
SYSTEM_PARAMS = {
    "BOOT" : True,
    "DOOR_OPEN": False,
    "PRINT_SYS_STATE" : True,
    "CRITICAL_CISTERN_LEVEL" : 10,
    "HUMIDITY_CRITICAL_LEVEL" : 10,
    "MANUAL_IRRIGATION_CONTROL" : False,
    "MANUAL_IRRIGATION_PUMP": False,
    "MANUAL_FAN_CONTROL" : False,
    "MANUAL_FAN_STATE": False,
    "MANUAL_LIGHTS_CONTROL" : False,
    "MANUAL_LIGHTS_LEVEL": 0,
    "LIGHTS_OFF_LEVEL": 20,
    "BLOCK_IRRIGATION_FOR_CRITICAL_CISTERN_LEVEL": False,
    "RESTART_SYSTEM": False,
    "FAN_ACTIVATION_TEMP": 30,
    "PUMP_CICLE": False
}

#IRQ_LOCK utilizzato per bloccare le altre irq del sistema nel caso in cui il sistema è
#in fase di boot o fi riavvio
IRQ_LOCK = False

#CISTERN PARAMETERS
CISTERN_TRIGGER_PIN = 26
CISTERN_ECHO_PIN = 25
CISTERN_HEIGHT = 12

#PUMP PARAMETERS
PUMP_PIN = 2

#ENVIRONMENT_SENSOR PARAMETERS
ENVIRONMENT_SENSOR_PIN = 4

#PHOTO_RESISTOR PARAMETERS
PHOTO_RESISTOR_PIN = 35
PHOTO_RESISTOR_MIN_VALUE = 0
PHOTO_RESISTOR_MAX_VALUE = 100

#LED_ZONE_1 PARAMETERS
LED1_PIN = 13
LED1_FREQ = 50

#LED_ZONE_2 PARAMETERS
LED2_PIN = 19
LED2_FREQ = 50

#FAN PARAMETERS
FAN_PIN = 14

#GROUND_SENSOR PARAMETERS
GROUND_SENSOR_PIN = 33
GROUND_SENSOR_MAX_READ = 4095
GROUND_SENSOR_MIN_READ = 1000
GROUND_SENSOR_MIN_VALUE = 0
GROUND_SENSOR_MAX_VALUE = 100

#OLED_DISPLAY PARAMETERS
OLED_WIDTH = 128
OLED_HEIGHT = 64
OLED_SLC_PIN = 22
OLED_SDA_PIN = 32
OLED_FILL = 0
OLED_COLOR = 1

#DOOR PARAMETERS
DOOR_PIN = 23
DOOR_CLOSE_ANGLE = 180
DOOR_OPEN_ANGLE = 110

#REstart_BTN PARAMETERS
RESTART_BTN_PIN = 15

#DOOR_BTN PARAMETERS
DOOR_BTN_PIN = 34

#BOUNCING BTNs VAR
LAST_RESET = 0
DELTA_MAX_RESET = 300
LAST_DOOR = 0
DELTA_MAX_DOOR = 1000

#Valori massimi e minimi inviati e ricevuti al/dal broker mqtt
DASH_MAX_VAL = 100
DASH_MIN_VAL = 0 

"""IMPLEMENTAZIONE DELLA LOGICA DEL SISTEMA"""

#ISTANZIAZIONE DEGLI OGGETTI DEL SISTEMA
restart_btn = Pin(RESTART_BTN_PIN, Pin.IN, Pin.PULL_DOWN) #bottone utilizzato per l'hard-restart del sistema
door_btn = Pin(DOOR_BTN_PIN, Pin.IN, Pin.PULL_DOWN) #bottone utilizzato per l'apertura e la chiusura della porta
cistern = CISTERN(CISTERN_TRIGGER_PIN, CISTERN_ECHO_PIN, CISTERN_HEIGHT) #consente la gestione del serbatoio tramite dei metodi di interfaccia di alto livello
pump = PUMP(PUMP_PIN) #consente la gestione della pompa tramite dei metodi di interfaccia di alto livello
environment_sensor = ENVIRONMENT_SENSOR(ENVIRONMENT_SENSOR_PIN) #consente la lettura dei dati dal sensore DHT22 tramite dei metodi di interfaccia di alto livello
photo_resistor = LDR(PHOTO_RESISTOR_PIN, PHOTO_RESISTOR_MIN_VALUE, PHOTO_RESISTOR_MAX_VALUE) #consente di leggere dati dal fotoresistore convertiti in un range (MIN, MAX)
ground_sensor = GROUND_SENSOR(GROUND_SENSOR_PIN, GROUND_SENSOR_MIN_VALUE, GROUND_SENSOR_MAX_VALUE, GROUND_SENSOR_MAX_READ, GROUND_SENSOR_MIN_READ) #consente di leggere dati dal sensore di umidità del terreno tramite dei metodi di interfaccia di alto livello
client = MQTT(MQTT_CLIENT_ID, MQTT_BROKER) #consente di gestire la connessione e lo scambio di messaggi con il server MQTT
oled = OLED(OLED_WIDTH, OLED_HEIGHT, OLED_SLC_PIN, OLED_SDA_PIN) #consente di stampare a testo sullo schermo OLED SSD1306 fornendo dei metodi di interfaccia di alto livello
fan = FAN(FAN_PIN) #consente di pilotare la ventola tamite dei metodi di interfaccia di alto livello
door = DOOR(DOOR_PIN, DOOR_CLOSE_ANGLE, DOOR_OPEN_ANGLE) #consente di pilotare la porta specificando l'angolo di chiusura della porta e l'angolo di apertura della porta 
led1 = PWM(Pin(LED1_PIN, Pin.OUT), freq=LED1_FREQ) #consete di pilotare un led in PWM
led2 = PWM(Pin(LED2_PIN, Pin.OUT), freq=LED2_FREQ) #consete di pilotare un led in PWM

#Inizializza il duty cycle dei led a 0 in modo tale da tenerli spenti all'accensione del sistema 
led1.duty(0) 
led2.duty(0)

"""DEFINIZIONE DELLE PROCEDURE CHE IMPLEMENTANO LA LOGICA DEL SISTEMA"""

#Questa funzione implemeta la logica che consente di connettere l'esp32 al WI-FI
def wifi_connect():

    global oled
    global OLED_COLOR
    
    try: #Prova ad eseguire la connessione
        shift_point = 0
        print("Connecting to WiFi", end="")
        #Stampa sul display oled lo stato del sistema 
        oled.print_line("Connecting", 0, 1, OLED_COLOR)
        oled.print_line_no_fill("to Wifi", 0, 10, OLED_COLOR)
        #Avvia la procedura di connessione
        sta_if = network.WLAN(network.STA_IF)
        sta_if.active(True)
        sta_if.connect(WIFI_SSID, WIFI_PASSWORD)
        while not sta_if.isconnected(): #Aspetta che la scheda sia connessa al WI-FI
            print(".", end="")
            oled.print_line_no_fill(".", 53 + shift_point, 10, OLED_COLOR)
            time.sleep(0.1)
            shift_point = shift_point + 6
        print(" Connected!")
        #Stampa sul display oled il risultato della procedura di connessione al WI-FI
        oled.print_line_no_fill("Connected!", 0, 20, OLED_COLOR)
    except OSError as ex: #Cattura un eccezione che indica il fallimento della procedura di connessione
        print("Failure connecting to WiFi!!")
        #Stampa sul display oled il risultato della procedura di connessione al WI-FI
        oled.print_line("Not Connected!", 0, 1, OLED_COLOR)
        for i in range(10, 0, -1): #Ciclo che mette in attesa il sistema per 10 secondi
            oled.fill_rect(60, 10, 80, 10, OLED_FILL)
            oled.print_line_no_fill("Retrying in " + str(i) + "s", 0, 10, OLED_COLOR)
            time.sleep(1)
        wifi_connect() #Al termine dell'attesa la funzione riproverà ad eseguire la procedura di connessione
        
#Questa funzione implementa la logica che il sistema deve eseguire durante le operazioni di riavvio
#manuale oppure di riavvio richiesto tramite broker mqtt, riporta il sistema allo stato iniziale 
def restart_procedure():

    global MQTT_PUBLISH_VALUE, SYSTEM_PARAMS, SENSORS_ACTUAL_VALUE
    global MQTT_GROUND_HUMIDITY
    global MQTT_ENVIRONMENT_TEMP
    global MQTT_ENVIRONMENT_HUMIDITY
    global MQTT_CISTERN_LEVEL
    global MQTT_OUTSIDE_LUX
    global MQTT_FAN_STATE
    global MQTT_DOOR_STATE
    global MQTT_PUMP_STATE
    global OLED_COLOR
    global led, pump, fan, oled, client, door

    #Stampa sul display oled lo stato del sistema indicando che il sistema è in fase
    #riavvio
    oled.print_line("Restarting the", 0, 1, OLED_COLOR)
    oled.print_line_no_fill("system", 0, 10, OLED_COLOR)
    shift_point = 0

    #Forza lo stato di tutti gli attuatori del sistema
    pump.stop_pump() #Disattiva la pompa
    led1.duty(0) #Spegne il led1
    led2.duty(0) #Spegne il led2
    fan.stop_fan() #Spegne la ventola
    door.close_door() #Chiude la porta

    try:
        #Invia al broker MQTT i dati azzerati in formato JSON
        client.publish(MQTT_GROUND_HUMIDITY, ujson.dumps({"humidity" : 0}))
        client.publish(MQTT_ENVIRONMENT_TEMP, ujson.dumps({"temp" : 0}))
        client.publish(MQTT_ENVIRONMENT_HUMIDITY, ujson.dumps({"humidity" : 0}))
        client.publish(MQTT_CISTERN_LEVEL, ujson.dumps({"cistern_level" : 0}))
        client.publish(MQTT_OUTSIDE_LUX, ujson.dumps({"light" : 0}))
        client.publish(MQTT_FAN_STATE, ujson.dumps({"fan" : 0}))
        client.publish(MQTT_PUMP_STATE,  ujson.dumps({"pump" : 0}))
        client.publish(MQTT_LED_STATE, ujson.dumps({"light" : 0}))
        client.publish(MQTT_DOOR_STATE, ujson.dumps({"door" : 0}))
    except OSError as e:
        print("Error during the sensors data pubblication: ", e)

    while shift_point < 28:
        oled.print_line_no_fill(".", 45 + shift_point, 10, OLED_COLOR)
        time.sleep(0.1)
        shift_point = shift_point + 6

    #Riporta i paramentri di sistema ai valori iniziali 
    SYSTEM_PARAMS = {
        "BOOT" : True,
        "DOOR_OPEN": False,
        "PRINT_SYS_STATE" : True,
        "CRITICAL_CISTERN_LEVEL" : 10,
        "HUMIDITY_CRITICAL_LEVEL" : 10,
        "MANUAL_IRRIGATION_CONTROL" : False,
        "MANUAL_IRRIGATION_PUMP": False,
        "MANUAL_FAN_CONTROL" : False,
        "MANUAL_FAN_STATE": False,
        "MANUAL_LIGHTS_CONTROL" : False,
        "MANUAL_LIGHTS_LEVEL": 0,
        "LIGHTS_OFF_LEVEL": 20,
        "BLOCK_IRRIGATION_FOR_CRITICAL_CISTERN_LEVEL": False,
        "RESTART_SYSTEM": False,
        "FAN_ACTIVATION_TEMP": 30,
        "PUMP_CICLE": False
    }

    #Resetta il dizionario che contiene i valori
    #che arrivano dai sensori e dallo stato degli 
    #attuatori da pubblicare sul rispettivo topic
    MQTT_PUBLISH_VALUE = {
        MQTT_GROUND_HUMIDITY :  None,
        MQTT_ENVIRONMENT_TEMP :  None,
        MQTT_ENVIRONMENT_HUMIDITY :  None,
        MQTT_CISTERN_LEVEL:  None,
        MQTT_OUTSIDE_LUX :  None,
        MQTT_FAN_STATE :  None,
        MQTT_PUMP_STATE : None,
        MQTT_LED_STATE : None,
        MQTT_DOOR_STATE : None
    }

    #Resetta il dizionario che contiene i valori aggiornati 
    #prelevati dai sensori ad ogni ciclo di lettura 
    SENSORS_ACTUAL_VALUE = {
        MQTT_GROUND_HUMIDITY :  None,
        MQTT_ENVIRONMENT_TEMP :  None,
        MQTT_ENVIRONMENT_HUMIDITY :  None,
        MQTT_CISTERN_LEVEL:  None,
        MQTT_OUTSIDE_LUX :  None,
    }

#Questa funzione implementa la logica di controllo automatico del sistema di ventilazione
#La procedura come tutte le procedure di controllo automatico è eseguita di default all'avvio
#e al riavvio del sistema
#la procedura non è eseguita se il sistema di ventilazione è sotto controllo manuale tramite la dashboard
def auto_fan_control():
    
    global SYSTEM_PARAMS, MQTT_PUBLISH_VALUE, MQTT_FAN_STATE
    global OLED_COLOR, OLED_FILL
    global fan, oled, client

    #Stampa sul display oled le informazioni di stato aggiornate indicando che il controllo della ventilazione
    #è in modalità AUTOMATICA
    oled.fill_rect(35, 20, 30, 10, OLED_FILL)
    oled.print_line_no_fill("AUT=>", 35, 20, OLED_COLOR)

    actual_temp = environment_sensor.get_last_temperature() #Legge l'ultimo valore di temperatura dell'ambiente rilevato 
                                                            #dal sensore di temperatura dell'ambiente (environment_sensor),
                                                            #ritorna un valore espresso in gradi C
    if SYSTEM_PARAMS["FAN_ACTIVATION_TEMP"] != None and actual_temp > SYSTEM_PARAMS["FAN_ACTIVATION_TEMP"]: #Verifica se l'ultima temperatura rilevata è maggiore 
                                                                                                            #del valore della temperatura di soglia oltre il quale
                                                                                                            #il sistema di ventilazione deve essere attivato, il valore di 
                                                                                                            #default della soglia è impostato a 30° ma modificabile tramite
                                                                                                            #dashboard
        fan.start_fan() #Se la temperatura dell'ambiente supera la temperatura di soglia 
                        #attiva la ventola tramite un metodo della classe FAN sull'oggetto fan
                        #che fornisce un astrazione di alto livello della ventola
        
        #Stampa sul display oled le informazioni di stato aggiornate indicando che la ventola
        #è attiva
        oled.fill_rect(80, 20, 60, 10, OLED_FILL)
        oled.print_line_no_fill("ON", 80, 20, OLED_COLOR)
        
        MQTT_PUBLISH_VALUE[MQTT_FAN_STATE] = ujson.dumps({"fan" : 1}) #Aggiorna il dizionario che contiene i valori aggiornati da pubblicare 
                                                                      #in particolare aggiorna il valore da pubblicare sul topic in cui viene pubblicato
                                                                      #lo stato della ventola (MQTT_FAN_STATE), il valore aggiornato è rappresentato con una 
                                                                      #stringa in formato JSON
        try:
            #Prova a pubblicare il nuovo valore che rappresenta lo stato della ventola sul topic MQTT_FAN_STATE
            #andando anche ad aggiornare le info di stato sul display oled
            client.publish(MQTT_FAN_STATE, MQTT_PUBLISH_VALUE[MQTT_FAN_STATE])
            oled.fill_rect(55, 10, 80, 10, OLED_FILL)
            oled.print_line_no_fill("Published", 55, 10, OLED_COLOR)
        except OSError as e:
            print("Error during the sensors data pubblication: ", e)
            oled.fill_rect(55, 10, 80, 10, OLED_FILL)
            oled.print_line_no_fill("Error", 55, 10, OLED_COLOR)
    else:
        
        fan.stop_fan()  #Se la temperatura dell'ambiente non supera la temperatura di soglia 
                        #disattiva la ventola tramite un metodo della classe FAN sull'oggetto fan
                        #che fornisce un astrazione di alto livello della ventola

        #Stampa sul display oled le informazioni di stato aggiornate indicando che la ventola
        #non è attiva
        oled.fill_rect(80, 20, 60, 10, OLED_FILL)
        oled.print_line_no_fill("OFF", 80, 20, OLED_COLOR)
        
        MQTT_PUBLISH_VALUE[MQTT_FAN_STATE] = ujson.dumps({"fan": 0}) #Aggiorna il dizionario che contiene i valori aggiornati da pubblicare 
                                                                     #in particolare aggiorna il valore da pubblicare sul topic in cui viene pubblicato
                                                                     #lo stato della ventola (MQTT_FAN_STATE), il valore aggiornato è rappresentato con una 
                                                                     #stringa in formato JSON
        try:
            #Prova a pubblicare il nuovo valore che rappresenta lo stato della ventola sul topic MQTT_FAN_STATE
            #andando anche ad aggiornare le info di stato sul display oled
            client.publish(MQTT_FAN_STATE, MQTT_PUBLISH_VALUE[MQTT_FAN_STATE])
            oled.fill_rect(55, 10, 80, 10, OLED_FILL)
            oled.print_line_no_fill("Published", 55, 10, OLED_COLOR)
        except OSError as e:
            print("Error during the sensors data pubblication: ", e)
            oled.fill_rect(55, 10, 80, 10, OLED_FILL)
            oled.print_line_no_fill("Error", 55, 10, OLED_COLOR)

#Questa funzione implementa la logica di controllo automatico del sistema di irrigazione
#La procedura come tutte le procedure di controllo automatico è eseguita di default all'avvio
#e al riavvio del sistema
#la procedura non è eseguita se il sistema di irrigazione è sotto controllo manuale tramite la dashboard
def auto_irrigation_control():

    global SYSTEM_PARAMS, MQTT_PUBLISH_VALUE, MQTT_PUMP_STATE
    global OLED_COLOR, OLED_FILL
    global oled, pump
    
    #Stampa sul display oled le informazioni di stato aggiornate indicando che il controllo dell'irrigazione
    #è in modalità AUTOMATICA
    oled.fill_rect(40, 30, 30, 10, OLED_FILL)
    oled.print_line_no_fill("AUT=>", 40, 30, OLED_COLOR)
    
    actual_ground_humidity = ground_sensor.get_last_value() #Legge l'ultimo valore di umidità del terreno rilevato 
                                                            #dal sensore di umidità del terreno (ground_sensor), il valore ritornato è compreso in un 
                                                            #range (GROUND_SENSOR_MAX_VALUE, GROUND_SENSOR_MIX_VALUE) 

    if actual_ground_humidity < SYSTEM_PARAMS["HUMIDITY_CRITICAL_LEVEL"]: #Verifica se l'ultimo valore di umidità rilevato è minore
                                                                          #del valore di umidità di soglia critica, il valore della soglia
                                                                          #è impostato di default a a 10% ma modificabile tramite dashboard
                                                                     
                                                                          
        print("Starting pump...", end="")
        pump.start_pump() #se l'ultima umidità rilevata è minore del livello di umidità 
                          #di soglia attiva la pompa tramite un metodo della classe PUMP sull'oggetto pump
                          #che fornisce un astrazione di alto livello della pompa

        #Stampa sul display oled le informazioni di stato aggiornate indicando che la pompa
        #è attiva
        oled.fill_rect(80, 30, 30, 10, OLED_FILL)
        oled.print_line_no_fill("ON", 80, 30, OLED_COLOR)

        MQTT_PUBLISH_VALUE[MQTT_PUMP_STATE] = ujson.dumps({"pump": 1}) #Aggiorna il dizionario che contiene i valori aggiornati da pubblicare 
                                                                       #in particolare aggiorna il valore da pubblicare sul topic in cui viene pubblicato
                                                                       #lo stato della pompa (MQTT_PUMP_STATE), il valore aggiornato è rappresentato con una 
                                                                       #stringa in formato JSON
        try:
            #Prova a pubblicare il nuovo valore che rappresenta lo stato della pompa sul topic MQTT_PUMP_STATE
            #andando anche ad aggiornare le info di stato sul display oled
            client.publish(MQTT_PUMP_STATE, MQTT_PUBLISH_VALUE[MQTT_PUMP_STATE])
            oled.fill_rect(55, 10, 80, 10, OLED_FILL)
            oled.print_line_no_fill("Published", 55, 10, OLED_COLOR)
        except OSError as e:
            print("Error during the sensors data pubblication: ", e)
            ooled.fill_rect(55, 10, 80, 10, OLED_FILL)
            oled.print_line_no_fill("Error", 55, 10, OLED_COLOR)
        
    else:
        pump.stop_pump() #Se l'umidità del terreno supera il livello di umidità di soglia,
                         #disattiva la pompa tramite un metodo della classe PUMP sull'oggetto pump
                         #che fornisce un astrazione di alto livello della pompa

        #Stampa sul display oled le informazioni di stato aggiornate indicando che la pompa
        #non è attiva
        oled.fill_rect(80, 30, 30, 10, OLED_FILL)
        oled.print_line_no_fill("OFF", 80, 30, OLED_COLOR)

        MQTT_PUBLISH_VALUE[MQTT_PUMP_STATE] = ujson.dumps({"pump": 0}) #Aggiorna il dizionario che contiene i valori aggiornati da pubblicare 
                                                                       #in particolare aggiorna il valore da pubblicare sul topic in cui viene pubblicato
                                                                       #lo stato della pompa (MQTT_PUMP_STATE), il valore aggiornato è rappresentato con una 
                                                                       #stringa in formato JSON
        try:
            #Prova a pubblicare il nuovo valore che rappresenta lo stato della pompa sul topic MQTT_PUMP_STATE
            #andando anche ad aggiornare le info di stato sul display oled
            client.publish(MQTT_PUMP_STATE, MQTT_PUBLISH_VALUE[MQTT_PUMP_STATE])
            oled.fill_rect(55, 10, 80, 10, OLED_FILL)
            oled.print_line_no_fill("Published", 55, 10, OLED_COLOR)
        except OSError as e:
            print("Error during the sensors data pubblication: ", e)
            oled.fill_rect(55, 10, 80, 10, OLED_FILL)
            oled.print_line_no_fill("Error", 55, 10, OLED_COLOR)

#Questa funzione implementa la logica di controllo automatico del sistema di illuminazione
#La procedura come tutte le procedure di controllo automatico è eseguita di default all'avvio
#e al riavvio del sistema
#la procedura non è eseguita se il sistema di illuminazione è sotto controllo manuale tramite la dashboard  
def auto_light_control():
    
    global MQTT_PUBLISH_VALUE, MQTT_LED_STATE
    global OLED_COLOR, OLED_FILL
    global led, client

    actual_external_lum = photo_resistor.get_last_value() #Legge l'ultimo valore di luminosità dell'ambiente esterno
                                                          #rilevato dal photo_sensor, il valore ritornato è compreso in un 
                                                          #range (PHOTO_RESISTOR_MAX_VALUE, PHOTO_RESISTOR_MIN_VALUE)

    #Stampa sul display oled le informazioni di stato aggiornate indicando che il controllo dell'illuminazione
    #è in modalità AUTOMATICA
    oled.fill_rect(49, 40, 41, 10, OLED_FILL)
    oled.print_line_no_fill("AUT=>", 49, 40, OLED_COLOR)

    if actual_external_lum < SYSTEM_PARAMS["LIGHTS_OFF_LEVEL"]: #Verifica se l'ultimo valore di luminosità rilevato è minore
                                                                #del valore di luminosità di soglia, valore impostato di default al 20%
                                                                #di luminosità ma modificabile tramite dashboard
        
        actual_external_lum_converted = PHOTO_RESISTOR_MAX_VALUE - actual_external_lum #Se il valore di luminosita rilevato è minore del valore di soglia,
                                                                                       #converte l'valore di luminosità in un valore di luminosità convertito
                                                                                       #che è pari a 100% quando l'effettivo valore della luminosità è pari a 0
                                                                                       #e viceversa, questa operazione è necessaria perchè più bassa è la 
                                                                                       #luminosità e maggiore dovrà essere l'intensità luminosa emessa dai led

        duty_value = int(1023 * actual_external_lum_converted / (PHOTO_RESISTOR_MAX_VALUE - PHOTO_RESISTOR_MIN_VALUE)) #Converte il valore di luminosità ottenuto dalla conversione
                                                                                                                       # in un valore di duty in un range che va da (1023, 0)

        #Setta il valore del duty dei due led al valore del duty appena calcolato
        #il valore di duty grazie all'operazione di conversione della luminosità esterna
        #sarà più alto per valori di intensità luminosa esterna bassi e viceversa
        led1.duty(duty_value)
        led2.duty(duty_value)

        #Stampa sul display oled le informazioni di stato aggiornate indicando la percentuale di luminosità
        #aggiornata dei led
        oled.fill_rect(90, 40, 60, 10, OLED_FILL)
        oled.print_line_no_fill(str(int(actual_external_lum_converted)) + "%", 90, 40, OLED_COLOR)

        MQTT_PUBLISH_VALUE[MQTT_LED_STATE] = ujson.dumps({"light" : 1}) #Aggiorna il dizionario che contiene i valori aggiornati da pubblicare 
                                                                        #in particolare aggiorna il valore da pubblicare sul topic in cui viene pubblicato
                                                                        #lo stato dei led (MQTT_LED_STATE), il valore aggiornato è rappresentato con una 
                                                                        #stringa in formato JSON
        try:
            #Prova a pubblicare il nuovo valore che rappresenta lo stato dei led sul topic MQTT_LED_STATE
            #andando ad aggiornare le info di stato sul display oled
            client.publish(MQTT_LED_STATE, MQTT_PUBLISH_VALUE[MQTT_LED_STATE])
            oled.fill_rect(55, 10, 80, 10, OLED_FILL)
            oled.print_line_no_fill("Published", 55, 10, OLED_COLOR)
        except OSError as e:
            print("Error during the sensors data pubblication: ", e)
            oled.fill_rect(55, 10, 80, 10, OLED_FILL)
            oled.print_line_no_fill("Error", 55, 10, OLED_COLOR)
       
    else:
        #Se il valore di luminosita rilevato non è minore del valore di soglia le luci possono rimanere
        #spente, dunque assegna 0 come valore di duty dei led
        led1.duty(0)
        led2.duty(0)
        
        #Stampa sul display oled le informazioni di stato aggiornate indicando la percentuale di luminosità
        #aggiornata dei led
        oled.fill_rect(90, 40, 60, 10, OLED_FILL)
        oled.print_line_no_fill("0%", 90, 40, OLED_COLOR)

        MQTT_PUBLISH_VALUE[MQTT_LED_STATE] = ujson.dumps({"light" : 0}) #Aggiorna il dizionario che contiene i valori aggiornati da pubblicare 
                                                                        #in particolare aggiorna il valore da pubblicare sul topic in cui viene pubblicato
                                                                        #lo stato dei led (MQTT_LED_STATE), il valore aggiornato è rappresentato con una 
                                                                        #stringa in formato JSON
        try:
            #Prova a pubblicare il nuovo valore che rappresenta lo stato dei led sul topic MQTT_LED_STATE
            #andando ad aggiornare le info di stato sul display oled
            client.publish(MQTT_LED_STATE, MQTT_PUBLISH_VALUE[MQTT_LED_STATE])
            oled.fill_rect(55, 10, 80, 10, OLED_FILL)
            oled.print_line_no_fill("Published", 55, 10, OLED_COLOR)
        except OSError as e:
            print("Error during the sensors data pubblication: ", e)
            oled.fill_rect(55, 10, 80, 10, OLED_FILL)
            oled.print_line_no_fill("Error", 55, 10, OLED_COLOR)

#Questa funzione implementa la logica per effettuare il ciclo di lettura dei valori dai sensori      
def read_sensor_value():

    global SENSORS_ACTUAL_VALUE, MQTT_ENVIRONMENT_TEMP, MQTT_ENVIRONMENT_HUMIDITY, MQTT_OUTSIDE_LUX
    global MQTT_CISTERN_LEVEL, MQTT_GROUND_HUMIDITY
    global OLED_COLOR, OLED_FILL
    global oled, environment_sensor, photo_resistor, cistern, ground_sensor

    print("Reading sensors values...")
    #Stampa sul display oled lo stato del sistema indicando che è in corso il ciclo di lettura dei valori dai sensori
    oled.fill_rect(70, 0, 60, 10, OLED_FILL)
    oled.print_line_no_fill("Reading", 65, 1, OLED_COLOR)

    environment_sensor.measure() #Richiede una misurazione al sensore DHT22 tramite un metodo della classe ENVIRONMENT_SENSOR

    #Fase di aggiornamento dei valori contenuti nel dizionario SENSOR_ACTUAL_VALUE 
    #sulla base dei nuovi valori letti dai sensori, le letture vengono effettuate tramite metodi
    #implementati nelle classi che realizzano un astrazione di alto livello di ogni sensore utilizzato
    #questi metodi restituiscono i valori di lettura tramite una stringa in formato JSON
    SENSORS_ACTUAL_VALUE[MQTT_ENVIRONMENT_TEMP] = environment_sensor.get_ujson_temp() #Recupera il valore della temperatura dell'ambiente dal sensore DHT22
    SENSORS_ACTUAL_VALUE[MQTT_OUTSIDE_LUX] = photo_resistor.get_ujson_value() #Recupera il valore dell'intensità luminosa dal foto resistore
                                                                              #il valore restituito dal metodo sarà compreso in un range (PHOTO_RESISTOR_MIN_VALUE, PHOTO_RESISTOR_MAX_VALUE)
    SENSORS_ACTUAL_VALUE[MQTT_CISTERN_LEVEL] = cistern.get_ujson_level() #Recupera il valore che indica lo stato di riempimento del serbatoio in percentuale 
    SENSORS_ACTUAL_VALUE[MQTT_GROUND_HUMIDITY] = ground_sensor.get_ujson_value() #Recupera il valore dell'umidità del terreno dal sensore di umidità del terreno 
                                                                                 #il valore restituito dal metodo sarà compreso in un range (GROUND_SENSOR_MIN_VALUE, GROUND_SENSOR_MAX_VALUE)
    SENSORS_ACTUAL_VALUE[MQTT_ENVIRONMENT_HUMIDITY] = environment_sensor.get_ujson_humidity() #Recupera il valore dell'umidità dell'ambiente dal sensore DHT22

    #Stampa sul display oled lo stato del sistema indicando che il ciclo di lettura dei valori dai sensori è terminato 
    oled.fill_rect(70, 0, 60, 10, OLED_FILL)
    oled.print_line_no_fill("Read", 65, 1, OLED_COLOR)

#Questa funzione implementa la logica per controllare il sistema sulla base del livello del liquido 
#all'interno del serbatoio, l'obbiettivo di questa funzione è forzare il blocco della pompa di irrigazione
#se il livello del liquido all'interno della cisterna è più basso di un livello di soglia predefinito 
#all'interno dei parametri di sistema
def check_cistern():

    global SENSORS_ACTUAL_VALUE, SYSTEM_PARAMS, MQTT_PUMP_STATE, MQTT_CISTERN_LEVEL
    global OLED_COLOR, OLED_FILL
    global oled, pump, cistern
    
    if cistern.get_last_level() < SYSTEM_PARAMS["CRITICAL_CISTERN_LEVEL"]: #Controlla se il livello del liquido all'interno della cisterna 
                                                                         #è più basso del livello critico 
        print("Livello di cisterna critico, ricarica il serbatoio per proseguire l'irrigazione")
        pump.stop_pump() #Se il livello di liquido nella cisterna è critico forza lo stop della pompa
                         #lo stop della pompa viene effettuato tramite un metodo della classe PUMP sull'oggetto pump 
                         #che fornisce un astrazione di alto livello della pompa
        
        #Stampa sul display oled le informazioni di stato aggiornate indicando che lo stato della pompa è OFF
        #e lo stato della cisterna è CRITIC
        if SYSTEM_PARAMS["MANUAL_IRRIGATION_CONTROL"] == False:
            oled.fill_rect(40, 30, 30, 10, OLED_FILL)
            oled.print_line_no_fill("AUT=>", 40, 30, OLED_COLOR)

        oled.fill_rect(80, 30, 30, 10, OLED_FILL)
        oled.print_line_no_fill("OFF", 80, 30, OLED_COLOR)

        oled.fill_rect(70, 50, 60, 10, OLED_FILL)
        oled.print_line_no_fill("Critic!!", 70, 50, OLED_COLOR)

        SYSTEM_PARAMS["BLOCK_IRRIGATION_FOR_CRITICAL_CISTERN_LEVEL"] = True #Setta il paramentro di sistema "BLOCK_IRRIGATION_FOR_CRITICAL_CISTERN_LEVEL"
                                                                            #a True, questo consentirà al sistema di bloccare qualsiasi tipo di tentativo di 
                                                                            #attivazione della pompa sia tramite controllo manuale (dashboard) che tramite 
                                                                            #le procedure di controllo automatico
        
        MQTT_PUBLISH_VALUE[MQTT_PUMP_STATE] = ujson.dumps({"pump": 0}) #Aggiorna il dizionario che contiene i valori aggiornati da pubblicare 
                                                                       #in particolare aggiorna il valore da pubblicare sul topic in cui viene pubblicato
                                                                       #lo stato della pompa (MQTT_PUMP_STATE), il valore aggiornato è rappresentato con una 
                                                                       #stringa in formato JSON
        try:    
            #Prova a pubblicare il nuovo valore che rappresenta lo stato della pompa sul topic MQTT_PUMP_STATE
            #andando ad aggiornare le info di stato sul display oled
            client.publish(MQTT_PUMP_STATE, MQTT_PUBLISH_VALUE[MQTT_PUMP_STATE])
            oled.fill_rect(55, 10, 80, 10, OLED_FILL)
            oled.print_line_no_fill("Published", 55, 10, OLED_COLOR)
        except OSError as e:
            print("Error during the pubblication of the new pump state: ", e)
            oled.fill_rect(55, 10, 80, 10, OLED_FILL)
            oled.print_line_no_fill("Error", 55, 10, OLED_COLOR)

    
    elif cistern.get_last_level() > SYSTEM_PARAMS["CRITICAL_CISTERN_LEVEL"] and SYSTEM_PARAMS["BLOCK_IRRIGATION_FOR_CRITICAL_CISTERN_LEVEL"]:
        #Se il livello della cisterna è superiore al livello critico e il sistema di irrigazione risulta bloccato perchè
        #il paramentro di sistema "BLOCK_IRRIGATION_FOR_CRITICAL_CISTERN_LEVEL" è impostato a True la procedura rileva che il livello della 
        #cisterna è ritornato ad un livello che non è critico dunque vengono effettuate le procedure per ripristinare il funzionamento del sistema
        #di irrigazione 
        print("Sistema di irrigazione ripristinato")
        SYSTEM_PARAMS["BLOCK_IRRIGATION_FOR_CRITICAL_CISTERN_LEVEL"] = False #Setta il paramentro di sistema "BLOCK_IRRIGATION_FOR_CRITICAL_CISTERN_LEVEL"
                                                                             #a False, questo consentirà al sistema di sbloccare il blocco di attivazione della pompa  
        
        #Stampa sul display oled le informazioni di stato aggiornate indicando che
        #lo stato della cisterna è FILLED
        oled.fill_rect(70, 50, 60, 10, OLED_FILL)
        oled.print_line_no_fill("Filled!!", 70, 50, OLED_COLOR)

        if SYSTEM_PARAMS["MANUAL_IRRIGATION_PUMP"] == True: #Verifica se il controllo manuale della pompa è attivo
            
            print("Starting pump...", end="")
            pump.start_pump() #Se il controllo manuale della pompa è attivo la pompa viene attivata

            #Stampa sul display oled le informazioni di stato aggiornate indicando che
            #lo stato della pompa è ON
            oled.fill_rect(80, 30, 30, 10, OLED_FILL)
            oled.print_line_no_fill("ON", 80, 30, OLED_COLOR)

            MQTT_PUBLISH_VALUE[MQTT_PUMP_STATE] = ujson.dumps({"pump": 1}) #Aggiorna il dizionario che contiene i valori aggiornati da pubblicare 
                                                                           #in particolare aggiorna il valore da pubblicare sul topic in cui viene pubblicato
                                                                           #lo stato della pompa (MQTT_PUMP_STATE), il valore aggiornato è rappresentato con una 
                                                                           #stringa in formato JSON
            try:
                #Prova a pubblicare il nuovo valore che rappresenta lo stato della pompa sul topic MQTT_PUMP_STATE
                #andando anche ad aggiornare le info di stato sul display oled
                client.publish(MQTT_PUMP_STATE, MQTT_PUBLISH_VALUE[MQTT_PUMP_STATE])
                oled.fill_rect(55, 10, 80, 10, OLED_FILL)
                oled.print_line_no_fill("Published", 55, 10, OLED_COLOR)
            except OSError as e:
                print("Error during the pubblication of the new pump state: ", e)
                ooled.fill_rect(55, 10, 80, 10, OLED_FILL)
                oled.print_line_no_fill("Error", 55, 10, OLED_COLOR)
    
    else:
        #Se il livello della cisterna è superiore al livello critico e il sistema di irrigazione  non risulta bloccato perchè
        #il paramentro di sistema "BLOCK_IRRIGATION_FOR_CRITICAL_CISTERN_LEVEL" è impostato a False la procedura rileva che il livello della 
        #cisterna è superiore al livello critico ed il sistema di irrigazione è regolarmente abilitato, la procedura si limita a 
        #stampare sul display oled le informazioni riguardanti il livello di riempimento del serbatoio in percentuale
        oled.fill_rect(70, 50, 60, 10, OLED_FILL)
        oled.print_line_no_fill(str(int(cistern.get_last_level())) + "%", 70, 50, OLED_COLOR)

#Questa funzione viene richiamata dopo che tramite la dashboard
#è stato preso il controllo manuale del sistema di irrigazione,
#la procedura implementa la logica necessaria a preparare il sistema
#di irrigazione al controllo manuale
def manual_irrigation_control():
    global MQTT_PUBLISH_VALUE, MQTT_PUMP_STATE
    global OLED_COLOR, OLED_FILL
    global oled, pump, client

    #Stampa sul display oled le informazioni di stato aggiornate indicando che il controllo dell'irrigazione è
    #passato in modalità MANUALE e che la pompa è disattivata dato quest'ultima potrebbe trovarsi nello stato attivo
    #a seguito di comandi ricevuti dalle procedure di controllo automatico
    oled.fill_rect(40, 30, 30, 10, OLED_FILL)
    oled.print_line_no_fill("MAN=>", 40, 30, OLED_COLOR) 

    pump.stop_pump() #Disattiva la pompa tramite un metodo della classe PUMP sull'oggetto pump 
                     #che fornisce un astrazione di alto livello della pompa

    oled.fill_rect(80, 30, 30, 10, OLED_FILL)
    oled.print_line_no_fill("OFF", 80, 30, OLED_COLOR)

    MQTT_PUBLISH_VALUE[MQTT_PUMP_STATE] = ujson.dumps({"pump": 0}) #Aggiorna il dizionario che contiene i valori aggiornati da pubblicare 
                                                                   #in particolare aggiorna il valore da pubblicare sul topic in cui viene pubblicato
                                                                   #lo stato della pompa (MQTT_PUMP_STATE), il valore aggiornato è rappresentato con una 
                                                                   #stringa in formato JSON
    try:
        #Prova a pubblicare il nuovo valore che rappresenta lo stato della pompa sul topic MQTT_PUMP_STATE
        #andando anche ad aggiornare le info di stato sul display oled
        client.publish(MQTT_PUMP_STATE, MQTT_PUBLISH_VALUE[MQTT_PUMP_STATE])
        oled.fill_rect(55, 10, 80, 10, OLED_FILL)
        oled.print_line_no_fill("Published", 55, 10, OLED_COLOR)
    except OSError as e:
        print("Error during the sensors data pubblication: ", e)
        oled.fill_rect(55, 10, 80, 10, OLED_FILL)
        oled.print_line_no_fill("Error", 55, 10, OLED_COLOR)

#Questa funzione viene richiamata dopo che tramite la dashboard
#è stato preso il controllo manuale del sistema di ventilazione,
#la procedura implementa la logica necessaria a preparare il sistema
#di ventilazione al controllo manuale
def manual_fan_control():

    global MQTT_PUBLISH_VALUE, MQTT_FAN_STATE
    global OLED_COLOR, OLED_FILL
    global oled, fan, client

    #Stampa sul display oled le informazioni di stato aggiornate indicando che il controllo della ventilazione è
    #passato in modalità MANUALE e che la ventola è stata disattivata dato quest'ultima potrebbe trovarsi nello stato attivo
    #a seguito di comandi ricevuti dalle procedure di controllo automatico
    oled.fill_rect(35, 20, 30, 10, OLED_FILL)
    oled.print_line_no_fill("MAN=>", 35, 20, OLED_COLOR)

    fan.stop_fan() #Disattiva la ventola tramite un metodo della classe FAN sull'oggetto fan
                   #che fornisce un astrazione di alto livello della ventola

    oled.fill_rect(80, 20, 60, 10, OLED_FILL)
    oled.print_line_no_fill("OFF", 80, 20, OLED_COLOR)

    MQTT_PUBLISH_VALUE[MQTT_FAN_STATE] = ujson.dumps({"fan" : 0 }) #Aggiorna il dizionario che contiene i valori aggiornati da pubblicare 
                                                                   #in particolare aggiorna il valore da pubblicare sul topic in cui viene pubblicato
                                                                   #lo stato della ventola (MQTT_FAN_STATE), il valore aggiornato è rappresentato con una 
                                                                   #stringa in formato JSON
    try:
        #Prova a pubblicare il nuovo valore che rappresenta lo stato della ventola sul topic MQTT_FAN_STATE
        #andando anche ad aggiornare le info di stato sul display oled
        client.publish(MQTT_FAN_STATE, MQTT_PUBLISH_VALUE[MQTT_FAN_STATE])
        oled.fill_rect(55, 10, 80, 10, OLED_FILL)
        oled.print_line_no_fill("Published", 55, 10, OLED_COLOR)
    except OSError as e:
        print("Error during the sensors data pubblication: ", e)
        oled.fill_rect(55, 10, 80, 10, OLED_FILL)
        oled.print_line_no_fill("Error", 55, 10, OLED_COLOR)

#Questa funzione viene richiamata dopo che tramite la dashboard
#è stata attivata manualmente la ventola, la procedura implementa
#la logica necessaria ad effettuare l'attivazione manuale della ventola 
def manual_fan_on():

    global SYSTEM_PARAMS, MQTT_PUBLISH_VALUE, DASH_MAX_VAL, MQTT_FAN_STATE
    global OLED_COLOR, OLED_FILL
    global fan, oled, client

    fan.start_fan() #Attiva la ventola tramite un metodo della classe FAN sull'oggetto fan
                    #che fornisce un astrazione di alto livello della ventola

    #Stampa sul display oled le informazioni di stato aggiornate indicando che la ventola
    #è attiva
    oled.fill_rect(80, 20, 60, 10, OLED_FILL)
    oled.print_line_no_fill("ON", 80, 20, OLED_COLOR)

    MQTT_PUBLISH_VALUE[MQTT_FAN_STATE] = ujson.dumps({"fan" : 1}) #Aggiorna il dizionario che contiene i valori aggiornati da pubblicare 
                                                                  #in particolare aggiorna il valore da pubblicare sul topic in cui viene pubblicato
                                                                  #lo stato della ventola (MQTT_FAN_STATE), il valore aggiornato è rappresentato con una 
                                                                  #stringa in formato JSON
    try:
        #Prova a pubblicare il nuovo valore che rappresenta lo stato della ventola sul topic MQTT_FAN_STATE
        #andando anche ad aggiornare le info di stato sul display oled
        client.publish(MQTT_FAN_STATE, MQTT_PUBLISH_VALUE[MQTT_FAN_STATE])
        oled.fill_rect(55, 10, 80, 10, OLED_FILL)
        oled.print_line_no_fill("Published", 55, 10, OLED_COLOR)
    except OSError as e:
        print("Error during the sensors data pubblication: ", e)
        oled.fill_rect(55, 10, 80, 10, OLED_FILL)
        oled.print_line_no_fill("Error", 55, 10, OLED_COLOR)

#Questa funzione viene richiamata dopo che tramite la dashboard
#è stata disattivata manualmente la ventola, la procedura implementa
#la logica necessaria ad effettuare l'attivazione manuale della ventola 
def manual_fan_off():
    global SYSTEM_PARAMS, MQTT_PUBLISH_VALUE, DASH_MAX_VAL, MQTT_FAN_STATE
    global OLED_COLOR, OLED_FILL
    global fan, oled, client

    fan.stop_fan() #Disattiva la ventola tramite un metodo della classe FAN sull'oggetto fan
                   #che fornisce un astrazione di alto livello della ventola

    #Stampa sul display oled le informazioni di stato aggiornate indicando che la ventola
    #non è attiva
    oled.fill_rect(80, 20, 60, 10, OLED_FILL)
    oled.print_line_no_fill("OFF", 80, 20, OLED_COLOR)

    MQTT_PUBLISH_VALUE[MQTT_FAN_STATE] = ujson.dumps({"fan" : 0}) #Aggiorna il dizionario che contiene i valori aggiornati da pubblicare 
                                                                  #in particolare aggiorna il valore da pubblicare sul topic in cui viene pubblicato
                                                                  #lo stato della ventola (MQTT_FAN_STATE), il valore aggiornato è rappresentato con una 
                                                                  #stringa in formato JSON
    try:
        #Prova a pubblicare il nuovo valore che rappresenta lo stato della ventola sul topic MQTT_FAN_STATE
        #andando anche ad aggiornare le info di stato sul display oled
        client.publish(MQTT_FAN_STATE, MQTT_PUBLISH_VALUE[MQTT_FAN_STATE])
        oled.fill_rect(55, 10, 80, 10, OLED_FILL)
        oled.print_line_no_fill("Published", 55, 10, OLED_COLOR)
    except OSError as e:
        print("Error during the sensors data pubblication: ", e)
        oled.fill_rect(55, 10, 80, 10, OLED_FILL)
        oled.print_line_no_fill("Error", 55, 10, OLED_COLOR)

#Questa funzione viene richiamata dopo che tramite la dashboard
#è stata attivata manualmente la pompa, la procedura implementa
#la logica necessaria ad effettuare l'attivazione manuale della pompa
def manual_irrigation_pump_on():

    global SYSTEM_PARAMS, MQTT_PUBLISH_VALUE, MQTT_PUMP_STATE, MQTT_CISTERN_LEVEL
    global OLED_COLOR, OLED_FILL
    global oled, client, pump 

    if SYSTEM_PARAMS["BLOCK_IRRIGATION_FOR_CRITICAL_CISTERN_LEVEL"] == False: #Verifica che il livello dell'acqua nella cisterna non è critico
        #Se il livello di acqua nel serbatoio non è critico la pompa può essere attivata
        print("Starting pump...", end="")
        pump.start_pump() #Attiva la pompa tramite un metodo della classe PUMP sull'oggetto pump
                          #che fornisce un astrazione di alto livello della pompa

        #Stampa sul display oled le informazioni di stato aggiornate indicando che la pompa
        #è attiva
        oled.fill_rect(80, 30, 30, 10, OLED_FILL)
        oled.print_line_no_fill("ON", 80, 30, OLED_COLOR)

        MQTT_PUBLISH_VALUE[MQTT_PUMP_STATE] = ujson.dumps({"pump": 1}) #Aggiorna il dizionario che contiene i valori aggiornati da pubblicare 
                                                                       #in particolare aggiorna il valore da pubblicare sul topic in cui viene pubblicato
                                                                       #lo stato della pompa (MQTT_PUMP_STATE), il valore aggiornato è rappresentato con una 
                                                                       #stringa in formato JSON
        try:
            #Prova a pubblicare il nuovo valore che rappresenta lo stato della pompa sul topic MQTT_PUMP_STATE
            #andando anche ad aggiornare le info di stato sul display oled
            client.publish(MQTT_PUMP_STATE, MQTT_PUBLISH_VALUE[MQTT_PUMP_STATE])
            oled.fill_rect(55, 10, 80, 10, OLED_FILL)
            oled.print_line_no_fill("Published", 55, 10, OLED_COLOR)
        except OSError as e:
            print("Error during the sensors data pubblication: ", e)
            oled.fill_rect(55, 10, 80, 10, OLED_FILL)
            oled.print_line_no_fill("Error", 55, 10, OLED_COLOR)
    else:
        #Se il livello di acqua nel serbatoio è critico la pompa non può essere attivata
        print("Livello di cisterna critico, ricarica il serbatoio per proseguire l'irrigazione")
        pump.stop_pump() #Disattiva la pompa tramite un metodo della classe PUMP sull'oggetto pump
                         #che fornisce un astrazione di alto livello della pompa

        #Stampa sul display oled le informazioni di stato aggiornate indicando che la pompa
        #non è attiva
        oled.fill_rect(80, 30, 30, 10, OLED_FILL)
        oled.print_line_no_fill("OFF", 80, 30, OLED_COLOR)

        MQTT_PUBLISH_VALUE[MQTT_PUMP_STATE] = ujson.dumps({"pump": 0}) #Aggiorna il dizionario che contiene i valori aggiornati da pubblicare 
                                                                       #in particolare aggiorna il valore da pubblicare sul topic in cui viene pubblicato
                                                                       #lo stato della pompa (MQTT_PUMP_STATE), il valore aggiornato è rappresentato con una 
                                                                       #stringa in formato JSON
        try:
            #Prova a pubblicare il nuovo valore che rappresenta lo stato della pompa sul topic MQTT_PUMP_STATE
            #andando anche ad aggiornare le info di stato sul display oled
            client.publish(MQTT_PUMP_STATE, MQTT_PUBLISH_VALUE[MQTT_PUMP_STATE])
            oled.fill_rect(55, 10, 80, 10, OLED_FILL)
            oled.print_line_no_fill("Published", 55, 10, OLED_COLOR)
        except OSError as e:
            print("Error during the sensors data pubblication: ", e)
            oled.fill_rect(55, 10, 80, 10, OLED_FILL)
            oled.print_line_no_fill("Error", 55, 10, OLED_COLOR)

#Questa funzione viene richiamata dopo che tramite la dashboard
#è stata disattivata manualmente la pompa, la procedura implementa
#la logica necessaria ad effettuare la disattivazione manuale della pompa
def manual_irrigation_pump_off():

    global MQTT_PUBLISH_VALUE, MQTT_PUMP_STATE
    global OLED_COLOR, OLED_FILL
    global oled, client, pump

    pump.stop_pump() #Disattiva la pompa tramite un metodo della classe PUMP sull'oggetto pump
                     #che fornisce un astrazione di alto livello della pompa

    #Stampa sul display oled le informazioni di stato aggiornate indicando che la pompa
    #non è attiva
    oled.fill_rect(80, 30, 30, 10, OLED_FILL)
    oled.print_line_no_fill("OFF", 80, 30, OLED_COLOR)

    MQTT_PUBLISH_VALUE[MQTT_PUMP_STATE] = ujson.dumps({"pump": 0}) #Aggiorna il dizionario che contiene i valori aggiornati da pubblicare 
                                                                   #in particolare aggiorna il valore da pubblicare sul topic in cui viene pubblicato
                                                                   #lo stato della pompa (MQTT_PUMP_STATE), il valore aggiornato è rappresentato con una 
                                                                   #stringa in formato JSON
    try:
        #Prova a pubblicare il nuovo valore che rappresenta lo stato della pompa sul topic MQTT_PUMP_STATE
        #andando anche ad aggiornare le info di stato sul display oled
        client.publish(MQTT_PUMP_STATE, MQTT_PUBLISH_VALUE[MQTT_PUMP_STATE])
        oled.fill_rect(55, 10, 80, 10, OLED_FILL)
        oled.print_line_no_fill("Published", 55, 10, OLED_COLOR)
    except OSError as e:
        print("Error during the sensors data pubblication: ", e)
        oled.fill_rect(55, 10, 80, 10, OLED_FILL)
        oled.print_line_no_fill("Error", 55, 10, OLED_COLOR)

#Questa funzione è richiamata nel caso in cui dalla dashboard è stato richiesto il controllo 
#manuale dell'illuminazione dei led 
#la procedura implementa la logica necessaria a preparare il sistema
#di illuminazione al controllo manuale
def manual_light_control():

    global MQTT_PUBLISH_VALUE, MQTT_LED_STATE, SYSTEM_PARAMS
    global OLED_COLOR, OLED_FILL
    global client, led

    #Setta il valore del duty dei led a 0, in modo tale da spegnerli nel caso in cui fossero accesi a seguito
    #delle operazioni eseguite dalle procedure di controllo automatico della luminosità dei led
    led1.duty(0)
    led2.duty(0)

    #Stampa sul display oled le informazioni di stato aggiornate indicando che il controllo dei led è
    #passato in modalità MANUALE
    oled.fill_rect(49, 40, 41, 10, OLED_FILL)
    oled.print_line_no_fill("MAN=>", 49, 40, OLED_COLOR)

    SYSTEM_PARAMS["MANUAL_LIGHTS_LEVEL"] = 0 #Resetta il valore del paramentro di sistema "MANUAL_LIGHTS_LEVEL", che 
                                             #potrebbe essere rimasto impostato a valori diversi dal valore di default
                                             #dopo una precedente richiesta di controllo manuale della luminosità 
                                             #questo valore verrà successivamente impostato dalla funzione subCallBack sulla base
                                             #del valore di intensità luminosa che verrà richiesto dalla dashboard

    #Stampa sul display oled le informazioni di stato aggiornate indicando la percentuale di luminosità
    #aggiornata dei led
    oled.fill_rect(90, 40, 60, 10, OLED_FILL)
    oled.print_line_no_fill(str(SYSTEM_PARAMS["MANUAL_LIGHTS_LEVEL"]) + "%", 90, 40, OLED_COLOR)

    MQTT_PUBLISH_VALUE[MQTT_LED_STATE] = ujson.dumps({"light" : 0 }) #Aggiorna il dizionario che contiene i valori aggiornati da pubblicare 
                                                                     #in particolare aggiorna il valore da pubblicare sul topic in cui viene pubblicato
                                                                     #lo stato dei led (MQTT_LED_STATE), il valore aggiornato è rappresentato con una 
                                                                     #stringa in formato JSON
    try:
        #Prova a pubblicare il nuovo valore che rappresenta lo stato dei led sul topic MQTT_LED_STATE
        #andando ad aggiornare le info di stato sul display oled
        client.publish(MQTT_LED_STATE, MQTT_PUBLISH_VALUE[MQTT_LED_STATE])
        oled.fill_rect(55, 10, 80, 10, OLED_FILL)
        oled.print_line_no_fill("Published", 55, 10, OLED_COLOR)
    except OSError as e:
        print("Error during the sensors data pubblication: ", e)
        oled.fill_rect(55, 10, 80, 10, OLED_FILL)
        oled.print_line_no_fill("Error", 55, 10, OLED_COLOR)

#Questa funzione implementa la logica per gestire il controllo manuale della lumiosità dei led 
#la procedura è richiamata nel caso in cui dalla dashboard è stato richiesto di impostare
#la luminosità dei led ad una certa percentuale
def manual_light_level():

    global SYSTEM_PARAMS, DASH_MAX_VAL, DASH_MIN_VAL, MQTT_LED_STATE, MQTT_PUBLISH_VALUE
    global OLED_COLOR, OLED_FILL
    global led, client

    duty_value = 1023 * SYSTEM_PARAMS["MANUAL_LIGHTS_LEVEL"] / (DASH_MAX_VAL - DASH_MIN_VAL) #Il parametro di sistema "MANUAL_LIGHT_LEVEL" contiene il valore 
                                                                                             #del livello di luminosità richiesto dalla dashboard, questo paramentro è 
                                                                                             #aggiornato nella subCallBack quando il sistema verificando i messaggi dal broker
                                                                                             #rileva un messaggio sul topic "MQTT_LIGHTS_MANUALLED", questo messaggio conterrà 
                                                                                             #il livello di luminosità dei led richiesto dalla dashboard, il valore ricevuto sarà
                                                                                             #contenuto nel range (DASH_MAX_VAL, DASH_MIN_VAL), la procedura converte questo valore in 
                                                                                             #un valore compreso da (0, 1023) che corrisponderà al valore del duty che verrà assegnato ai due
                                                                                             #led pilotati in PWM
    #Il valore del duty calcolato viene assegnato ai led
    led1.duty(int(duty_value))
    led2.duty(int(duty_value))

    #Stampa sul display oled le informazioni di stato aggiornate indicando la percentuale di luminosità
    #aggiornata dei led
    oled.fill_rect(90, 40, 60, 10, OLED_FILL)
    oled.print_line_no_fill(str(SYSTEM_PARAMS["MANUAL_LIGHTS_LEVEL"]) + "%", 90, 40, OLED_COLOR)

    MQTT_PUBLISH_VALUE[MQTT_LED_STATE] = ujson.dumps({"light" : 1}) #Aggiorna il dizionario che contiene i valori aggiornati da pubblicare 
                                                                    #in particolare aggiorna il valore da pubblicare sul topic in cui viene pubblicato
                                                                    #lo stato dei led (MQTT_LED_STATE), il valore aggiornato è rappresentato con una 
                                                                    #stringa in formato JSON
    try:
        #Prova a pubblicare il nuovo valore che rappresenta lo stato dei led sul topic MQTT_LED_STATE
        #andando ad aggiornare le info di stato sul display oled
        client.publish(MQTT_LED_STATE, MQTT_PUBLISH_VALUE[MQTT_LED_STATE])
        oled.fill_rect(55, 10, 80, 10, OLED_FILL)
        oled.print_line_no_fill("Published", 55, 10, OLED_COLOR)
    except OSError as e:
        print("Error during the sensors data pubblication: ", e)
        oled.fill_rect(55, 10, 80, 10, OLED_FILL)
        oled.print_line_no_fill("Error", 55, 10, OLED_COLOR)

#Questa funzione che verrà richiamata ogni volta che sul client (oggetto della classe MQTT che gestisce la comunicazione del sistema con il broker)
#verrà richiamato il metodo check_msg(), la procedura verifica se sui topic a cui client si è sottoscritto sono stati accodati nuovi messaggi
#che corrispondono a messaggi in arrivo dalla dashboard, sulla base dei messaggi ricevuti la funzione andrà poi successivamente a modificare alcuni paramentri di 
#sistema e richiamare delle procedure specifiche per il controllo manuale degli attuatori
def subCallback(topic, msg):

    global SYSTEM_PARAMS, MQTT_SUBSCRIBE_TOPIC
    global oled
    
    print(topic, msg)
    if topic == MQTT_SUBSCRIBE_TOPIC["MQTT_RESET_SYSTEM"]: #Verifica se è stato ricevuto un messaggio sul topic "MQTT_RESET_SYSTEM"
        #Se è presente un messaggio in coda sul topic verifica il contenuto del messaggio
        if msg == b'true': 
            SYSTEM_PARAMS["RESTART_SYSTEM"] = True #Se il messaggio è 'true' la dashboard ha richiesto il riavvio da remoto del sistema
                                                   #il prarametro di sistema "RESTART_SYSTEM" viene impostato a True, questo comporterà il riavvio del sistema
        elif msg == b'false':
            SYSTEM_PARAMS["RESTART_SYSTEM"] = False #Se il messaggio è 'false' la dashboard non ha richiesto il riavvio da remoto del sistema
                                                    #il prarametro di sistema "RESTART_SYSTEM" viene impostato a False, questo non comporterà il riavvio del sistema

    if topic == MQTT_SUBSCRIBE_TOPIC["MQTT_IRRIGATION_MANUALCONTROL"]: #Verifica se è stato ricevuto un messaggio sul topic "MQTT_IRRIGATION_MANUALCONTROL"
        #Se è presente un messaggio in coda sul topic verifica il contenuto del messaggio
        if msg == b'true':
            SYSTEM_PARAMS["MANUAL_IRRIGATION_CONTROL"] = True #Se il messaggio è 'true' la dashboard ha richiesto controllo manuale dell'irrigazione
                                                              #il prarametro di sistema "MANUAL_IRRIGATION_CONTROL" viene impostato a True, questo comporterà il blocco delle procedure
                                                              #di irrigazione automatica
            manual_irrigation_control() #Richiama la procedura che consente di prendere il controllo manuale del sistema di irrigazione
        elif msg == b'false':
            #Stampa sul display oled le informazioni di stato aggiornate indicando che il controllo dell'irrigazione è
            #passato in modalità AUTOMATICA
            oled.fill_rect(40, 30, 30, 10, OLED_FILL)
            oled.print_line_no_fill("AUT=>", 40, 30, OLED_COLOR)
            SYSTEM_PARAMS["MANUAL_IRRIGATION_CONTROL"] = False #Se il messaggio è 'false' la dashboard ha rilasciato controllo manuale dell'irrigazione
                                                               #il prarametro di sistema "MANUAL_IRRIGATION_CONTROL" viene impostato a False, questo comporterà la riattivazione delle procedure
                                                               #di irrigazione automatica
    
    if topic == MQTT_SUBSCRIBE_TOPIC["MQTT_IRRIGATION_MANUALPUMP"]: #Verifica se è stato ricevuto un messaggio sul topic "MQTT_IRRIGATION_MANUALPUMP"
        #Se è presente un messaggio in coda sul topic verifica il contenuto del messaggio
        if msg == b'true':
            SYSTEM_PARAMS["MANUAL_IRRIGATION_PUMP"] = True #Se il messaggio è 'true' la dashboard ha richiesto l'accensione manuale della pompa
                                                           #dopo aver preso il controllo del sistema di irrigazione, il prarametro di sistema
                                                           #"MANUAL_IRRIGATION_PUMP" viene impostato a True andando ad indicare alle
                                                           #altre procedure di controllo dell'irrigazione che la pompa è attiva per via di un comando arrivato dalla
                                                           #dashboard
            manual_irrigation_pump_on() #Viene richiamata la procedura di attivazione manuale della pompa
        elif msg == b'false':
            SYSTEM_PARAMS["MANUAL_IRRIGATION_PUMP"] = False #Se il messaggio è 'false' la dashboard ha richiesto lo spegnimento manuale della pompa
                                                            #il prarametro di sistema "MANUAL_IRRIGATION_PUMP" viene impostato a False andando ad indicare alle
                                                            #altre procedure di controllo dell'irrigazione che la pompa è disattivata per via di un comando arrivato dalla
                                                            #dashboard
            manual_irrigation_pump_off() #Viene richiamata la procedura di disattivazione manuale della pompa
    
    if topic == MQTT_SUBSCRIBE_TOPIC["MQTT_IRRIGATION_HUMIDITY"]: #Verifica se è stato ricevuto un messaggio sul topic "MQTT_IRRIGATION_HUMIDITY"
        #Se è presente un messaggio in coda su questo topic significa che l'utente ha impostato dalla dashboard una nuova soglia critica 
        #di umidità del terreno sulla base del quale deve essere effettuata l'irrigazione
        SYSTEM_PARAMS["HUMIDITY_CRITICAL_LEVEL"] = int(msg) #il paramentro di sistema "HUMIDITY_CRITICAL_LEVEL" viene impostato al valore 
                                                            #contenuto nel messaggio arrivato dalla dashboard, la procedura si assicura di convertire
                                                            #il valore in intero, sulla base di questo paramentro la procedura di irrigazione automatica
                                                            #deciderà in quali condizioni di umidità del terreno dovrà essere attivata la pompa

    if topic == MQTT_SUBSCRIBE_TOPIC["MQTT_FAN_MANUALCONTROL"]: #Verifica se è stato ricevuto un messaggio sul topic "MQTT_FAN_MANUALCONTROL"
        #Se è presente un messaggio in coda sul topic verifica il contenuto del messaggio
        if msg == b'true':
            SYSTEM_PARAMS["MANUAL_FAN_CONTROL"] = True #Se il messaggio è 'true' la dashboard ha richiesto controllo manuale del sistema di ventilazione
                                                       #il prarametro di sistema "MANUAL_FAN_CONTROL" viene impostato a True, questo comporterà il blocco delle procedure
                                                       #ventilazione automatica
            manual_fan_control() #Richiama la procedura che consente di prendere il controllo manuale del sistema di ventilazione
        elif msg == b'false':
            SYSTEM_PARAMS["MANUAL_FAN_CONTROL"] = False #Se il messaggio è 'false' la dashboard ha rilasciato il controllo manuale del sistema di ventilazione
                                                        #il prarametro di sistema "MANUAL_FAN_CONTROL" viene impostato a False, questo comporterà la riattivazione delle procedure
                                                        #ventilazione automatica

    if topic == MQTT_SUBSCRIBE_TOPIC["MQTT_FAN_MANUALSTATE"]: #Verifica se è stato ricevuto un messaggio sul topic "MQTT_FAN_MANUALSTATE"
        #Se è presente un messaggio in coda sul topic verifica il contenuto del messaggio
        if msg == b'true':
            SYSTEM_PARAMS["MANUAL_FAN_STATE"] = True  #Se il messaggio è 'true' la dashboard ha richiesto l'accensione manuale della pompa
                                                      #dopo aver preso il controllo del sistema di ventilazione, il prarametro di sistema
                                                      #"MANUAL_FAN_STATE" viene impostato a True andando ad indicare alle
                                                      #altre procedure di controllo della ventilazione che la ventola è attiva per via di un comando arrivato dalla
                                                      #dashboard
            manual_fan_on() #Viene richiamata la procedura di attivazione manuale della ventola
        elif msg == b'false':
            SYSTEM_PARAMS["MANUAL_FAN_STATE"] = False #Se il messaggio è 'false' la dashboard ha richiesto lo spegnimento manuale della pompa
                                                      #il prarametro di sistema "MANUAL_FAN_STATE" viene impostato a False andando ad indicare alle
                                                      #altre procedure di controllo della ventulazione che la ventola è disattivata per via di un comando arrivato dalla
                                                      #dashboard
            manual_fan_off() #Viene richiamata la procedura di disattivazione manuale della ventola

    if topic == MQTT_SUBSCRIBE_TOPIC["MQTT_FAN_ACTIVATIONTEMP"]: #Verifica se è stato ricevuto un messaggio sul topic "MQTT_FAN_ACTIVATIONTEMP"
        #Se è presente un messaggio in coda su questo topic significa che l'utente ha impostato dalla dashboard una nuova soglia critica 
        #di temperatura dell'ambiente sulla base del quale deve essere effettuata la ventilazione
        SYSTEM_PARAMS["FAN_ACTIVATION_TEMP"] = int(msg) #il paramentro di sistema "FAN_ACTIVATION_TEMP" viene impostato al valore 
                                                        #contenuto nel messaggio arrivato dalla dashboard, la procedura si assicura di convertire
                                                        #il valore in intero, sulla base di questo paramentro la procedura di ventilazione automatica
                                                        #deciderà quando dovrà essere attivata la ventilazione
    
    if topic == MQTT_SUBSCRIBE_TOPIC["MQTT_LIGHTS_MANUALCONTROL"]: #Verifica se è stato ricevuto un messaggio sul topic "MQTT_LIGHTS_MANUALCONTROL"
        #Se è presente un messaggio in coda sul topic verifica il contenuto del messaggio
        if msg == b'true':
            SYSTEM_PARAMS["MANUAL_LIGHTS_CONTROL"] = True #Se il messaggio è 'true' la dashboard ha richiesto controllo manuale dell'illuminazione dell'ambiente
                                                          #il prarametro di sistema "MANUAL_LIGHTS_CONTROL" viene impostato a True, questo comporterà il blocco delle procedure
                                                          #di regolazione dell'illuminazione automatica
            manual_light_control() #Richiama la procedura che consente di prendere il controllo manuale del sistema di illuminazione
        elif msg == b'false':
            SYSTEM_PARAMS["MANUAL_LIGHTS_CONTROL"] = False #Se il messaggio è 'false' la dashboard ha rilasciato il controllo manuale dell'illuminazione dell'ambiente
                                                           #il prarametro di sistema "MMANUAL_LIGHTS_CONTROL" viene impostato a False, questo comporterà la riattivazione delle procedure
                                                           #di regolazione dell'illuminazione automatica
    
    if topic == MQTT_SUBSCRIBE_TOPIC["MQTT_LIGHTS_MANUALLED"]: #Verifica se è stato ricevuto un messaggio sul topic "MQTT_LIGHTS_MANUALLED"
        #Se è presente un messaggio in coda su questo topic significa che l'utente ha impostato dalla dashboard il livello di luminosità
        #dell'ambiente in tramite comando manuale
        SYSTEM_PARAMS["MANUAL_LIGHTS_LEVEL"] = int(msg) #il paramentro di sistema "MANUAL_LIGHTS_LEVEL" viene impostato al valore 
                                                        #contenuto nel messaggio arrivato dalla dashboard, la procedura si assicura di convertire
                                                        #il valore in intero, sulla base di questo paramentro la procedura di regolazione del livello di illuminazione manuale 
                                                        #successivamente richiamata si assicurerà che i led emanino il livello di intensità luminosa
                                                        #richiesto dalla dashboard
        manual_light_level() #Viene richiamata la procedura di regolazione del livello di luminosità manuale
    
    if topic == MQTT_SUBSCRIBE_TOPIC["MQTT_LIGHTS_LEVEL"]:  #Verifica se è stato ricevuto un messaggio sul topic "MQTT_LIGHTS_LEVEL"
        SYSTEM_PARAMS["LIGHTS_OFF_LEVEL"] = int(msg) #il paramentro di sistema "LIGHTS_OFF_LEVEL" viene impostato al valore 
                                                     #contenuto nel messaggio arrivato dalla dashboard, la procedura si assicura di convertire
                                                     #il valore in intero, sulla base di questo paramentro la procedura di regolazione del livello di luminosità
                                                     #automatica deciderà quando dovrà essere attivata l'illuminazione

#Questa funzione implementa la logica che consente di effettuare la connessione al broker MQTT
def mqtt_connection():

    global client, oled
    global OLED_COLOR

    print("Connecting to MQTT server", end="")
    shift_point = 0
    #Stampa sul display oled lo stato del sistema indicando che il sistema sta iniziando la procedura di connessione al broker MQTT
    oled.print_line("Connecting to", 0, 1, OLED_COLOR)
    oled.print_line_no_fill("MQTT server", 0, 10, OLED_COLOR)
    client.connect(MQTT_SUBSCRIBE_TOPIC, subCallback) #Richiama su client il metodo connect che implementa la logica 
                                                      #per effettuare la connessione al server MQTT, prende come paramentri
                                                      #il dizionario di Topic a cui il sistema deve sottoscriversi e la funzione 
                                                      #subCallBack che verrà eseguita ogni volta che il sistema verificherà la presenza di messaggi
                                                      #sul broker MQTT sui topic a cui il sistema si è sottoscritto durante la fase di connessione
                                                      #al broker
    while shift_point < 28: #Ciclo che effettua delle stampe sul display oled che vanno a rappresentare graficamente che la procedura di connessione è in corso
        print(".", end="")
        oled.print_line_no_fill(".", 85 + shift_point, 10, OLED_COLOR)
        time.sleep(0.1)
        shift_point = shift_point + 6
    if client.get_conn_state(): #Verifica se la connessione al broker è andata a buon fine
        print(" Connected")
        #Stampa sul display oled lo stato del sistema indicando che il sistema si è connesso al broker correttamente
        oled.print_line_no_fill("Connected!", 0, 20, OLED_COLOR)
        oled.fill_clr()
    else:
        print("Failure connecting to MQTT server!!")
        #Stampa sul display oled lo stato del sistema indicando che il sistema non si è connesso al broker correttamente
        oled.print_line_no_fill("Not Connected!", 0, 20, OLED_COLOR)
        oled.fill_clr()

#Questa funzione verrà eseguita come funzione di handling per gli interrupt 
#generati dal bottone di hard restart
#la logica implementata da questa procedura preparara il sistema all'esecuzione delle
#procedure di riavvio
def hard_restart(btn_restart):
    global LAST_RESET, SYSTEM_PARAMS, DELTA_MAX_RESET

    #Procedura di eliminazione del bouncing del bottone
    current = time.ticks_ms()
    delta = time.ticks_diff(current, LAST_RESET)
    
    if delta < DELTA_MAX_RESET:
        return
    
    LAST_RESET = current
    SYSTEM_PARAMS["RESTART_SYSTEM"] = True #Setta il paramentro di sistema "RESTART_SYSTEM" a True
                                           #questo causerà il riavvio del sistema al prossimo ciclo di
                                           #esecuzione

restart_btn.irq(trigger=Pin.IRQ_RISING, handler=hard_restart) #Definisce un irq sul fronte di salita del bottone di restart

#Questa funzione è richiamata al termine dell'esecuzione della funzione di handling per gli interrupt 
#generati dal bottone di apertura e chiusura della porta, la logica di questa procedura implementa la 
#riscrittura delle informazioni dinamiche riguardanti lo stato del sistema, questa procedura è necessaria
#perche la funzione di handling dell'irq esegue un fill del display per stampare altre info di interesse,
#dunque prima che la funzione di handling restituisca il controllo al programma è necessario riportare le 
#le informazioni stampate nello schermo oled nello stato precedente alla chiamata della funzione di handling.
#per fare ciò la funzione ha necessità di verificare se prima della chiamata alla funzione di handling 
#alcuni controlli manuali erano attivi tramite l'accesso ai valori contenuti nei paramteri di sistema
def change_door_state_reprint():
    global SYSTEM_PARAMS
    global oled
    
    if SYSTEM_PARAMS["MANUAL_IRRIGATION_CONTROL"] == True: #Verifica se il parametro di sistema "MANUAL_IRRIGATION_CONTROL" è impostato a True
        #Se il paramentro è impostato a True significa che il controllo del sistema di irrigazione è
        #manuale dunque la procedura stampa sul display che il sistema di irrigazione è sotto controllo MANUALE
        oled.fill_rect(40, 30, 30, 10, OLED_FILL)
        oled.print_line_no_fill("MAN=>", 40, 30, OLED_COLOR)
        if SYSTEM_PARAMS["MANUAL_IRRIGATION_PUMP"] == True: #Verifica se il parametro di sistema "MANUAL_IRRIGATION_PUMP" è impostato a True
            #Se il paramentro è impostato a True significa che la pompa è stata attivata a seguito di un comando manuale 
            #inviato dalla dashboard, dunque la procedura stampa sul display che la pompa è attiva
            oled.fill_rect(80, 30, 30, 10, OLED_FILL)
            oled.print_line_no_fill("ON", 80, 30, OLED_COLOR)
        else:
            #Se il paramentro è impostato a False significa che la pompa è stata disattivata a seguito di un comando manuale 
            #inviato dalla dashboard, dunque la procedura stampa sul display che la pompa non è attiva
            oled.fill_rect(80, 30, 30, 10, OLED_FILL)
            oled.print_line_no_fill("OFF", 80, 30, OLED_COLOR)
    
    if SYSTEM_PARAMS["MANUAL_FAN_CONTROL"] == True: #Verifica se il parametro di sistema "MANUAL_FAN_CONTROL" è impostato a True
        #Se il paramentro è impostato a True significa che il controllo del sistema di ventilazione è
        #manuale dunque la procedura stampa sul display che il sistema di ventilazione è sotto controllo MANUALE
        oled.fill_rect(35, 20, 30, 10, OLED_FILL)
        oled.print_line_no_fill("MAN=>", 35, 20, OLED_COLOR)
        
        if SYSTEM_PARAMS["MANUAL_FAN_STATE"] == True: #Verifica se il parametro di sistema "MANUAL_FAN_STATE" è impostato a True
            #Se il paramentro è impostato a True significa che la ventola è stata attivata a seguito di un comando manuale 
            #inviato dalla dashboard, dunque la procedura stampa sul display che la ventola è attiva
            oled.fill_rect(80, 20, 60, 10, OLED_FILL)
            oled.print_line_no_fill("ON", 80, 20, OLED_COLOR)
        else:
            #Se il paramentro è impostato a False significa che la ventola è stata disattivata a seguito di un comando manuale 
            #inviato dalla dashboard, dunque la procedura stampa sul display che la ventola non è attiva
            oled.fill_rect(80, 20, 60, 10, OLED_FILL)
            oled.print_line_no_fill("OFF", 80, 20, OLED_COLOR)
    
    if SYSTEM_PARAMS["MANUAL_LIGHTS_CONTROL"] == True: #Verifica se il parametro di sistema "MANUAL_LIGHTS_CONTROL" è impostato a True
        #Se il paramentro è impostato a True significa che il controllo del sistema di illuminazione è
        #manuale dunque la procedura stampa sul display che il sistema di irrigazione è sotto controllo MANUALE
        oled.fill_rect(49, 40, 41, 10, OLED_FILL)
        oled.print_line_no_fill("MAN=>", 49, 40, OLED_COLOR)

        #La procedura stampa il livello di luminosità in percentuale impostato a seguito di un comando manuale
        #inviato dalla dashboard, questo valore è contenuto nella variabile di sistema "MANUAL_LIGHT_LEVEL"
        oled.fill_rect(90, 40, 60, 10, OLED_FILL)
        oled.print_line_no_fill(str(SYSTEM_PARAMS["MANUAL_LIGHTS_LEVEL"]) + "%", 90, 40, OLED_COLOR)

#Questa funzione verrà eseguita come funzione di handling per gli interrupt 
#generati dal bottone di apertura e chiusura della porta
#la logica implementata da questa procedura consente di effettuare l'apertura 
#e la chiusura della porta
def change_door_state(btn_door):
    global LAST_DOOR, SYSTEM_PARAMS, DELTA_MAX_DOOR, IRQ_LOCK, MQTT_DOOR_STATE
    global door, oled, client
    global OLED_FILL, OLED_COLOR

    if IRQ_LOCK == False: #Verifica se l'IRQ_LOCK è False
        #Se l'IRQ_LOCK è false significa che non è in esecuzione nessuna procedura di 
        #boot o di riavvio del sistema dunque la funzione può essere eseguita

        #Procedura di eliminazione del bouncing del bottone
        current = time.ticks_ms()
        delta = time.ticks_diff(current, LAST_DOOR)
        
        if delta < DELTA_MAX_DOOR:
            return
        
        LAST_DOOR = current

        SYSTEM_PARAMS["DOOR_OPEN"] = not SYSTEM_PARAMS["DOOR_OPEN"] #Inverte il valore contenuto nel paramentro di sistema
                                                                    #"DOOR_OPEN", di default questo paramentro è settato a False
                                                                    #perchè durante la costruzione dell'istanza dell'oggetto door
                                                                    #della classe DOOR la porta viene portata all'angolo di chiusura
                                                                    #dunque dopo l'avvio o il riavvio del sistema la porta è sempre chiusa
                                                                    #la procedura in questa riga inverte il valore perchè la pressione del pulsante
                                                                    #che ha generato l'irq vuole provocare un cambiamento nello stato della porta 
        
        if SYSTEM_PARAMS["DOOR_OPEN"] == True: #Verifica se il paramentro di sistema "DOOR_OPEN" è stato portato al valore True 
            #Se il paramentro "DOOR_OPEN" è stato portato al valore True significa che la porta deve essere aperta 
            #perchè partiva da uno stato False che ne stava ad indicare la chiusura
            
            door.open_door() #provoca l'apertura della porta fino all'angolo di apertura specificato in 
                             #gradi nel paramentro DOOR_OPEN_ANGLE, l'apertura può essere richiesta tramite la 
                             #chiamata del metodo open_door() sull'oggetto door di classe DOOR che va a realizzare un 
                             #astrazione di alto livello di una porta il cui movimento di apertura e chiusura è realizzato
                             #mediante il movimento di un servo motore
            
            oled.print_door_state(SYSTEM_PARAMS["DOOR_OPEN"], OLED_FILL, OLED_COLOR) #Stampa sul display oled le informazioni di stato aggiornate 
                                                                                     #indicando che è in corso l'apertura della porta tramite al metodo print_door_state() 
                                                                                     #della classe OLED che implementa tutta la logica necessaria
            
            MQTT_PUBLISH_VALUE[MQTT_DOOR_STATE] = ujson.dumps({"door" : 1})  #Aggiorna il dizionario che contiene i valori aggiornati da pubblicare 
                                                                             #in particolare aggiorna il valore da pubblicare sul topic in cui viene pubblicato
                                                                             #lo stato della porta (MQTT_DOOR_STATE), il valore aggiornato è rappresentato con una 
                                                                             #stringa in formato JSON
            try:
                #Prova a pubblicare il nuovo valore che rappresenta lo stato della porta sul topic MQTT_DOOR_STATE
                #andando ad aggiornare le info di stato sul display oled
                client.publish(MQTT_DOOR_STATE, MQTT_PUBLISH_VALUE[MQTT_DOOR_STATE])
                oled.fill_rect(55, 10, 80, 10, OLED_FILL)
                oled.print_line_no_fill("Published", 55, 10, OLED_COLOR)
            except OSError as e:
                print("Error during the sensors data pubblication: ", e)
                oled.fill_rect(55, 10, 80, 10, OLED_FILL)
                oled.print_line_no_fill("Error", 55, 10, OLED_COLOR)
            
        elif SYSTEM_PARAMS["DOOR_OPEN"] == False: #Verifica se il paramentro di sistema "DOOR_OPEN" è stato portato al valore False
            #Se il paramentro "DOOR_OPEN" è stato portato al valore False significa che la porta deve essere chiusa
            #perchè partiva da uno stato True che ne stava ad indicare l'apertura

            door.close_door() #provoca la chiusura della porta fino all'angolo di chiusura specificato in 
                              #gradi nel paramentro DOOR_CLOSE_ANGLE, la chiusura può essere richiesta tramite la 
                              #chiamata del metodo close_door() sull'oggetto door di classe DOOR che va a realizzare un 
                              #astrazione di alto livello di una porta il cui movimento di apertura e chiusura è realizzato
                              #mediante il movimento di un servo motore
            
            oled.print_door_state(SYSTEM_PARAMS["DOOR_OPEN"], OLED_FILL, OLED_COLOR) #Stampa sul display oled le informazioni di stato aggiornate 
                                                                                     #indicando che è in corso la chiusura della porta tramite al metodo print_door_state() 
                                                                                     #della classe OLED che implementa tutta la logica necessaria
            
            MQTT_PUBLISH_VALUE[MQTT_DOOR_STATE] = ujson.dumps({"door" : 0}) #Aggiorna il dizionario che contiene i valori aggiornati da pubblicare 
                                                                            #in particolare aggiorna il valore da pubblicare sul topic in cui viene pubblicato
                                                                            #lo stato della porta (MQTT_DOOR_STATE), il valore aggiornato è rappresentato con una 
                                                                            #stringa in formato JSON
            
            try:
                #Prova a pubblicare il nuovo valore che rappresenta lo stato della porta sul topic MQTT_DOOR_STATE
                #andando ad aggiornare le info di stato sul display oled
                client.publish(MQTT_DOOR_STATE, MQTT_PUBLISH_VALUE[MQTT_DOOR_STATE])
                oled.fill_rect(55, 10, 80, 10, OLED_FILL)
                oled.print_line_no_fill("Published", 55, 10, OLED_COLOR)
            except OSError as e:
                print("Error during the sensors data pubblication: ", e)
                oled.fill_rect(55, 10, 80, 10, OLED_FILL)
                oled.print_line_no_fill("Error", 55, 10, OLED_COLOR)
        
        oled.print_system_state(OLED_FILL,OLED_COLOR) #Ristampa sullo schermo oled la parte di testo statico che rappresenta
                                                      #lo stato del sistema
        change_door_state_reprint() #Richiama una procedura che va a ristampare sullo schermo oled tutte le informazioni dinamiche
                                    #sullo stato del sistema

door_btn.irq(trigger=Pin.IRQ_RISING, handler=change_door_state) #Definisce un irq sul fronte di salita del bottone apertura/chiusura della porta

#Richiama un metodo sull'oggetto oled che andrà a scrivere sul display che il sistema
#è nella fase di boot e sta avviando le procedure di connettività per consentire 
#la connessione del sistema al broker MQTT
oled.print_booting_info(OLED_FILL, OLED_COLOR)

#Loop principale del sistema, effettua dei controlli sui parametri di sistema e successivamente
#esegue le procedure
while True:
    if SYSTEM_PARAMS["BOOT"] == True: #Verifica se il sistema deve effettuare il boot
        #Se il sistema deve effettuare il boot esegue le procedure di connettività 
        IRQ_LOCK = True #Abilita il lock delle IRQ, eventuali IRQ che potrebbero scattare in questa fase non verranno considerate
        wifi_connect() #Esegue la connessione del sistema al WI-FI
        mqtt_connection() #Esegue la connessione del sistema al server MQTT
        oled.print_system_state(OLED_FILL,OLED_COLOR) #Stampa sul display oled il testo statico che rappresenta le informazioni sullo stato del sistema
        SYSTEM_PARAMS["BOOT"] = False #Imposta il parametro di sistema "BOOT" a False, in modo tale che il sistema al prossimo ciclo di esecuzione
                                      #non dovrà rieseguire le procedure di boot
        IRQ_LOCK = False #Rilascia il lock delle IRQ, tutte le IRQ che scatteranno a seguito delle operazioni di boot verranno gestite
    
    if SYSTEM_PARAMS["PRINT_SYS_STATE"] == True: #Verifica se bisogna stampare sullo schermo oled il testo statico che rappresenta le informazioni sullo stato del sistema
        oled.print_system_state(OLED_FILL,OLED_COLOR) #Stampa il testo statico che rappresenta le info sullo stato del sistema
        SYSTEM_PARAMS["PRINT_SYS_STATE"] = False #Imposta il parametro si sitema "PRINT_SYS_STATE", in modo tale che il sistema
                                                 #al prossimo ciclo di esecuzione non dovrà rieseguire la stampa della parte di testo statica
                                                 #sulle info di sistema

    if SYSTEM_PARAMS["RESTART_SYSTEM"] == False: #Verifica se il sistema deve essere riavviato
        #Se il sistema non deve essere riavviato esegue il classico ciclo di scansione 
        try:
            read_sensor_value() #esegue il ciclo di lettura dei dati dai sensori
        except OSError as e:
            #Cattura eventuali eccezioni lanciate durante il ciclo di lettura dei dati dai sensori
            print("Error while reading the sensors values:", e)
        
        try:
            MQTT_PUBLISH_VALUE = client.publish_new_sensor_value(MQTT_PUBLISH_VALUE, SENSORS_ACTUAL_VALUE) #Pubblica solo i valori prelevati dai sensori che sono variati dal precedente ciclo di scansione
                                                                                                           #utilizzando un metodo messo a disposizione dalla classe MQTT che implementa la logica necessaria per effettuare l'operazione
        except OSError as e:
            #Cattura eventuali eccezioni lanciate durante la pubblicazione dei valori dei sensori
            print("Error during the sensors data pubblication: ", e)
        
        check_cistern() #Verifica lo stato del serbatoio

        try:
            print("Checking messages from the broker...")
            client.check_msg() #Verifica se sul broker MQTT sono presenti dei messaggi pubblicati dalla dashboard sui topic a cui il sistema è sottoscritto
            #Stampa sullo schermo oled le informazioni dinamiche sullo stato del sistema in particolare
            #sullo stato delle operazioni di ricezione/pubblicazione di messaggi dal/verso il broker mqtt 
            oled.fill_rect(55, 10, 80, 10, OLED_FILL)
            oled.print_line_no_fill("Checked", 55, 10, OLED_COLOR)
        except OSError as e:
            oled.fill_rect(55, 10, 80, 10, OLED_FILL)
            oled.print_line_no_fill("Error", 55, 10, OLED_COLOR)
            print("Checking masseges from the broker fail: ", e)

        #A seguito delle operazioni di controllo dei messaggi sul broker MQTT, potrebbero essere arrivati dal broker dei messaggi
        #che hanno provocato l'esecuzione di procedure per il controllo del sistema in modalità manuale e dunque durante il ciclo di 
        #esecuzione il sistema deve verificare se a seguito di questa operazione alcuni valori dei parametri di sistema hanno subito delle variazione
        #rispetto ai valori di default che invece vanno ad indicare che in sistema deve eseguire delle procedure per il controllo automatico 
        #dello stato degli attuatori 


        if SYSTEM_PARAMS["MANUAL_FAN_CONTROL"] == False: #Verifica se il sistema deve eseguire il controllo automatico della ventola 
            auto_fan_control() #Esegue la procedura di controllo automatico della ventola 
        
        if SYSTEM_PARAMS["MANUAL_IRRIGATION_CONTROL"] == False and SYSTEM_PARAMS["BLOCK_IRRIGATION_FOR_CRITICAL_CISTERN_LEVEL"] == False: #Verifica se il sistema deve eseguire il controllo automatico dell'irrigazione 
                                                                                                                                          #nel caso in cui il livello della cisterna è critico dunque il serbatoio è quasi vuoto 
                                                                                                                                          #il paramentro di "BLOCK_IRRIGATION_FOR_CRITICAL_CISTERN_LEVEL" sarà stato portato al valore True
                                                                                                                                          #della procedura check_cistern(), dunque in questo caso anche se il paramentro "MANUAL_IRRIGATION_CONTROL"
                                                                                                                                          #ha valore False e dunque il controllo dell'irrigazione deve essere effettuata in modalità automatica il sistema
                                                                                                                                          #bloccherà in tutti i casi le procedure di irrigazione
            auto_irrigation_control() #Esegue la procedura per il controllo automatico dell'irrigazione

        if SYSTEM_PARAMS["MANUAL_LIGHTS_CONTROL"] == False: #Verifica se il sistema deve eseguire il controllo automatico dell'intensità luminosa dei led
            auto_light_control() #Esegue le procedura per il controllo automatico dell'intensità luminosa

    else:
        IRQ_LOCK = True #Se il sistema deve essere riavviato abilita il lock delle IRQ, 
                        #eventuali IRQ che potrebbero scattare in questa fase non verranno considerate
        restart_procedure() #Esegue la procedura di riavvio del sistema
        IRQ_LOCK = False #Rilascia il lock delle IRQ, tutte le IRQ che scatteranno a seguito delle operazioni di boot verranno gestite
