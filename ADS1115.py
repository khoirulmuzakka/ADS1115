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
        config = bus.read_word_data (address, pointer_config) & 0xFFFF
        swapped_config =( (config & 0xFF) << 8) | (config >> 8)
        print("Configuration register : {0:016b}".format(swapped_config))
        
        # reading channel
        chnl = channel_list[(swapped_config & 0x7000 ) >> 12]
        print ("Channel : {0}".format(chnl))  
                
        #Reading FSR value
        FSR = FSR_list[(swapped_config & 0x0E00 ) >> 9]
        print ("FSR : {} V".format(FSR))
        
        #Reading operating mode
        mode = mode_list[(swapped_config & 0x0100 ) >> 8]
        print ("Operating Mode : {}".format(mode))
                
        #Reading data rate in SPS
        D_R = data_rate_list[(swapped_config & 0x00E0 ) >> 5]
        print ("Data rate : {} SPS".format(D_R))
                
    except AssertionError:
        print ("Please enter a valid address")
    except IOError:
        print ("Device is not connected")
                
    
def reset (address= 0x48):
    """ Go back to default setting, can be used to stop ADC from converting in continous mode. The default setting is
    Channel : AINP = AIN0 and AINN = GND
    FSR : 4.096 V
    Operating Mode : Single shot conversion
    Data rate : 64 SPS""" 
    try :
        assert address in address_list
        def_config = 0x4363 #channel = 0b100, FSR = 0b001, mode =1, data_rate = 0b011
        bus.write_i2c_block_data(address, pointer_config, [def_config >> 8, def_config & 0xFF] )
        time.sleep(0.1)
    except AssertionError:
        print ("Please enter a valid address")
    except :
        print("Error has accoured during writing default configuration register to the ADC")
        

class Ads1115(object) :
    """Basic functionalities of ADS1115"""
    def __init__(self, address = 0x48, channel = 0b100, FSR =0b001, mode = 1, data_rate = 0b011):
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
        return FSR_list[self.FSR]
                 
    def __data_rate_value (self) :
        """find data rate given data rate input """
        return data_rate_list[self.data_rate]
               
    def __write_config(self):
        """write the configuration register"""
        try :
            new_config = (1 << 15) | (self.channel << 12) | (self.FSR << 9) | (self.mode << 8)|(self.data_rate << 5) | 0b11
            bus.write_i2c_block_data(self.address, pointer_config, [new_config >> 8, new_config & 0xFF]) 
            time.sleep(0.1) 
        except IOError :
            print ("Device is not connected")
  
    def raw_data(self):
        """read raw data output from ads1115. The output is 16bit binary two's complement integers.
        Note that we write config register first before retrieving raw data. To get the last conversion raw data
        without first writing config register, use last_raw_data methode"""
        self.__write_config()
        raw_data = bus.read_word_data(self.address, pointer_conversion) & 0xFFFF
        return (raw_data >> 8) | ((raw_data & 0xFF) << 8) #swapping byte order
    
    def read(self) :
        """ Read the conversion result. The output is in Volts.
        This command writes config register first then read the conversion. To get the last conversion result without
        write config register first, use last_conversion methode"""                    
        def value (): #Converting from binary two complement to signed integers
            if self.raw_data() & 0x8000 != 0:
                return self.raw_data()- (1 << 16)
            else :
                return self.raw_data()
            
        return (float(value())/(2**15))*self.__current_FSR_value()

    def last_raw_data(self):
        """Read raw data from the last conversion without writing config register beforehand. The output is 16bit binary
        two's complement integers"""
        raw_data = bus.read_word_data(self.address, pointer_conversion) & 0xFFFF
        return (raw_data >> 8) | ((raw_data & 0xFF) << 8)
        
    def last_read(self):
        """Read conversion Result from the last cnversion without writing config beforehand. The output is in Volts"""      
        def value ():  #Converting from binary two complement to signed integers"""
            if self.last_raw_data() & 0x8000 != 0:
                return self.last_raw_data()- (1 << 16)
            else :
                return self.last_raw_data()    
            
        return (float(value())/(2**15))*self.__current_FSR_value()      
                            
    def histogram_singleshot(self, number_of_samples = 200, bins =50 ):
        """Draw histogram from a multiple single shot conversions."""
        samples=[]
        for i in range(1,number_of_samples) :
            sample = self.raw_data()
            samples.append(sample)
            
        mean_raw_data = np.mean(samples)
        print ("Mean of Raw Data : {0}".format(mean_raw_data))

        RMS = np.sqrt(np.mean(np.square(samples)))
        print ("RMS : {0}".format(RMS))
        
        std = np.std([float(i) for i in samples])
        print ("Standard Deviation : {}".format(std))
    
        plt.hist(samples, bins)
        plt.title (" ADS1115 Histogram")
        plt.xlabel ("Raw Data")
        plt.show()

    def histogram(self, number_of_samples = 200, bins =50 ):
        """Draw histogram in continuous conversion mode"""
        samples=[]
        try :
            assert self.mode == 0
            for i in range(1,number_of_samples) :            
                sample = self.last_raw_data()
                time.sleep(0.1)
                samples.append(sample)
                       
            mean_raw_data = np.mean(samples)
            print ("Mean of Raw Data : {0}".format(mean_raw_data))

            RMS = np.sqrt(np.mean(np.square(samples)))
            print ("RMS : {0}".format(RMS))
        
            std = np.std([float(i) for i in samples])
            print ("Standard Deviation : {}".format(std))
    
            plt.hist(samples, bins)
            plt.title ("ADS1115 Histogram")
            plt.xlabel ("Raw Data")
            plt.show()
        except AssertionError :
                print ("The device must be in the continuous conversion mode")

        

        

    
        
        
             
             
    
             





