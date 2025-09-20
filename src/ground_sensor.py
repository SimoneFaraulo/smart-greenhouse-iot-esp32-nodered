from machine import Pin, ADC
import ujson

class GROUND_SENSOR:
    """
    Questa classe fornisce un'astrazione di un sensore di umidità del terreno.
    Fornisce metodi per ottenere e interpretare valori di umidità del terreno
    basati sulle letture di un sensore resistivo di umidità del terreno
    """
    def __init__(self, pin, min_value=0, max_value=100, max_value_read = 500, min_value_read = 0):
        """
        Inizializza una nuova istanza.
        :param pin Il pin a cui è collegato il sensore
        :param min_value Il valore minimo che può essere restituito
        :param max_value Il valore massimo che può essere restituito
        """
        if min_value >= max_value:
            raise Exception('Min value is greater or equal to max value')

        self.adc = ADC(Pin(pin), atten = ADC.ATTN_11DB)
        self.min_value = min_value
        self.max_value = max_value
        self.max_value_read = max_value_read
        self.min_value_read = min_value_read
        self.last_read = 0
        self.last_value = 0

    def read(self):
        """
        Legge un valore grezzo dal sensore
        :return Un valore grezzo compreso tra 0 e 4095.
        """
        self.last_read = self.adc.read()
        return self.last_read

    def value(self):
        """
        Restituisce il valore di umidità del terreno
        :return Il valore di umidità calcolato, compreso tra il valore minimo e massimo specificato.
        """
        #Calcola la differenza tra i valori massimi e minimi per l'input e l'output
        differenza_input = self.max_value_read - self.min_value_read
        differenza_output = self.max_value - self.min_value

        #Normalizza il valore di input rispetto alla differenza tra i valori di lettura massimi e minimi
        valore_normalizzato = (self.read() - self.min_value_read) / differenza_input

        #Mappa il valore normalizzato nel range specificato per l'umidità del terreno
        valore_output = (valore_normalizzato * differenza_output) + self.min_value
        
        #Gestisce eventuali casi eccezionali
        if valore_output == 0:
            valore_output = 100
            self.last_value = valore_output
            return self.last_value
        elif valore_output == 100:
            valore_output = 0
            self.last_value = valore_output
            return self.last_value
        else:
            #Calcola il complemento a 100 del valore di output per invertire la scala di umidità
            valore_output = 100 - valore_output
            #Memorizza il valore calcolato come ultimo valore e lo restituisce
            self.last_value = valore_output
            return self.last_value
            

    def get_last_value(self):
        """
        Restituisce l'ultimo valore di umidità calcolato
        :return L'ultimo valore di umidità.
        """
        return self.last_value

    def set_max_value_read(self, value):
        """
        Imposta il valore massimo di lettura del sensore.
        :param value Il nuovo valore massimo di lettura.
        """
        self.max_value_read = value 

    def get_ujson_value(self):
        """
        Restituisce il valore di umidità in formato JSON.
        :return Il valore di umidità in formato JSON.
        """
        message = ujson.dumps({
        "humidity": self.value()
        })
        return message
    
    def get_ujson_read(self):
        """
        Legge un valore grezzo dal sensore di umidità del sensore.
        :return Un valore compreso tra 0 e 4095 in formato JSON.
        """
        message = ujson.dumps({
        "humidity": self.read()
        })
        return message
    

