from serial import Serial
import numpy as np
import time
import threading

class Tactile():
    def __init__(self, start_time, port_num=0, baudrate=250000, num_tactile_cells=7, num_sensors=2, use_calibrated_data=False, method="bin"):
        print("Initiallizing sensor...")
        # set the start time of the tactile sensor
        self.start_time = start_time
        #  - Sensor parameters -
        print("Defining sensor parameters...")
        # Change this for less more tactile sensors (1 - 4)
        NUM_TACTILE_CELLS = num_tactile_cells
        NUM_SENSORS = num_sensors
        # Length of data stream from microcontroller
        self.data_len = NUM_TACTILE_CELLS * NUM_SENSORS
        # save the option of having calibrated data or not
        self.use_calibrated_data = use_calibrated_data
        #save the method to use when reading tactile data
        self.method = method
        
        # MAX_PORTS = 32
        PORT = f"/dev/ttyACM{port_num}"
        # serial speed  (bits per seconds)
        BAUDRATE = baudrate
        # serial timout (seconds)
        TIMEOUT = 1
        WRITE_TIMEOUT = 1
        
        # - Sensor Object -
        print("Defining sensor object...")
        # Try to open serial port and create serial object
        self.serObj = Serial(
            port=PORT,
            baudrate=BAUDRATE,
            dsrdtr=True,
            write_timeout=WRITE_TIMEOUT,
            timeout=TIMEOUT
        )
        # Timeout to allow the serial connection to stabilize
        time.sleep(3)

        # - initiallize sensor communication -
        print("Setting up sensor communication...")
        # clear any data on the buffer
        self.serObj.reset_input_buffer()
        self.serObj.reset_output_buffer()

        # Start the serial communication
        self.connected = self.start_serial_communication()
        if(not self.connected):
            print("Problem with starting serial communication")
        else:
            print("Serial communication established!")

        # - calibrate the sensor -
        print("Calibrating sensor...")
        # Get the calibrated sensor values
        self.calibration_values = self.calibrate_sensor(num_readings=5)
        # indicate the offset from zero to allow the sensors to fluctuate at rest
        self.calibration_buffer_offset = 10000

        # Read the calibrated data to initiallize the last reported reading
        self.last_readout = None
        self.time_last_updated = None
        self.sensor_buffer = self.initiallize_sensor_buffer(num_readings=3)
        self.buffer_counter = 0

        # Specify that the object is currently not reading data
        self.is_reading_data = False

        print("Sensor initiallized!")


    def calibrate_sensor(self, num_readings):
        # take the median of the number of specified readings
        dimensions = (num_readings, self.data_len)
        calibration_reading = np.zeros(dimensions, dtype=np.uint32)
        for i in range(num_readings):
            time.sleep(0.5)
            calibration_reading[i, :] = np.array(self.read_raw_data()[1], dtype=np.uint32)
        calibration_reading = np.median(calibration_reading, axis=0)
        calibration_reading = calibration_reading.astype("uint32")
        return(calibration_reading)


    def initiallize_sensor_buffer(self, num_readings=3):
        dimensions = (num_readings, self.data_len)
        reading_group = np.zeros(dimensions, dtype=np.uint32)
        for i in range(num_readings):
            time.sleep(0.5)
            if(self.use_calibrated_data):
                self.time_last_updated, self.last_readout = self.read_calibrated_data()
            else:
                self.time_last_updated, self.last_readout = self.read_raw_data()
            reading_group[i, :] = self.last_readout
        return(reading_group)


    def start_serial_communication(self):
        # Write an initial bit to the microcontroller to initiate serial communication
        self.serObj.write(b'a')
        # get the starting time and timeout to wait for acknowledgement bit
        send_time = time.time()
        timeout = 3
        # flag indicating return character received
        start_byte_received = False
        # wait for return byte, stop trying if exceed timeout
        while not start_byte_received and ((time.time()-send_time)<timeout):
            b = int.from_bytes(self.serObj.read(1),'big')
            print(b)
            if b == 255:
                start_byte_received = True
        # return status of acknowledgement bit
        return start_byte_received


    ###
    def get_data(self):
        current_time = time.time()-self.start_time
        return(current_time, self.last_readout)
    

    def get_smoothed_data(self):
        reported_reading = np.median(self.sensor_buffer, axis=0)
        reported_reading = reported_reading.astype("uint32")
        current_time = time.time()-self.start_time
        return(current_time, list(reported_reading))
    

    ###
    def start(self):
        self.is_reading_data = True
        self.tactile_reading_thread = threading.Thread(target=self.update_tactile_readings, args=())
        self.tactile_reading_thread.start()


    def stop(self):
        with threading.Lock():
            self.is_reading_data = False


    def update_tactile_readings(self):
        try:
            while(self.is_reading_data):
                # keep looping to update the tactile sensor readings
                if(self.use_calibrated_data):
                    latest_time, latest_readout = self.read_calibrated_data()
                else:
                    latest_time, latest_readout = self.read_raw_data()
                # update the sensor buffer with the newest tactile data
                self.buffer_counter += 1
                self.buffer_counter %= 3
                with threading.Lock():
                    self.time_last_updated = latest_time
                    self.last_readout = latest_readout
                    self.sensor_buffer[self.buffer_counter, :] = self.last_readout
                # sleep for a short while to reserve resources and give time to read data
                time.sleep(0.001)
                
        except Exception as e:
            print("-------------------------")
            print(e)
            print("-------------------------")
            with threading.Lock():
                self.is_reading_data = False
            
        

    ###
    def read_calibrated_data(self):
        # get the data as an unsigned integer
        reading = np.array(self.read_raw_data()[1], dtype=np.uint32)
        # subtract the calibration values (with the added buffer offset)
        reading -= self.calibration_values
        reading += self.calibration_buffer_offset
        # save the time of the most recent reading
        current_time = time.time()-self.start_time
        # return the list of values
        return(current_time, reading)


    def read_raw_data(self):
        #reset the buffer to get the newest data point before reading
        self.serObj.reset_input_buffer()
        # Read the data from each tactile sensor
        tactile_data = self.read_tactile_sensor(self.method)
        # save the time of the most recent reading
        current_time = time.time()-self.start_time
        # return the time and raw reading
        return(current_time, tactile_data)
    

    def read_tactile_sensor(self, method="hex"):
        match(method.upper()):
            case "PRINT":
                reading = self.read_tactile_sensor_print()
            case "HEX":
                reading = self.read_tactile_sensor_hex()
            case "BIN":
                reading = self.read_tactile_sensor_bin()
        
        return(reading)
    

    def read_tactile_sensor_print(self):
        msg = ""
        b = str(self.serObj.read(1).decode())
        while (b != '\n'):
            msg += b
            b = str(self.serObj.read(1).decode())

        msg = msg.split(';')
        return msg[0:len(msg)-1]


    def read_tactile_sensor_hex(self):
        b = str(self.serObj.read(1).decode())
        msg = ""
        while (b != '\n'):
            msg += b
            b = str(self.serObj.read(1).decode())
        
        msg = msg.split(';')
        hex_list = list()
        for hex_string in msg[0:len(msg)-1]:
            hex_val = int(hex_string, 16)
            hex_list.append(hex_val)
        return hex_list


    def read_tactile_sensor_bin(self):
        val_list = list()
        for i in range(self.data_len):
            msg = 0
            b = int.from_bytes(self.serObj.read(1),'big')
            byteArray = [b]

            while ((b >> 7) & 1):
                b = int.from_bytes(self.serObj.read(1),'big')
                byteArray.append(b)

            for i, byte in enumerate(reversed(byteArray)):
                byte = byte & ~(1<<7)
                msg = msg | (byte << (i*7))
            if msg > 50000:
                msg = msg - 65536

            val_list.append(msg)

        return val_list


    def __del__(self):
        self.serObj.close()