from ssd1306 import SSD1306_I2C
from machine import I2C, Pin
import time


class OLED:
    """
    Questa classe fornisce l'interfaccia che consente di comunicare con il display OLED SSD1306 utilizzando il protocollo I2C
    la classe fornisce un'astrazione di alto livello che facilita la scrittura testo sul display oled SSD1306, si 
    appoggia ai metodi forniti dal driver ssd1306 
    """
    def __init__(self, oled_width, oled_height, scl_pin, sda_pin):
        """
        Inizializza una nuova istanza.
        :parameter oled_width Una dimensione che indica la larghezza del display OLED SSD1306 espressa in pixel 
        :parameter oled_height Una dimensione che indica l'altezza del display OLED SSD1306 espressa in pixel 
        :parameter scd_pin Un pin collegato al pin scd del display OLED SSD1306
        :parameter sda_pin Un pin collegato al pin sda del display OLED SSD1306
        """
        self.oled_height = oled_height
        self.oled_width = oled_width
        self.oled = SSD1306_I2C(oled_width, oled_height,I2C(0, scl=Pin(scl_pin), sda=Pin(sda_pin)))

    def fill_clr(self, color = 0):
        """
        Eegue il fill dello schermo OLED SSD1306 con il colore specificato
        :parameter color Un valore che indica di che colore deve essere riempito il display (0 = nero, 1 = bianco)
        """
        self.oled.fill(color)

    def print_line(self, text, x, y, c):
        """
        Esegue la stampa di una linea di testo sul display, andando prima a riempire il display
        del colore opposto al colore con cui si vuole scrivere il testo
        :parameter text Un testo che si vuole stampare sul display
        :parameter x Un valore che indica a quale distanza dal bordo sinistro del display deve essere 
        stampato il testo espresso in pixel
        :parameter y Un valore che indica a quale distanza dal bordo superiore del display deve essere 
        stampato il testo espresso in pixel 
        :parameter c Un valore che indica di che colore deve essere il testo da stampare sul display (0 = nero, 1 = bianco)
        """
        #Verifica il colore con cui deve essere riempito il display
        #sulla base del colore del testo da stampare 
        if c == 1:
            self.oled.fill(0)
        elif c == 0:
            self.oled.fill(1)
        
        self.oled.text(text, x, y, c) #Stampa il testo sul display
        self.oled.show() #Rende visibile il testo stampato sul display 
    
    def print_line_no_fill(self, text, x , y, c):
        """
        Esegue la stampa di una linea di testo sul display, senza riempire il display
        del colore opposto al colore con cui si vuole scrivere il testo
        :parameter text Un testo che si vuole stampare sul display
        :parameter x Un valore che indica a quale distanza dal bordo sinistro del display deve essere 
        stampato il testo espresso in pixel
        :parameter y Un valore che indica a quale distanza dal bordo superiore del display deve essere 
        stampato il testo espresso in pixel 
        :parameter c Un valore che indica di che colore deve essere il testo da stampare sul display (0 = nero, 1 = bianco)
        """
        self.oled.text(text, x, y, c) #Stampa il testo sul display
        self.oled.show() #Rende visibile il testo stampato sul display 
    
    def set_height(self, height):
        """
        Consente la modifica del valore che indica l'altezza del display OLED SSD1306 espressa in pixel
        :parameter height Una dimensione che indica l'altezza del display OLED SSD1306 espressa in pixel 
        """
        self.oled_height = oled_height
    
    def set_width(self, width):
        """
        Consente la modifica del valore che indica la larghezza del display OLED SSD1306 espressa in pixel
        :parameter width Una dimensione che indica la larghezza del display OLED SSD1306 espressa in pixel 
        """
        self.oled_width = oled_width

    def fill_rect(self, x0, y0, width, height, color):
        """
        Consente la stampa sul display di un rettangolo
        :parameter text Un testo che si vuole stampare sul display
        :parameter x Un valore che indica a quale distanza dal bordo sinistro del display deve essere 
        stampato il rettangolo espresso in pixel
        :parameter y Un valore che indica a quale distanza dal bordo superiore del display deve essere 
        stampato il rettangolo espresso in pixel 
        :parameter width Una dimensione che indica la larghezza del rettangolo da stampare sul dispay espressa in pixel
        :parameter height Una dimensione che indica l'altezza del rettangolo da stampare sul dispay espressa in pixel
        :parameter color Un valore che indica di che colore deve essere il rettangolo da stampare sul display (0 = nero, 1 = bianco)
        """
        self.oled.fill_rect(x0, y0, width, height, color)

    def print_door_state(self, state, fill, color):
        """
        Stampa sul display le informazioni che indicano l'apertura o la chiusura della porta 
        :parameter state Un valore che indica se la porta è in apertura o in chiusura (True = apertura, False = chiusura)
        :parameter fill Un valore che indica di che colore deve essere riempito il display (0 = nero, 1 = bianco)
        :parameter color Un valore che indica di che colore deve essere il testo da stampare sul display (0 = nero, 1 = bianco)
        """
        if state == True: #Verifica se il parametro state passato indica che la porta è in apertura
                          #o in chiusura
            #Se la porta è in apertura stampa le informazioni che 
            #indicano l'apertura della porta 
            self.oled.fill(fill)
            self.oled.text("Opening door", 0, 1, color)
            shift_point = 0
            while shift_point < 28:
                self.oled.text(".", 93 + shift_point, 1, color)
                self.oled.show()
                time.sleep(0.1)
                shift_point = shift_point + 6
        elif state == False:
            #Se la porta è in chiusura stampa le informazioni che 
            #indicano la chiusura della porta 
            self.oled.fill(fill)
            self.oled.text("Closing door", 0, 1, color)
            shift_point = 0
            while shift_point < 28:
                self.oled.text(".", 93 + shift_point, 1, color)
                self.oled.show()
                time.sleep(0.1)
                shift_point = shift_point + 6
        

    def print_system_state(self, fill, color):
        """
        Stampa sul display le informazioni statiche che indicano lo stato del sistema
        :parameter fill Un valore che indica di che colore deve essere riempito il display (0 = nero, 1 = bianco)
        :parameter color Un valore che indica di che colore deve essere il testo da stampare sul display (0 = nero, 1 = bianco)
        """
        self.oled.fill(fill)
        self.oled.text("Sensors: ", 0, 1, color)
        self.oled.text("Broker: ", 0, 10, color)
        self.oled.text("Fan: ", 0, 20, color)
        self.oled.text("Pump: ", 0, 30, color)
        self.oled.text("Light: ", 0, 40, color)
        self.oled.text("Cistern: ", 0 ,50, color)
        self.oled.show()

    def print_booting_info(self, fill=0, color = 1):
        """
        Stampa sul display le informazioni statiche che indicano che il sistema è in fase di avvio o di riavvio
        :parameter fill Un valore che indica di che colore deve essere riempito il display (0 = nero, 1 = bianco)
        :parameter color Un valore che indica di che colore deve essere il testo da stampare sul display (0 = nero, 1 = bianco)
        """
        self.oled.fill(fill)
        self.oled.text("Booting", 0, 1, color)
        self.oled.show()
        shift_point = 0
        while shift_point < 28:
            self.oled.text(".", 57 + shift_point, 1, color)
            self.oled.show()
            time.sleep(0.1)
            shift_point = shift_point + 6
        self.oled.text("Starting ", 0, 10,color)
        self.oled.show()
        self.oled.text("connectivity ", 0, 20,color)
        self.oled.show()
        self.oled.text("procedures ", 0, 30,color)
        self.oled.show()
        shift_point = 0
        while shift_point < 28:
            self.oled.text(".", 80 + shift_point, 30, color)
            self.oled.show()
            time.sleep(0.1)
            shift_point = shift_point + 6

    


