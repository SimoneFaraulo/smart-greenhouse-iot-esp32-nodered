from machine import Pin

class FAN:
    """
    Questa classe fornisce l'interfaccia che consente di pilotare la ventola utilizzando 
    tramite l'utilizzo di un relè 5V
    """
    def __init__(self, pin):
        """
        Inizializza una nuova istanza.
        :parameter pin Un pin collegato ad un relè 5V
        """
        self.fan = Pin(pin, Pin.OUT)
        self.fan.value(1)
    
    def start_fan(self):
        """
        Imposta il valore logico sul pin di output a 0 e aziona il relè 
        che consente di avviare la ventola
        """
        self.fan.value(0)
    
    def stop_fan(self):
        """
        Imposta il valore logico sul pin di output a 1 e disattiva il relè 
        che consente di fermare la ventola
        """
        self.fan.value(1)
