import os, sys


# =============================================================================
# INPUT
# =============================================================================
sys_path_PSSE = r'C:\Program Files\PTI\PSSE36\36.4\PSSPY313'  
sys.path.append(sys_path_PSSE)
os.environ['PATH'] = os.environ['PATH'] + ';' +  sys_path_PSSE
PSSE_LOCATION = r"C:\Program Files\PTI\PSSE36\36.4\PSSBIN"
sys.path.append(PSSE_LOCATION)
os.environ['PATH'] = os.environ['PATH'] + ';' +  PSSE_LOCATION

local_dir = os.path.dirname(__file__)
sys.path.append(local_dir)
os.environ['PATH'] += ';' + local_dir
os.chdir(local_dir)

import psse3604
import psspy
psspy.psseinit(200000)

_i = psspy.getdefaultint()
_f = psspy.getdefaultreal()
_s = psspy.getdefaultchar()

rawFilePath = local_dir + '\\' + 'REGFM_A1.raw'
dyrFilePath = local_dir + '\\' + 'REGFM_A1.dyr' 
outFilePath = local_dir + '\\' + 'REGFMA1.out' 
#csvFilePath = local_dir + '\\' + 'flat.csv'
#csvFilePath = local_dir + '\\' + 'REGFMA1_VoltDown.csv'
#csvFilePath = local_dir + '\\' + 'REGFMA1_VoltUp.csv' 
#csvFilePath = local_dir + '\\' + 'REGFMA1_FreqDwn.csv' 
#csvFilePath = local_dir + '\\' + 'REGFMA1_FreqUp.csv' 
#csvFilePath = local_dir + '\\' + 'REGFMA1_01sFault.csv' 
#csvFilePath = local_dir + '\\' + 'REGFMA1_05sFault.csv' 
csvFilePath = local_dir + '\\' + 'REGFMA1_05s_HI_Fault.csv' 

eventStartTime = 3
eventEndTime = 3.5
simEndTime = 5
faultBusNum = 401
invBusNum_1 = 401
LoadBus = 601

invBusId = '1'

psspy.psseinit(1000000)
psspy.readrawversion(0, '36', rawFilePath)
psspy.fnsl([0,0,0,1,0,0,0,0])     # Power Flow setting
psspy.cong(0)  # conversion for dynamic simulation
psspy.conl(0,1,1,[0,0],[ 0.0,100.0,0.0, 100.0])
psspy.conl(0,1,2,[0,0],[ 0.0,100.0,0.0, 100.0])
psspy.conl(0,1,3,[0,0],[ 0.0,100.0,0.0, 100.0])
psspy.dyre_new([1,1,1,1],dyrFilePath,"","","")

### change GFM inverter parameters in this section ###
ierr = psspy.change_wnmod_icon(invBusNum_1, invBusId, 'REGFMA1', 1, 1) # VFlag (0: internal voltage, 1: terminal voltage)
ierr = psspy.change_wnmod_icon(invBusNum_1, invBusId, 'REGFMA1', 2, 1) # QVFlag 
# (0: plant controller input is the Qref signal (Vref is not used), 1: plant controller input is the Vref signal (Qref is not used))  
ierr = psspy.change_wnmod_con(invBusNum_1, invBusId, 'REGFMA1', 1, 0.01) # TPf    
ierr = psspy.change_wnmod_con(invBusNum_1, invBusId, 'REGFMA1', 2, 0.01) # TQf  
ierr = psspy.change_wnmod_con(invBusNum_1, invBusId, 'REGFMA1', 3, 0.01) # TVf    
ierr = psspy.change_wnmod_con(invBusNum_1, invBusId, 'REGFMA1', 4, 2.00) # Imax   
ierr = psspy.change_wnmod_con(invBusNum_1, invBusId, 'REGFMA1', 5, 1.15) # Emax   
ierr = psspy.change_wnmod_con(invBusNum_1, invBusId, 'REGFMA1', 6, 0.00) # Emin    
ierr = psspy.change_wnmod_con(invBusNum_1, invBusId, 'REGFMA1', 7, 0.9) # Pmax
ierr = psspy.change_wnmod_con(invBusNum_1, invBusId, 'REGFMA1', 8, 0.0) # Pmin
ierr = psspy.change_wnmod_con(invBusNum_1, invBusId, 'REGFMA1', 9, 0.44) # Qmax 
ierr = psspy.change_wnmod_con(invBusNum_1, invBusId, 'REGFMA1', 10, -0.44) # Qmin
ierr = psspy.change_wnmod_con(invBusNum_1, invBusId, 'REGFMA1', 11, 0.01) # mp
ierr = psspy.change_wnmod_con(invBusNum_1, invBusId, 'REGFMA1', 12, 0.05) # mq
ierr = psspy.change_wnmod_con(invBusNum_1, invBusId, 'REGFMA1', 13, 0.01) # kppmax
ierr = psspy.change_wnmod_con(invBusNum_1, invBusId, 'REGFMA1', 14, 0.1) # kipmax
ierr = psspy.change_wnmod_con(invBusNum_1, invBusId, 'REGFMA1', 15, 3.0) # kpqmax
ierr = psspy.change_wnmod_con(invBusNum_1, invBusId, 'REGFMA1', 16, 20) # kiqmax
ierr = psspy.change_wnmod_con(invBusNum_1, invBusId, 'REGFMA1', 17, 0.00) # kpv
ierr = psspy.change_wnmod_con(invBusNum_1, invBusId, 'REGFMA1', 18, 5.86) # kiv

### change PLBVF1 parameters in this section ###
ierr = psspy.change_plmod_icon(LoadBus, invBusId, 'PLBVF1', 1, 1) # Voltage Playback flag (1: play voltage signal, else 0)
ierr = psspy.change_plmod_icon(LoadBus, invBusId, 'PLBVF1', 2, 1) # Frequency Playback flag (1: play frequency signal, else 0)
#ierr = psspy.change_plmod_chricn(LoadBus, invBusId, 'PLBVF1', 3, 'VoltStepDown') # Playback file name (in single quotes, without ".plb")
#ierr = psspy.change_plmod_chricn(LoadBus, invBusId, 'PLBVF1', 3, 'VoltStepUp') # Playback file name (in single quotes, without ".plb")
#ierr = psspy.change_plmod_chricn(LoadBus, invBusId, 'PLBVF1', 3, 'FreqStepDown') # Playback file name (in single quotes, without ".plb")
#ierr = psspy.change_plmod_chricn(LoadBus, invBusId, 'PLBVF1', 3, 'FreqStepUp') # Playback file name (in single quotes, without ".plb")
ierr = psspy.change_plmod_chricn(LoadBus, invBusId, 'PLBVF1', 3, 'flat') # Playback file name (in single quotes, without ".plb")


psspy.snap([-1,-1,-1,-1,-1],"GFMI_new.snp")
psspy.chsb(0,1,[-1,-1,-1,1,1,0])
psspy.chsb(0,1,[-1,-1,-1,1,2,0])
psspy.chsb(0,1,[-1,-1,-1,1,3,0])
psspy.chsb(0,1,[-1,-1,-1,1,4,0])
psspy.chsb(0,1,[-1,-1,-1,1,5,0])
psspy.chsb(0,1,[-1,-1,-1,1,6,0])
psspy.chsb(0,1,[-1,-1,-1,1,7,0])
psspy.chsb(0,1,[-1,-1,-1,1,8,0])
psspy.chsb(0,1,[-1,-1,-1,1,9,0])
psspy.chsb(0,1,[-1,-1,-1,1,10,0])
psspy.chsb(0,1,[-1,-1,-1,1,11,0])
psspy.chsb(0,1,[-1,-1,-1,1,21,0])
psspy.chsb(0,1,[-1,-1,-1,1,22,0])
psspy.chsb(0,1,[-1,-1,-1,1,23,0])
psspy.chsb(0,1,[-1,-1,-1,1,24,0])
psspy.chsb(0,1,[-1,-1,-1,1,13,0])
psspy.chsb(0,1,[-1,-1,-1,1,16,0])
psspy.chsb(0,1,[-1,-1,-1,1,29,0]) # added
psspy.chsb(0,1,[-1,-1,-1,1,30,0]) # added
psspy.chsb(0,1,[-1,-1,-1,1,31,0]) # added
psspy.chsb(0,1,[-1,-1,-1,1,32,0]) # added
psspy.chsb(0,1,[-1,-1,-1,1,33,0]) # added
psspy.chsb(0,1,[-1,-1,-1,1,34,0]) # added
psspy.chsb(0,1,[-1,-1,-1,1,35,0]) # added
psspy.chsb(0,1,[-1,-1,-1,1,36,0]) # added
psspy.chsb(0,1,[-1,-1,-1,1,37,0]) # added

GFM_bus_list = [401]
GFM_ID_list = ['1', '1']
for idx in range(len(GFM_bus_list)):
    ierr, variableNumber = psspy.windmind(GFM_bus_list[idx], GFM_ID_list[idx], 'WGEN', 'VAR')


""" Running dynamic simulation """
psspy.dynamics_solution_params([99,_i,_i,_i,_i,_i,_i,_i],[ 1.0,_f, 0.0042, 0.02,_f,_f,_f,_f],'')
psspy.strt_2([1, 0],outFilePath)

psspy.run(0, eventStartTime,999,1,999)

#Uncomment the following three lines for fault 
ierr = psspy.dist_bus_fault_3(3, 0.0, [1, 1, faultBusNum, 0, 1], [0.032,0,0,0.0,0.0,0.0]) # Note: Insert impedance value in ohm, not per-unit
psspy.run(0, eventEndTime,999,1,999)
ierr = psspy.dist_clear_fault(1)

psspy.run(0, simEndTime,999,1,999)

import dyntools
import pandas as pd
chnfobj = dyntools.CHNF(outFilePath)
sh_ttl, ch_id, ch_data = chnfobj.get_data()
plot_chns = list(range(1, len(ch_id)))
csv_dict = {}
time = ch_data['time']
csv_dict['time'] = time
for chn_idx in plot_chns:
 	csv_dict[ch_id[chn_idx]] = ch_data[chn_idx]
df = pd.DataFrame(csv_dict)
df.to_csv(csvFilePath, index=False)
