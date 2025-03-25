import time
import datetime
import pathlib

from tactile import Tactile

def write_and_print_tactie_data(csv_file, time_s, data):
    time_ms = int(1000*time_s)
    print(f"{time_ms}: ", end='')
    csv_file.write(f"{time_ms},")
    for val in data:
        print(f"{val},", end='')
        csv_file.write(f"{val},")
    print('')
    csv_file.write("\n")

def main():
    # keep track of a global start time
    start = time.time()
    # instantiate the tactile sensor
    tactile = Tactile(
        start_time = start,
        port_num = "COM3",
        baudrate = 115200, 
        num_tactile_cells = 7, 
        num_sensors = 2,
        use_calibrated_data = False,
        method = "hex"
    )

    REFRESH_RATE_HZ = 20

    # check that the tactile sensor is connected
    if(tactile.connected):
        print("Connected!")
    else:
        raise(Exception("\n========================\nTrouble Connecting Tactile Sensor! Please unplug & plug the USB and try again!\n======================="))
    
    # Get the name of the CSV file from the user
    print("=========================")
    csv_name = input("Please enter a name for the CSV file (do not include '.csv'): ")
    time_string = str(datetime.datetime.now()).replace('-', '_').replace(' ', '_').replace(':', '_').split('.')[0]

    # Start the thread to read the tactile sensor
    tactile.start()

    # Read the tactile sensor to a CSV
    dirpath = pathlib.Path(__file__)
    dirpath = dirpath.parent
    dirpath = dirpath.joinpath("data")
    filename = str(dirpath / f"{csv_name}_data_{time_string}.csv")
    csv_file = open(filename, "w")
    csv_file.write(f"time_ms,L7,L6,L5,L4,L3,L2,L1,R7,R6,R5,R4,R3,R2,R1,\n")
    try:
        while(tactile.is_reading_data):
            # gather data
            time_s, data = tactile.get_data()
            #time_s, data = tactile.get_smoothed_data()

            # write data to csv and print to console
            write_and_print_tactie_data(csv_file, time_s, data)

            # save data given refresh rate
            time.sleep(1/REFRESH_RATE_HZ)
    except:
        # stop the tactile sensor reading when an exception occurs
        tactile.stop()
    finally:
        # lastly, before finishing, close the csv file to save the values
        csv_file.close()

if(__name__ == "__main__"):
    main()