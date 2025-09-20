from machine import Pin
import dht
import ujson

class ENVIRONMENT_SENSOR:
    """Questa classe fornisce l'interfaccia che consente di leggere valori dal sensore di umidità e temperatura DHT22"""
    def __init__(self, pin):
        """
        Inizializza una nuova istanza.
        :parameter pin Un pin collegato ad un sensore DHT22
        """
        self.dht22_sensor = dht.DHT22(Pin(pin))
        self.last_temperature = 0
        self.last_humidity = 0
    
    def measure(self):
        """Richiede una misurazione al sensore DHT22"""
        self.dht22_sensor.measure()
    
    def get_last_temperature(self):
        """ 
        :return Il valore dell'ultima misurazione della temperatura effettuata
        dal sensore DHT22
        """
        return self.last_temperature
    
    def get_last_humidity(self):
        """
        :return Il valore dell'ultima misurazione della temperatura effettuata
        dal sensore DHT22
        """
        return self.last_humidity

    def read_temperature(self):
        """
        Legge il valore recuprato dall'ultima misurazione della temperatura dal sensore DHT22.
        :return Il valore di temperatura letto
        """
        self.last_temperature = self.dht22_sensor.temperature()
        return self.last_temperature
    
    def read_humidity(self):
        """
        Legge il valore recuprato dall'ultima misurazione dell'umidità dal sensore DHT22.
        :return Il valore di umidità letto
        """
        self.dht22_sensor.measure()
        #self.dht22_sensor.temperature()
        self.last_humidity = self.dht22_sensor.humidity()
        return self.last_humidity
    
    def get_ujson_mesure(self):
        """
        :return Il valore della temperatura e dell'umidità letti in formato JSON
        """
        self.last_humidity = self.dht22_sensor.humidity()
        self.last_temperature = self.dht22_sensor.temperature()
        message = ujson.dumps({
        "temp": self.last_temperature,
        "humidity": self.last_humidity,
        })
        return message
    
    def get_ujson_temp(self):
        """
        :return Il valore di temperatura letto in formato JSON
        """
        self.last_temperature = self.dht22_sensor.temperature()
        message = ujson.dumps({
        "temp": self.last_temperature,
        })
        return message
    
    def get_ujson_humidity(self):
        """
        :return Il valore di umidità letto in formato JSON
        """
        self.last_humidity = self.dht22_sensor.humidity()
        message = ujson.dumps({
        "humidity": self.last_humidity,
        })
        return message


