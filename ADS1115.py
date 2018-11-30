"""
Created on Fri Nov 16 10:25:43 2018

@author: khoirul_muzakka
"""
import smbus
import time
import matplotlib.pyplot as plt
import numpy as np

#Device Address
address_list = [0x48, 0x49, 0x4A, 0x4B]

#Device Pointer Register
pointer_conversion = 0x00
pointer_config = 0x01

#Inside configuration register
channel_list = {0b000 : "AINP = AIN0 and AINN = AIN1",
                0b001 : "AINP = AIN0 and AINN = AIN3",
                0b010 : "AINP = AIN1 and AINN = AIN3",
                0b011 : "AINP = AIN2 and AINN = AIN3",
                0b100 : "AINP = AIN0 and AINN = GND",
                0b101 : "AINP = AIN1 and AINN = GND",
                0b110 : "AINP = AIN2 and AINN = GND",
                0b111 : "AINP = AIN3 and AINN = GND"}

FSR_list = {0b000 : 6.144,
            0b001 : 4.096,
            0b010 : 2.048,
            0b011 : 1.024,
            0b100 : 0.512,
            0b101 : 0.256,
            0b110 : 0.256,
            0b111 : 0.256}

mode_list = {0 : "Continous Conversion", 
             1 : "Single shot conversion"}

data_rate_list = {0b000 : 8, 
                  0b001 : 16, 
                  0b010 : 32, 
                  0b011 : 64,
                  0b100 : 128,
                  0b101 : 250, 
                  0b110 : 475,
                  0b111 : 860 }

bus = smbus.SMBus(1)


def read_config(address = 0x48):
    """Read the configuration register of ADS1115. The sole argument of this function is Address.""" 
    try :
        assert address in address_list
        
        #Receiving configuration data from ADC
        config = bus.read_word_data (address, pointer_config ) & 0xFFFF  
        print("Configuration register : {0:016b}".format(config))
        
        # reading channel
        chnl = (config & 0x7000 ) >> 12
        for key, value in channel_list.items():
            if key == chnl :
                print ("Channel : {0}".format(value))  
                
        #Reading FSR value
        FSR =  (config & 0x0E00 ) >> 9
        for key, value in FSR_list.items():
            if key == FSR:
                print ("FSR : {} V".format(value))
        
        #Reading operating mode
        mode =  (config & 0x0100 ) >> 8
        for key, value in mode_list.items():
           if key == mode:
                print ("Operating Mode : {}".format(value))
                
        #Reading data rate in SPS
        D_R =  (config & 0x00E0 ) >> 5
        for key, value in data_rate_list.items():
            if key == D_R:
                print ("Data rate : {} SPS".format(value))
                
    except AssertionError:
        print ("Please enter a valid address")
    except IOError:
        print ("Device is not connected")
                
    
def reset (address= 0x48):
    """ Go back to default setting, can be used to stop ADC from converting in continous mode""" 
    try :
        assert address in address_list
        def_config = 0x4583 #channel = 0b100, FSR = 0b010, mode =1, data_rate = 0b100
        bus.write_word_data(address, pointer_config, def_config )
        time.sleep(0.1)
    except AssertionError:
        print ("Please enter a valid address")
    except IOError :
        print("Device is not connected")
        

class Ads1115(object) :
    """Basic functionality of ADS1115"""
    def __init__(self, address = 0x48, channel = 0b100, FSR =0b001, mode = 1, data_rate = 0b100):
        self.address = address
        self.channel = channel
        self.FSR = FSR
        self.mode = mode
        self.data_rate = data_rate
        
        try :
            assert address in address_list and channel in channel_list.keys() and FSR in FSR_list.keys() and mode in mode_list.keys() and data_rate in data_rate_list.keys() 
            self.__write_config()
            
        except AssertionError :
            print ("Please enter correct values for the arguments")  
          
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
            new_config = 0 | (self.channel << 12) | (self.FSR << 9) | (self.mode << 8)|(self.data_rate << 5) | (0 << 4) | (0 << 3) | (0 <<2) |0b11
            bus.write_word_data(self.address, pointer_config, new_config) 
            time.sleep(0.1) 
        except IOError :
            print ("Device is not connected")
  
    def read_raw_data(self):
        """read raw data output from ads1115 """
        self.__write_config()
        raw_data = bus.read_word_data(self.address, pointer_conversion) & 0xFFFF
        return (raw_data >> 8) | ((raw_data & 0xFF) << 8) #swapping byte order

    def read_raw_data_cont(self):
        """Read Raw Data in continuous conversion mode, read the raw data without writing config register beforehand"""
        try :
            assert self.mode == 0
            raw_data = bus.read_word_data(self.address, pointer_conversion) & 0xFFFF
            return (raw_data >> 8) | ((raw_data & 0xFF) << 8)
        except AssertionError :
            print ("The device must be in continous conversion mode to run this function")            
        
    def just_read(self):
        """Conversion Result without writing config before reading : useful in continous mode"""      
        def value ():  #Converting from binary two complement to signed integers"""
            if self.read_raw_data() & 0x8000 != 0:
                return self.read_raw_data()- (1 << 16)
            else :
                return self.read_raw_data()        
        return (float(value())/(2**15))*self.__current_FSR_value()
        
    def read(self) :
        """ Read the conversion result. The output is in Volts"""                    
        def value (): #Converting from binary two complement to signed integers
            if self.read_raw_data() & 0x8000 != 0:
                return self.read_raw_data()- (1 << 16)
            else :
                return self.read_raw_data()
            
        return (float(value())/(2**15))*self.__current_FSR_value()      
                   
    def histogram(self, number_of_samples = 200, bins =50 ):
        """Draw histogram"""
        samples=[]
        for i in range(1,number_of_samples) :
            sample = self.read_raw_data()
            samples.append(sample)
            
        mean_raw_data = sum(samples)/number_of_samples
        print ("Mean of Raw Data : {0}".format(mean_raw_data))

        RMS = np.sqrt(sum(np.square([float(i) for i in samples]))/number_of_samples)
        print ("RMS : {0}".format(RMS))
        
        std = np.std([float(i) for i in samples])
        print ("Standard Deviation : {}".format(std))
    
        plt.hist(samples, bins)
        plt.title (" ADS1115 Histogram")
        plt.xlabel ("Raw Data")
        plt.show()

    def histogram_cont(self, number_of_samples = 200, bins =50 ):
        """Draw histogram in continuous conversion mode"""
        samples=[]
        try :
            assert self.mode == 0
            for i in range(1,number_of_samples) :            
                sample = self.read_raw_data_cont()
                time.sleep(0.1)
                samples.append(sample)
                       
            mean_raw_data = sum(samples)/number_of_samples
            print ("Mean of Raw Data : {0}".format(mean_raw_data))

            RMS = np.sqrt(sum(np.square([float(i) for i in samples]))/number_of_samples)
            print ("RMS : {0}".format(RMS))
        
            std = np.std([float(i) for i in samples])
            print ("Standard Deviation : {}".format(std))
    
            plt.hist(samples, bins)
            plt.title ("ADS1115 Histogram")
            plt.xlabel ("Raw Data")
            plt.show()
        except AssertionError :
                print ("The device must be in the continuous conversion mode")

        

        

    
        
        
             
             
    
             





