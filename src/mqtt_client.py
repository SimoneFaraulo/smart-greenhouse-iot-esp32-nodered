from umqtt.simple import MQTTClient

class MQTT:
    """
    Questa classe fornisce l'interfaccia che consente di gestire la comunicazione con il broker MQTT utilizzando il protocollo mqtt,
    la classe fornisce un'astrazione di alto livello che le operazioni di connessione e pubblicazione di dati al broker MQTT.
    La classe si appoggia ai metodi forniti dalla classe MQTTClient.
    """
    def __init__(self,client_id, broker_id,  port=0, user=None, password=None, keepalive=0, ssl=False, ssl_params={}):
        """
        Inizializza una nuova istanza.
        :parameter client_id Un identificatore unico per il client MQTT
        :parameter broker_id Un indirizzo del server MQTT (broker) a cui il client deve connettersi, può essere un indirizzo IP o un hostname
        :parameter port Una valore che indica la porta del server MQTT su cui il client deve connettersi, il valore predefinito è 0 Il valore predefinito è 0, 
        che in genere indica che la libreria utilizzerà le porta standard (1883 per connessioni non SSL/TLS e 8883 per connessioni SSL/TLS)
        :parameter user Un valore che indica il nome utente per l'autenticazione con il broker MQTT, questo parametro è facoltativo e viene
        utilizzato quando il broker richiede l'autenticazione del client
        :parameter password Un valore che indica la password per l'autenticazione con il broker MQTT, anche questo parametro è facoltativo e lavora 
        in maniera congiunta al parametro utente
        :parameter keepalive Un valore che indica un intervallo di mantenimento, misurato in secondi. 
        Specifica il periodo massimo tra le comunicazioni con il broker. Se non avviene alcuna comunicazione entro questo intervallo, 
        il client invierà un ping al broker per mantenere la connessione
        :parameter ssl Un valore booleano che specifica se utilizzare SSL/TLS per proteggere la connessione. 
        Se impostato a True, la connessione verrà protetta utilizzando SSL/TLS
        :parameter ssl_params Un dizionario di parametri SSL/TLS passati alla libreria SSL sottostante. 
        Consente di specificare opzioni quali certificati, chiavi e impostazioni del contesto SSL
        """
        self.client = MQTTClient(client_id, broker_id, port=0, user=user, password=password, keepalive=keepalive, ssl=ssl, ssl_params=ssl_params)
        self.conn_state = False
    
    def connect(self, subs_topic_dict = dict(), sub_callback = None, qos = 0):
        """
        Festisce la connessione al broker MQTT e la sottoscrizione a uno o più topic con una specifica 
        Quality of Service (QoS)
        :parameter subs_topic_dict Un dizionario dove le chiavi rappresentano i nomi dei topic e i valori rappresentano i relativi topic a cui il client deve sottoscriversi
        :parameter sub_callback  Una funzione di callback che verrà chiamata quando un messaggio viene ricevuto su uno dei topic sottoscritti. 
        Deve essere una funzione valida (callable). Se subs_topic_dict non è vuoto, questa funzione deve essere fornita e deve essere callable.
        :parameter qos Un intero che rappresenta il livello di Quality of Service per le sottoscrizioni
        """
        if qos > 1: #Verifica il livello di QOS richiesto perchè 
                    #non è supportato QoS = 2.
            print("Qos out of bound: min= 0, max= 1")
            self.conn_state = False
        elif len(subs_topic_dict) > 0 and (not callable(sub_callback)): #Se subs_topic_dict non è vuoto e sub_callback non è una funzione callable,
            print("sub callback not callable") #viene stampato un messaggio di errore "sub callback not callable" 
            self.conn_state = False  #conn_state è impostato a False
        elif len(subs_topic_dict) > 0 and (callable(sub_callback)): #Se subs_topic_dict non è vuoto e sub_callback è una funzione callable
            self.client.connect() #Il client si connette al broker MQTT utilizzando client.connect()
            self.client.set_callback(sub_callback) #Imposta la funzione di callback per le sottoscrizioni con set_callback(sub_callback)
            for k, v in subs_topic_dict.items(): #Sottoscrive a ciascun topic presente in subs_topic_dict utilizzando il livello di QOS specificato.
                self.client.subscribe(v, qos=qos)
            self.conn_state = True #Imposta lo stato della connessione (conn_state) a True.
    
    def subscribe(self, topic, qos = 0):
        """
        Sottoscrive il client a un topic specifico sul broker MQTT utilizzando una specifica Quality of Service (QOS).
        :parameter topic Il topic al quale il client deve sottoscriversi
        :parameter qos Un intero che rappresenta il livello di Quality of Service per la sottoscrizione
        """
        self.client.subscribe(topic, qos=qos) #Sottoscrive il client al topic specificato utilizzando il livello di QOS fornito

    def publish_new_sensor_value(self, pub_dict = dict(), sensors_last_val_dict = dict(), qos = 0):
        """
        Gestisce la pubblicazione di nuovi valori dei sensori sul broker MQTT se i valori sono cambiati, utilizzando una specifica 
        Quality of Service (QOS).
        :parameter pub_dict Un dizionario dove le chiavi rappresentano i nomi dei topic e i valori rappresentano i valori pubblicati più recenti.
        :parameter sensors_last_val_dict Un dizionario dove le chiavi rappresentano i nomi dei topic e i valori rappresentano i valori attuali letti dei sensori.
        :parameter qos Un intero che rappresenta il livello di Quality of Service per le pubblicazioni.
        :return Restituisce pub_dict aggiornato con i nuovi valori pubblicati se ci sono cambiamenti, altrimenti None.
        """
        if len(pub_dict) > 0 and len(sensors_last_val_dict) > 0: #Controlla se pub_dict e sensors_last_val_dict non sono vuoti
            print("published values: ")

            for k, v in sensors_last_val_dict.items(): #Itera su ciascun elemento in sensors_last_val_dict
                if v != pub_dict[k]: #Se il valore corrente del sensore è diverso dal valore pubblicato più recente
                    pub_dict[k] = v #Aggiorna pub_dict con il nuovo valore del sensore
                    self.client.publish(k, pub_dict[k], qos = qos) #Pubblica il nuovo valore sul broker MQTT con il livello di QOS specificato
                    print(k, v)
            return pub_dict #Restituisce il dizionario pub_dict aggiornato
        return None #Restituisce None se pub_dict o sensors_last_val_dict sono vuoti
    
    def publish(self, topic, msg, qos = 0):
        """
        Pubblica un messaggio su un topic specifico sul broker MQTT utilizzando una specifica Quality of Service (QOS)
        :parameter topic Il topic sul quale pubblicare il messaggio
        :parameter msg Il messaggio da pubblicare
        :parameter qos Un intero che rappresenta il livello di Quality of Service per la pubblicazione
        """
        self.client.publish(topic, msg, qos = qos) #Pubblica il messaggio sul broker MQTT utilizzando il livello di QOS specificato
    
    def check_msg(self):
        """
        Verifica se ci sono nuovi messaggi ricevuti sul broker MQTT. Questo metodo chiama la funzione di callback impostata
        per gestire i messaggi in arrivo. Deve essere chiamato periodicamente per processare i messaggi in arrivo.
        """
        self.client.check_msg() #Verifica la presenza di nuovi messaggi e chiama la funzione di callback impostata per gestirli,
                                #se non sono presenti nuovi messaggi ritorna immediatamente
    
    def get_conn_state(self):
        """
        Restituisce lo stato corrente della connessione al broker MQTT.
        :return Restituisce True se il client è connesso al broker MQTT, altrimenti False.
        """
        return self.conn_state


