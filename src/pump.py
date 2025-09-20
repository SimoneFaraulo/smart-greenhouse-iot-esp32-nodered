from machine import Pin
import time

class PUMP:
    """
    Questa classe fornisce l'interfaccia che permette di pilotare una pompa di irrigazione
    tramite un relè 5V
    """
    def __init__(self, pin):
        """
        Inizializza una nuova istanza.
        :parameter pin Un pin collegato a un relè 5V che consente di pilotare una pompa di irrigazione
        """
        self.pump = Pin(pin, Pin.OUT)
        self.pump.value(1)
    
    def start_pump(self):
        """
        Imposta il valore logico sul pin di output a 0 e aziona il relè 
        che consente di avviare la pompa 
        """
        self.pump.value(0)
    
    def stop_pump(self):
        """
        Imposta il valore logico sul pin di output a 1 e disattiva il relè 
        che consente di disattivare la pompa 
        """
        self.pump.value(1)

        

