from hcsr04 import HCSR04
import ujson

class CISTERN:
    """
    Questa classe fornisce un'astrazione di una cisterna
    fornendo metodi che consentono di conoscere il suo stato
    I metodi della classe si appoggiano a dei metodi del driver HCSR04 
    che consentono di ottenere misurazioni dal sensore ultrasuoni  HCSR04
    """
    def __init__(self, trigger, echo, height_cm):
        """
        Inizializza una nuova istanza.
        :parameter trigger Un pin collegato al pin di trigger del sensore HCSR04
        :parameter echo Un pin collegato al pin echo del sensore HCSR04
        :parameter height Un valore che esprime l'altezza in cm della cisterna fisica che
        sarà monitorata
        """
        self.cistern = HCSR04(trigger, echo)
        self.height_cm = height_cm
        self.last_level = 0
    
    
    def level(self):
        """
        Calcola un valore in percentuale che corrisponde al livello di liquido 
        che si trova attualmente nella cisterna. 
        Per ottenere un valore attendibile dal calcolo il sensore HCSR04 deve essere posizionato sul lato 
        superiore della cisterna e deve essere rivolto verso la superficie del liquido
        :return Il valore calcolato 
        """
        
        water_surface_distance_cm = self.cistern.distance_cm() #ottiene la distanza in cm dalla superficie del liquido
        
        water_actual_height = self.height_cm - water_surface_distance_cm #calcola l'altezza attuale del liquido all'interno della cisterna
        
        water_level_perc = int((water_actual_height/self.height_cm) * 100) #calcola la percentuale di riempimento dell cisterna in percentuale

        if water_level_perc < 0.0: #verifica se il risultato ottenuto dal calcolo è minore di 0 
            #Se il risultato ottenuto è minore di 0 lo approsima al valore 0
            water_level_perc = 0.0
            self.last_level = water_level_perc
            return self.last_level
        else:
            self.last_level = water_level_perc
            return self.last_level
        
    def get_last_level(self):
        """
        :return Il risultato dell'ultima misurazione del livello di riempimento della cisterna
        """
        return self.last_level

    def get_ujson_level(self):
        """
        :return Il risultato della misurazione del livello di riempimento della cisterna
        in formato JSON
        """
        message = ujson.dumps({
        "cistern_level": self.level()
        })
        return message
