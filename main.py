import random
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import tkinter as tk
from tkinter import simpledialog, messagebox


###///Stuct's///###
###################
class CustomDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("EV Charging Simulation Parameters")
        self.geometry("400x300")
        self.resizable(False, False)

        self.result = None

        self.create_widgets()
        self.create_buttons()

    def create_widgets(self):
        tk.Label(self, text="Enter the parameters for the parking lot:", font=("Arial", 14)).pack(pady=10)

        self.entries = {}
        labels = [
            "First switch current:", "Second switch current:",
            "Number of switches in the second layer:", "Number of charging stations per switch:",
            "Current per station:", "Closed parking time (minutes):"
        ]

        defaults = [0, 0, 0, 0, 0, 0]  # Example default values
        for i, label_text in enumerate(labels):
            frame = tk.Frame(self)
            frame.pack(fill="x", pady=5)
            label = tk.Label(frame, text=label_text, width=30, anchor="w")
            label.pack(side="left")
            entry = tk.Entry(frame)
            entry.insert(0, defaults[i])  # Insert default value
            entry.pack(side="left", fill="x", expand=True)
            self.entries[label_text] = entry

    def create_buttons(self):
        frame = tk.Frame(self)
        frame.pack(pady=20)
        tk.Button(frame, text="OK", command=self.on_ok).pack(side="left", padx=10)
        tk.Button(frame, text="Cancel", command=self.on_cancel).pack(side="left", padx=10)

    def on_ok(self):
        self.result = {key: int(entry.get()) for key, entry in self.entries.items()}
        self.destroy()

    def on_cancel(self):
        self.result = None
        self.destroy()


class Ev:
    def __init__(self, full_battery, current_battery, soc, level, idx, phase, enter_time, exit_time, messege, id):
        self.full_battery=full_battery
        self.current_battery=current_battery
        self.soc=soc
        self.level = level #level represent num from the second_switch
        self.idx=idx       #idx is index in the level
        self.phase=phase
        self.enter_time=enter_time
        self.exit_time=exit_time
        self.messege=messege
        self.id=id

class Parking:
    def __init__(self, first_switch_cur, second_switch_cur, num_second_switch, num_charging_station_per_switch, cur_per_station):
        self.first_switch_cur=first_switch_cur
        self.second_switch_cur=second_switch_cur
        self.num_second_switch=num_second_switch
        self.num_charging_station_per_switch=num_charging_station_per_switch
        self.cur_per_station=cur_per_station

###///Funcrions///###
#####################

#Help functions
def cyclic_qeue(charge_qeue):
    # Perform cyclic rotation to the right
    temp = charge_qeue[-1:] + charge_qeue[:-1]
    for i in range(len(temp)):
        charge_qeue[i] = temp[i]

def calc_all_parking_current_demend(charge_qeues, cur_per_station):
    total_parking_demend_current = 0
    for qeue in charge_qeues:
        total_parking_demend_current = total_parking_demend_current + cur_per_station*len(qeue)
    return total_parking_demend_current

def convert_list_to_sorted_no_dulicate_list(lst):
    no_duplicate_set = set(lst)
    no_duplicate_list = list(no_duplicate_set)
    sorted_no_dulicate_list = sorted(no_duplicate_list)
    return sorted_no_dulicate_list

def print_battery_ev(charge_qeues):
    for i in range(len(charge_qeues)):
        for j in range(len(charge_qeues[i])):
            print("qeue:", i, ",ID:", charge_qeues[i][j].id, ",current_buttery:",round(charge_qeues[i][j].current_battery), ",EV messege:", charge_qeues[i][j].messege)

def insert_ev2charge_qeues(all_ev, minuts, charge_qeues, charge_stations, first_switch_cur, num_second_switch, cur_per_station):
    total_parking_demend_current = calc_all_parking_current_demend(charge_qeues, cur_per_station)
    cur_allocate_level = first_switch_cur / num_second_switch
    answer = "yes"
    for ev in all_ev:
        if(ev.enter_time == minuts):
            if(total_parking_demend_current > 2*first_switch_cur and len(charge_qeues[ev.level])*cur_per_station > cur_allocate_level):
                answer = str(simpledialog.askstring("Input", "Warning! the charging will take longer than expected due to large number of charging vichels. Do you stil want to charge? enter yes or no: "))
            if(answer == "yes"):
                charge_qeues[ev.level].append(ev)
                charge_stations.append(ev)

def calc_remain_cur(charge_qeues, cur_per_station, cur_level_lst, cur_allocate_level):
    remain_cur = 0
    for i in range(len(cur_level_lst)):
        if (cur_level_lst[i] == 0):
            remain_cur = remain_cur + cur_allocate_level - len(charge_qeues[i]) * cur_per_station
    return remain_cur

def max_current_buttery_in_charge_qeue(charge_qeue):
    max_current_battery = 0
    idx = 0
    for i in range(len(charge_qeue)):
        if(charge_qeue[i].current_buttery > max_current_battery):
            max_current_battery = charge_qeue[i].current_buttery
            idx = i
    return idx


#####################################
#####################################

def send_ev_message_stage_3(charge_qeue, num_second_switch):
    len_qeue = len(charge_qeue)
    len_qeue_num_sending_message = max(int(0.2*len_qeue) , 1) #will asking 20% of the most charge ev's

    percent_charge_ev = [0] * len_qeue
    for j in range(len(charge_qeue)):
        percent_charge_ev[j] = charge_qeue[j].current_battery / charge_qeue[j].full_battery #ordering the battery precent in list by the order of the charge_qeue list

    for i in range(len_qeue_num_sending_message):
        max_element = max(percent_charge_ev)
        max_index = percent_charge_ev.index(max_element)

        capacity_percent_ev = max_element*100
        answer = str(simpledialog.askstring("Input", "Due to crowded parking lot the Taarif is rise by 30 precent Kwh, your battery capacity is %d precent. do you want still charging?" % capacity_percent_ev))
        if(answer == "no" and len(charge_qeue) != 0):
            charge_qeue.pop(max_index)
        percent_charge_ev.pop(max_index)
    return

def parking_stage(charge_qeues, RR_lst, capacity_precent, num_second_switch):
    stage = 0
    for i in range(len(charge_qeues)):
        if(RR_lst[i] == 0):
            stage = 1
            for ev in charge_qeues[i]:
                ev.messege=""

        elif(RR_lst[i] == 1 and capacity_precent[i] > 0.85):
            stage = 2
            for ev in charge_qeues[i]:
                ev.messege="Your level is starting to full, it possible that the Taarif will rise up"

        elif(RR_lst[i] == 1 and capacity_precent[i] < 0.85):
            stage = 3
            for ev in charge_qeues[i]:
                ev.messege="Notice! your level at full capacity"
            send_ev_message_stage_3(charge_qeues[i], num_second_switch)


#Charging Ev in 1 or 3 phase
def charging_Ev(charge_que, cur_per_station, num_ev_can_charge):
    for ev_num in range(num_ev_can_charge):
        if(charge_que[ev_num].soc == 0):
            if(charge_que[ev_num].phase == 3): # 3 phase charging
                charge_que[ev_num].current_battery = charge_que[ev_num].current_battery + (cur_per_station * 3 * 230) / 60
            if(charge_que[ev_num].phase == 1): # 1 phase charging
                charge_que[ev_num].current_battery = charge_que[ev_num].current_battery + (cur_per_station * 230) / 60
            if(charge_que[ev_num].current_battery >= charge_que[ev_num].full_battery):
                charge_que[ev_num].current_battery = charge_que[ev_num].full_battery
                charge_que[ev_num].soc = 1
    for ev in charge_que:
        if(ev.soc == 1):
            charge_que.remove(ev)

def remove_exit_ev(charge_stations, minuts):
    for ev in charge_stations:
        if (ev.exit_time == minuts):
            charge_stations.remove(ev)

def smart_charging(charge_qeues, cur_level_lst ,RR_lst, capacity_precent, cur_per_station, first_switch_cur, second_switch_cur, num_second_switch):
    cur_allocate_level = first_switch_cur/num_second_switch
    num_cur_level_lst_1 = 0
    remain_cur = calc_remain_cur(charge_qeues, cur_per_station, cur_level_lst, cur_allocate_level)
    for i in cur_level_lst:
        num_cur_level_lst_1 = num_cur_level_lst_1 + i
    if(num_cur_level_lst_1 > 0):
        extra_current_each_1_can_get = remain_cur/num_cur_level_lst_1

    for qeue_num in range(len(charge_qeues)):
        # if charge_qeue current demand is less than cur_allocate_level
        if (cur_level_lst[qeue_num] == 0):
            charging_Ev(charge_qeues[qeue_num], cur_per_station, len(charge_qeues[qeue_num]))
            RR_lst[qeue_num] = 0

        # if charge qeue current demand is more than first_switch_cur/num_second_switch
        if (cur_level_lst[qeue_num] == 1):
            cur_level_demand = len(charge_qeues[qeue_num])*cur_per_station
            cur_extra_need = min(second_switch_cur , cur_level_demand) - cur_allocate_level #calc the remain current that needed in the level
            cur_can_provide = min(cur_extra_need , extra_current_each_1_can_get) #check if the needed cur not more than the remainig from all levels
            ev_can_charge_in_level = int(min((cur_allocate_level + cur_can_provide)/cur_per_station , second_switch_cur/cur_per_station))
            charging_Ev(charge_qeues[qeue_num], cur_per_station, ev_can_charge_in_level)

            #init helps list
            if(ev_can_charge_in_level < int(cur_level_demand/cur_per_station)):
                RR_lst[qeue_num] = 1
            capacity_precent[qeue_num] = (min(cur_allocate_level + cur_can_provide , second_switch_cur))/ cur_level_demand

def init_cur_level_lst(charge_qeues, cur_level_lst, num_second_switch, cur_per_station, first_switch_cur):
    for i in range(len(cur_level_lst)):
        cur_level_demand = len(charge_qeues[i]) * cur_per_station
        if (cur_level_demand <= first_switch_cur / num_second_switch):
            cur_level_lst[i] = 0
        else:
            cur_level_lst[i] = 1

def ev_data_list (minutes, ev1_battery_data, ev9_battery_data, ev13_battery_data, ev1, ev9, ev13):
    if (minutes >= 10 and minutes <= 200):
        ev1_battery_data[minutes - 10] = 100 * (ev1.current_battery / ev1.full_battery)
        ev9_battery_data[minutes - 10] = 100 * (ev9.current_battery / ev9.full_battery)
        ev13_battery_data[minutes - 10] = 100 * (ev13.current_battery / ev13.full_battery)

if __name__ == '__main__':
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    dialog = CustomDialog(root)
    root.wait_window(dialog)

    if dialog.result:
        params = dialog.result

        first_switch_cur = params["First switch current:"]
        second_switch_cur = params["Second switch current:"]
        num_second_switch = params["Number of switches in the second layer:"]
        num_charging_station_per_switch = params["Number of charging stations per switch:"]
        cur_per_station = params["Current per station:"]
        closed_parking_time = params["Closed parking time (minutes):"]

        messagebox.showinfo("Initialization", "Starting the EV charging simulation with the provided parameters...")

    # first_switch_cur=200
    # second_switch_cur=60
    # num_second_switch=4
    # cur_per_station=16
    # num_charging_station_per_switch=6
    # closed_parking_time=240

    parking=Parking(first_switch_cur,second_switch_cur,num_second_switch,num_charging_station_per_switch,cur_per_station)
    if(first_switch_cur/(second_switch_cur*num_second_switch) < 0.6):
        messagebox.showinfo("Initialization", "Parking implementation unrealistic")
        exit(1)
    #(full_battery, current_battery, soc, level, idx, phase, enter_time, exit_time, messege, id)
    ev1=Ev(100000,12000,0,0,1,3,10,200,"",1)
    ev2=Ev(70000,30000,0,0,2,1,3,218,"",2)
    # ev3=Ev(40000,22000,0,0,3,3,4,55,"",3)
    # ev4=Ev(90000,22000,0,0,4,3,8,57,"",4)

    ev5=Ev(100000,12000,0,1,1,3,10,200,"",5)
    ev6=Ev(100000,10000,0,1,2,1,5,210,"",6)
    ev7=Ev(110000,17000,0,1,3,1,4,212,"",7)
    # ev8=Ev(80000,30000,0,4,4,1,16,72,"",8)

    ev9=Ev(100000,12000,0,2,1,3,10,200,"",9)
    ev10=Ev(40000,2000,0,2,2,3,8,208,"",10)
    ev11=Ev(40000,3000,0,2,3,3,4,202,"",11)
    ev12=Ev(40000,7000,0,2,4,3,6,200,"",12)

    ev13=Ev(100000,12000,0,3,1,3,10,200,"",13)
    ev14=Ev(40000,6000,0,3,2,3,9,213,"",14)
    ev15=Ev(90000,3000,0,3,3,3,3,201,"",15)
    ev16=Ev(40000,9000,0,3,4,3,6,218,"",16)
    ev17=Ev(80000,3000,0,3,5,1,3,219,"",17)
    ev18=Ev(40000,3000,0,3,6,3,8,207,"",18)
    #ev19=Ev(40000,1000,0,3,5,3,42,102,"",19)
    #ev20=Ev(40000,8000,0,1,6,1,43,104,"",20)
    #ev21=Ev(40000,3000,0,2,6,3,44,108,"",21)


    charge_qeues = []
    for i in range(num_second_switch):
        charge_qeues.append([])

    all_ev = [ev1,ev2,ev5,ev6,ev7,ev9,ev10,ev11,ev12,ev13,ev14,ev15,ev16,ev17,ev18]
    charge_stations = []

    ###### help lists #####################
    cur_level_lst = [0]*num_second_switch
    RR_lst = [0]*num_second_switch
    capacity_precent = [0]*num_second_switch

    ###### help lists for graphs ##########
    ev1_battery_data = [0]*191 #will be in stage 1
    ev9_battery_data = [0]*191 #will be in stage 2
    ev13_battery_data = [0]*191 #will be in stage 3

    Energy_lst_120_min = [0] * len(all_ev)
    init_battery_ev = [0]*len(all_ev)
    for j in range(len(init_battery_ev)):
        init_battery_ev[j] = all_ev[j].current_battery

    minutes = 1

    while(minutes < closed_parking_time):
        insert_ev2charge_qeues(all_ev, minutes, charge_qeues, charge_stations, first_switch_cur, num_second_switch, cur_per_station) #insert ev's to the parking
        init_cur_level_lst(charge_qeues, cur_level_lst, num_second_switch, cur_per_station, first_switch_cur) #init in each minute cur_level_lst
        smart_charging(charge_qeues, cur_level_lst, RR_lst, capacity_precent, cur_per_station, first_switch_cur, second_switch_cur, num_second_switch)
        parking_stage(charge_qeues, RR_lst, capacity_precent, num_second_switch)


        for qeue_num in range(num_second_switch):
            remove_exit_ev(charge_qeues[qeue_num], minutes)
            if(minutes%15 == 0):
                cyclic_qeue(charge_qeues[qeue_num])

        print("minutes: ",minutes)
        #print_battery_ev(charge_qeues)

        if (minutes == 120):
            for j in range(len(all_ev)):
                Energy_lst_120_min[j] = round(all_ev[j].current_battery - init_battery_ev[j])


        ev_data_list(minutes, ev1_battery_data, ev9_battery_data, ev13_battery_data, ev1, ev9, ev13)
        minutes = minutes + 1

    print('End of day')


###### plotting states graphs
#############################
    x = np.arange(0, 191, 1)
    y1 = ev1_battery_data
    y2 = ev9_battery_data
    y3 = ev13_battery_data

    img = Image.open("EV6.JPEG")
    fig, ax = plt.subplots()
    ax.imshow(img, extent=[0, 191, -1.5, 85.5], aspect='auto')

    plt.plot(x,y1, label="Ev in state 1", color='cyan',linewidth=2)
    plt.plot(x,y2, label="Ev in state 2", color='red',linewidth=2)
    plt.plot(x,y3, label="Ev in state 3", color='magenta',linewidth=2)
    plt.legend()
    plt.grid(True, color='white', linewidth=0.25)
    plt.title('EV Charging in each state')
    plt.xlabel('Time[minutes]')
    plt.ylabel('Battery by %')
    plt.show()

###### plotting energy graphs
#############################
    # n = np.arange(0, len(all_ev), 1)
    # y_n = Energy_lst_120_min
    # plt.bar(n, y_n, color='blue')
    # plt.title('Energy each EV received after 120 minutes')
    # plt.xlabel('EV')
    # plt.ylabel('Energy [kWh]')
    # plt.show()

#############################
    # fig, ax = plt.subplots(3)
    # ax[0].plot(x, y1)
    # ax[0].set_title('Stage 1')
    # ax[1].plot(x, y2)
    # ax[1].set_title('Stage 2')
    # ax[2].plot(x, y3)
    # ax[2].set_title('Stage 3')
    # plt.tight_layout()
    # plt.legend()
    # plt.show()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
