"""
Created on Fri Nov 16 10:25:43 2018

@author: khoirul_muzakka
"""





import smbus
import time
import matplotlib.pyplot as plt
import numpy as np

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
FSR_list = {"000" : 6.144,
            "001" : 4.096,
            "010" : 2.048,
            "011" : 1.024,
            "100" : 0.512,
            "101" : 0.256,
            "110" : 0.256,
            "111" : 0.256}

mode_list = {"0" : "Continous Conversion", 
             "1" : "Single shot conversion"}
data_rate_list = {"000" : 8, 
                  "001" : 16, 
                  "010" : 32, 
                  "011" : 64,
                  "100" : 128,
                  "101" : 250, 
                  "110" : 475,
                  "111" : 860 }
#config_comp_mode = 0x0000
#config_comp_pol = 0x0000
#config_pol_lat = 0x0000
#config_comp_que = 0x003

bus = smbus.SMBus(1)


def read_config(address = 0x48):
    """Read the configuration register of ADS1115. The sole argument of this function is Address.""" 

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
                
        #Reading FSR value
        FSR= format(config, "020b")[-12:-9]
        for key, value in FSR_list.items():
            if key == FSR:
                print ("FSR : {} V".format(value))
        
        #Reading operating mode
        mode = format(config, "020b")[-9]
        for key, value in mode_list.items():
            if key == mode:
                print ("Operating Mode : {}".format(value))
                
        #Reading data rate in SPS
        D_R = format(config, "020b")[-8:-5]
        for key, value in data_rate_list.items():
            if key == D_R:
                print ("Data rate : {} SPS".format(value))
                
    except AssertionError:
        print ("Please enter a valid address")
    except :
        print ("Error has accoured during reading the configuration register of the ADC")
        
        
    
def reset (address= 0x48):
    """ Go back to default setting, can be used to stop ADC from converting in continous mode""" 
    try :
        assert address in address_list
        def_config = 0x4583 #channel = 100, FSR = 010, mode =1, data_rate = 100
        bus.write_word_data(address, pointer_config, def_config )
        time.sleep(1/128 +0.0001)
    except AssertionError:
        print ("Please enter a valid address")
    except :
        print("Error has accoured during writing default configuration register to the ADC")
        
    
    

""" ADS1115 class"""
class Ads1115(object) :
    """ When make an instance from this class, configuration register is automatically written to the ADS1115"""
    def __init__(self, address = 0x48, channel = '100', FSR ="000", mode = "1", data_rate = "100"):
        self.address = address
        self.channel = channel
        self.FSR = FSR
        self.mode = mode
        self.data_rate = data_rate
        
        try :
            assert address in address_list
            assert channel in channel_list.keys()
            assert FSR in FSR_list.keys()
            assert mode in mode_list.keys()
            assert data_rate in data_rate_list.keys()            
            
        except AssertionError :
            print ("Please enter correct values for the arguments. Note that Channel, FSR, mode, and data rate take string values, for example '100'")

        self.__write_config()

      
    def __current_FSR_value(self):
        """Find FSR value given the FSR input""" 
        for key, value in FSR_list.items():
            if key == self.FSR :
                return value
               
    
    
    def __data_rate_value (self) :
        """find data rate given data rate input """
        for key, value in data_rate_list.items():
            if key == self.data_rate:
                return value 
        
        
    def __write_config(self):
        """write the configuration register"""
        try :
            str_new_config = "0"+ self.channel+ self.FSR+self.mode+self.data_rate+"0"+"0"+"0"+"11"
            new_config = int(str_new_config, 2)
            bus.write_word_data(self.address, pointer_config, new_config) 
            time.sleep(1/self.__data_rate_value() +0.0001) 
        except :
            print ("Error has accoured during writing the configuration register to the ADC")

    
    def read_raw_data(self):
        """read raw data output from ads1115 """
        try :
            self.__write_config()
            raw_data = bus.read_word_data(self.address, pointer_conversion) & 0xFFFF
            return (raw_data >> 8) | ((raw_data & 0xFF) << 8) #swapping byte order
        except :
            print ("Error has accured during reading the conversion register of the ADC")   
            
   
    
    def just_read(self):
        """Conversion Result without writing config during before reading : useful in continous mode"""
        try :                   
            #Converting from binary two complement to signed integers"""
            def value ():
                if self.read_raw_data() & 0x8000 != 0:
                    return self.read_raw_data()- (1 << 16)
                else :
                    return self.read_raw_data()
                
            return (value()/(2**15))*self.__current_FSR_value()
        
        except :
             print ("Error has accured during reading the conversion register of the ADC")
             
    
            
    def read(self) :
        """ Read the conversion result. The output is in Volts""" 
        try :            
            #Converting from binary two complement to signed integers"""
            def value ():
                if self.read_raw_data() & 0x8000 != 0:
                    return self.read_raw_data()- (1 << 16)
                else :
                    return self.read_raw_data()
                
            return (value()/(2**15))*self.__current_FSR_value()
        
        except :
             print ("Error has accured during reading the conversion register of the ADC")
        

           
    def histogram(self, number_of_samples = 200, bins =50 ):
        """Draw histogram"""
        samples=[]
        for i in range(1,number_of_samples) :
            sample = self.read_raw_data()
            time.sleep(1/self.__data_rate_value() +0.0001)
            samples.append(sample)
            
        mean_raw_data = sum(samples)/number_of_samples
        print (" Mean of Raw Data : {0}".format(mean_raw_data))

        RMS = np.sqrt(sum(np.square([float(i) for i in samples]))/number_of_samples)
        print ("RMS : {0}".format(RMS))
        
        std = np.std([float(i) for i in samples])
        print ("Standard Deviation : {}".format(std))
    
        plt.hist(samples, bins)
        plt.title (" ADS1115 Histogram")
        plt.xlabel ("Raw Data")
        plt.show()

        

        

    
        
        
             
             
    
             





