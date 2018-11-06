import smbus
import time

"""Device Address"""
address_list = [0x48, 0x49, 0x4A, 0x4B]

"""Device Pointer Register"""
pointer_conversion = 0x00
pointer_config = 0x01
#pointer_low_threshold = 0x02
#pointer_high_treshold = 0x03

"""Inside configuration register"""
#config_os = 0x8000
channel_list = {"000" : "AINP = AIN0 and AINN = AIN1",
                "001" : "AINP = AIN0 and AINN = AIN3",
                "010" : "AINP = AIN1 and AINN = AIN3",
                "011" : "AINP = AIN2 and AINN = AIN3",
                "100" : "AINP = AIN0 and AINN = GND",
                "101" : "AINP = AIN1 and AINN = GND",
                "110" : "AINP = AIN2 and AINN = GND",
                "111" : "AINP = AIN3 and AINN = GND"}
FSR_list = {"000" : "6.144 V",
            "001" : "4.096 V",
            "010" : "2.048 V",
            "011" : "1.024 V",
            "100" : "0.512 V",
            "101" : "0.256 V",
            "110" : "0.256 V",
            "111" : "0.256 V"}

#config_mode = 0x100
#config_DR = 0x0080
#config_comp_mode = 0x0000
#config_comp_pol = 0x0000
#config_pol_lat = 0x0000
#config_comp_que = 0x003

bus = smbus.SMBus(1)

"""Reading configuration register"""
def read_config(address):
    try :
        assert address in address_list
        
        #Receiving configuration data from ADC
        config = bus.read_word_data (address, pointer_config ) & 0xFFFF  
        print("Configuration register : {0:016b}".format(config))
        
        # reading channel
        chnl = format(config, "020b")[-15:-12]
        for key, value in channel_list.items():
            if key == chnl :
                print ("Channel : {0}".format(value))     
        
        #Reading PGA FSR
        fsr = format(config, "020b")[-12:-9]
        for key, value in FSR_list.items():
            if key == fsr:
                print ("FSR : {}".format(value))
                
    except AssertionError:
        print ("Please enter a valid address")
    except :
        print ("Error has accoured during reading the configuration register of the ADC")
	
	
    



""" ADS1115 class"""
class Ads1115 :
    def __init__(self, address = 0x48, channel = '100', FSR ="010" ):
        self.address = address
        self.channel = channel
        self.FSR = FSR
        try :
            assert address in address_list
            assert channel in channel_list.keys()
            assert FSR in FSR_list.keys()
            assert type(channel) == str
            assert type(FSR) == str
        except AssertionError :
            print ("Please enter correct values for the arguments. Note that Channel and FSR take string values, for example '100'")
            
            
    """Reading the configuration register"""            
    def read_config(self):
        try :
            #Receiving configuration data from ADC
            config = bus.read_word_data (self.address, pointer_config ) & 0xFFFF  
            print("Configuration register : {0:016b}".format(config))
        except :
            print ("Error has accoured during reading the configuration register of the ADC")
               
        # reading channel
        chnl = format(config, "020b")[-15:-12]
        for key, value in channel_list.items():
            if key == chnl :
                print ("Channel : {0}".format(value))
        
        #Reading PGA FSR
        fsr = format(config, "020b")[-12:-9]
        for key, value in FSR_list.items():
            if key == fsr:
                print ("FSR : {0}".format(value))

 

    """writing the configuration register"""
    def write_config(self):
        try :
            str_new_config = "0"+ self.channel+ self.FSR+"1"+"100"+"0"+"0"+"0"+"11"
            new_config = int(str_new_config, 2)
            bus.write_word_data(self.address, pointer_config, new_config)
            time.sleep(0.5) #to make sure that ADC has finished converting
        except :
            print ("Error has accoured during writing the configuration register to the ADC")
            
        
        

    """read hex raw data output from ads1115 """
    def read_raw_data(self):
        try :
            raw_data = bus.read_word_data(self.address, pointer_conversion) & 0xFFFF
            return (raw_data >> 8) | ((raw_data & 0xFF) << 8) #swapping byte order
        except :
            print ("Error has accured during reading the conversion register of the ADC")          
        
    

    """Conversion Result"""
    def read(self):
        try : 
            """read hex raw data output from ads1115 """
            def read_raw_data():
                raw_data = bus.read_word_data(self.address, pointer_conversion) & 0xFFFF
                return (raw_data >> 8) | ((raw_data & 0xFF) << 8) #swapping byte order
      
            """selecting FSR key that has FSR value given by FSR"""
            def current_FSR ():
                for key, value in FSR_list.items():
                    if key == self.FSR :
                        FSR_value = value
                FSR_value = float( FSR_value.replace("V", "") )#removing 'V' in FSR
                return FSR_value

            return (read_raw_data()/(2**15))*current_FSR()
        
        except :
             print ("Error has accured during reading the conversion register of the ADC")








