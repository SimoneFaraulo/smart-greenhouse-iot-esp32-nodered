from machine import Pin, ADC
import ujson

class LDR:
    """Questa classe fornisce l'interfaccia che consente di leggere valori da un foto resistore (LDR)"""
    def __init__(self, pin, min_value=0, max_value=100):
        """
        Inizializza una nuova istanza.
        :parameter pin Un pin collegato a un LDR.
        :parameter min_value Il valore minimo che può essere restituito dal metodo value()..
        :parameter max_value Il valore massimo che può essere restituito dal metodo value().
        """
        if min_value >= max_value:
            raise Exception('Min value is greater or equal to max value')

        self.adc = ADC(Pin(pin))
        self.min_value = min_value
        self.max_value = max_value
        self.last_read = 0
        self.last_value = 0

    def read(self):
        """
        Legge un valore grezzo dall'LDR.
        :return Un valore compreso tra 0 e 4095.
        """
        self.last_read = self.adc.read()
        return self.last_read

    def value(self):
        """
        Legge un valore dall'LDR nell'intervallo specificato.
        :return Un valore dall'intervallo specificato [min, max].
        """
        self.last_value = (self.max_value - self.min_value) * self.read() / 4095
        if self.last_value < 1:
            self.last_value = 1
        return self.last_value

    def get_last_value(self):
        """
        :return Il valore dell'ultima lettura effettuata
        dall'LDR
        """
        return self.last_value

    def get_ujson_value(self):
        """
        Legge un valore dall'LDR nell'intervallo specificato.
        :return Un valore dall'intervallo specificato [min, max] in formato JSON.
        """
        message = ujson.dumps({
        "light": self.value()
        })
        return message
    
    def get_ujson_read(self):
        """
        Legge un valore grezzo dall'LDR.
        :return Un valore compreso tra 0 e 4095 in formato JSON.
        """
        message = ujson.dumps({
        "light": self.read()
        })
        return message
    
