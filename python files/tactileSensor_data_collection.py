from serial import Serial
import numpy as np
import time

class Tactile():
    def __init__(self, port_num=0):
        #  - Sensor parameters -
        # Change this for less more tactile sensors (1 - 4)
        NUM_SENSORS = 2
        # Length of data stream from microcontroller, assumes 8 barometers per tactile sensor
        self.data_len = NUM_SENSORS * 7 
        
        # MAX_PORTS = 32
        PORT = "COM3" # f"/dev/ttyACM{port_num}"
        # serial speed  (bits per seconds)
        BAUDRATE = 250000
        # serial timout (seconds)
        TIMEOUT  = 1
        WRITE_TIMEOUT = 1
        
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

        # clear any data on the buffer
        self.serObj.reset_input_buffer()
        self.serObj.reset_output_buffer()

        # Start the serial communication
        self.connected = self.start_serial_communication()

        # Get the calibrated sensor values
        self.calibration_values = self.calibrate_sensor(num_readings=5)
        # indicate the offset from zero to allow the sensors to fluctuate at rest
        self.calibration_buffer_offset = 400 #2.5% offset

        # Read the calibrated data to initiallize the last reported reading
        self.sensor_buffer = self.initiallize_sensor_buffer(num_readings=3)
        self.buffer_counter = 0


    def calibrate_sensor(self, num_readings):
        # take the median of the number of specified readings
        dimensions = (num_readings, self.data_len)
        calibration_reading = np.zeros(dimensions, dtype=np.uint16)
        for i in range(num_readings):
            time.sleep(0.5)
            calibration_reading[i, :] = np.array(self.read_raw_data(), dtype=np.uint16)
        calibration_reading = np.median(calibration_reading, axis=0)
        calibration_reading = calibration_reading.astype("uint16")
        return(calibration_reading)


    def initiallize_sensor_buffer(self, num_readings=3):
        dimensions = (num_readings, self.data_len)
        reading_group = np.zeros(dimensions, dtype=np.uint16)
        for i in range(num_readings):
            time.sleep(0.5)
            reading_group[i, :] = self.read_calibrated_data()
        return(reading_group)


    def start_serial_communication(self):
        # Write an initial bit to the microcontroller to initiate serial communication
        self.serObj.write(b'a')
        # get the starting time and timeout to wait for acknowledgement bit
        send_time = time.time()
        timeout = 1
        # flag indicating return character received
        start_byte_received = False
        # wait for return byte, stop trying if exceed timeout
        while not start_byte_received and ((time.time()-send_time)<timeout):
            b = int.from_bytes(self.serObj.read(1),'big')
            if b == 255:
                start_byte_received = True
        # return status of acknowledgement bit
        return start_byte_received


    def read_smoothed_calibrated_data(self):
        # smoothen the reading to reduce effect of glitches
        self.buffer_counter += 1
        self.buffer_counter %= 3

        new_reading = self.read_calibrated_data()

        self.sensor_buffer[self.buffer_counter, :] = new_reading

        reported_reading = np.median(self.sensor_buffer, axis=0)
        reported_reading = reported_reading.astype("uint16")

        #self.last_reported_reading = 0.631*self.last_reported_reading + 0.369*new_reading # constants defined such that 90% of new reading reached after 5 updates
        #self.last_reported_reading = self.last_reported_reading.astype("uint16")
        return(list(reported_reading))


    def read_calibrated_data(self):
        # get the data as an unsigned 16 bit integer
        reading = np.array(self.read_raw_data(), dtype=np.uint16)
        # subtract the calibration values (with the added buffer offset)
        reading -= self.calibration_values
        reading += self.calibration_buffer_offset
        # remove the influence of the 2 most significant bits to treat value as a 14 bit unsigned integer
        reading &= 0x3FFF 
        # return the list of values   
        return(reading)


    def read_raw_data(self):
        #reset the buffer to get the newest data point before reading
        self.serObj.reset_input_buffer()
        # Read the data from each tactile sensor
        tactile_data = list()
        for i in range(self.data_len):
            reading = self.read_single_tactile_sensor(i)
            tactile_data.append(reading)
        self.last_readout = tactile_data
        return(tactile_data)
    

    def read_single_tactile_sensor(self, tactile_id):
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
        return msg
    

    def __del__(self):
        self.serObj.close()




tactile = Tactile(port_num = 1)
if(tactile.connected):
    print("connected")

csv_file = open("./ONR_data/weight_test_all_sensor_raw_calibrated.csv", "w")

logging_duration = 60 # in seconds

start_time = time.time()

try:
    while True:
        elapsed_time = time.time() - start_time  # Calculate elapsed time
        if elapsed_time >= logging_duration:  # Check if the total logging time has passed
            print("Logging finished.")
            break  # Exit the loop after the desired time has passed

        if tactile.serObj.in_waiting > 0:  # Check if data is available in the serial buffer
            data = tactile.read_smoothed_calibrated_data()  # Read the data
            print(data[8:16])  # Print the data for the sensors 8 to 15
            for val in data[8:16]:
                csv_file.write(f"{val},")  # Write data to the CSV file
            csv_file.write("\n")
        else:
            time.sleep(0.1)  # Sleep for a short time before checking again (execution delay) #frequncy 

except Exception as e:
    print(f"An error occurred: {e}")
finally:
    csv_file.close()  # Ensure the file is closed when done