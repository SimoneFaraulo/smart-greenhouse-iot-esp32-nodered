from machine import Pin, PWM


class DOOR:
    """
    Questa classe fornisce un'astrazione di una porta controllata da un servomotore.
    Fornisce metodi per aprire e chiudere la porta tramite il controllo del duty PWM.
    Gli angoli di apertura e chiusura della porta possono essere configurati dinamicamente.
    """
    def __init__(self, door_pin, door_close_angle, door_open_angle, duty_min = 26, duty_max = 123):
        """
        Inizializza una nuova istanza.
        :param door_pin Il pin utilizzato per controllare il servomotore della porta
        :param door_close_angle L'angolo di chiusura della porta
        :param door_open_angle L'angolo di apertura della porta
        :param duty_min Il valore minimo del duty PWM
        :param duty_max Il valore massimo del duty PWM
        """
        self.door = PWM(Pin(door_pin), freq=50)
        self.close_angle = door_close_angle
        self.open_angle = door_open_angle 
        self.duty_min = duty_min
        self.duty_max = duty_max
        self.door.duty(int(self.duty_min + (self.close_angle/180)*(self.duty_max-self.duty_min)))

    def open_door(self):
        """
        Apre la porta spostando il servomotore all'angolo di apertura specificato
        """
        self.door.duty(int(self.duty_min + (self.open_angle/180)*(self.duty_max-self.duty_min)))
    
    def close_door(self):
        """
        Chiude la porta spostando il servomotore all'angolo di chiusura specificato
        """
        self.door.duty(int(self.duty_min + (self.close_angle/180)*(self.duty_max-self.duty_min)))

    def set_close_angle(self, door_close_angle):
        """
        Imposta l'angolo di chiusura della porta.
        :param door_close_angle Il nuovo angolo di chiusura della porta
        """
        self.close_angle = door_close_angle

    def set_open_angle(self, door_open_angle):
        """
        Imposta l'angolo di apertura della porta.
        :param door_open_angle Il nuovo angolo di apertura della porta
        """
        self.open_angle = door_open_angle

