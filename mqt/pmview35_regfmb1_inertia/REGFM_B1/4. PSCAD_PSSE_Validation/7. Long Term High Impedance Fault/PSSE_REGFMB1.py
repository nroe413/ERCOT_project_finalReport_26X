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

rawFilePath = local_dir + '\\' + 'REGFM_B1.raw'
dyrFilePath = local_dir + '\\' + 'REGFM_B1.dyr' 
outFilePath = local_dir + '\\' + 'REGFMB1.out' 
#csvFilePath = local_dir + '\\' + 'REGFMB1_Flat.csv'
#csvFilePath = local_dir + '\\' + 'REGFMB1_VoltDown.csv'
#csvFilePath = local_dir + '\\' + 'REGFMB1_VoltUp.csv' 
#csvFilePath = local_dir + '\\' + 'REGFMB1_FreqDwn.csv' 
#csvFilePath = local_dir + '\\' + 'REGFMB1_FreqUp.csv' 
#csvFilePath = local_dir + '\\' + 'REGFMB1_01sFault.csv' 
#csvFilePath = local_dir + '\\' + 'REGFMB1_05sFault.csv' 
csvFilePath = local_dir + '\\' + 'REGFMB1_05s_HI_Fault.csv' 

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
ierr = psspy.change_wnmod_icon(invBusNum_1, invBusId, 'REGFMB1U', 1, 0) # wFlag
ierr = psspy.change_wnmod_icon(invBusNum_1, invBusId, 'REGFMB1U', 2, 0) # VdrpFlag
ierr = psspy.change_wnmod_icon(invBusNum_1, invBusId, 'REGFMB1U', 3, 1) # QVFlag 
ierr = psspy.change_wnmod_icon(invBusNum_1, invBusId, 'REGFMB1U', 4, 1) # PQFlag 
ierr = psspy.change_wnmod_icon(invBusNum_1, invBusId, 'REGFMB1U', 5, 1) # FFlag 
ierr = psspy.change_wnmod_icon(invBusNum_1, invBusId, 'REGFMB1U', 6, 1) # ESFlag 
 
# (0: plant controller input is the Qref signal (Vref is not used), 1: plant controller input is the Vref signal (Qref is not used))  
ierr = psspy.change_wnmod_con(invBusNum_1, invBusId, 'REGFMB1U', 1, 0.05) # mq (pu), Q-V droop gain    
ierr = psspy.change_wnmod_con(invBusNum_1, invBusId, 'REGFMB1U', 2, 0.0) # Kpv (pu), Proportional gain Q-V path
ierr = psspy.change_wnmod_con(invBusNum_1, invBusId, 'REGFMB1U', 3, 5.0) # Kiv (pu/s), Integral gain Q-V path (> 0)
ierr = psspy.change_wnmod_con(invBusNum_1, invBusId, 'REGFMB1U', 4, 0.02) # mp (pu), Power-frequency droop gain (> 0)
ierr = psspy.change_wnmod_con(invBusNum_1, invBusId, 'REGFMB1U', 5, 0.05) # Dwmax (pu), upper limit of Δwm (≥ 0)
ierr = psspy.change_wnmod_con(invBusNum_1, invBusId, 'REGFMB1U', 6, -0.05) # Dwmin (pu), lower limit of Δwm (≤ 0)
ierr = psspy.change_wnmod_con(invBusNum_1, invBusId, 'REGFMB1U', 7, 0.265) # KpPLL (pu), PLL proportional gain
ierr = psspy.change_wnmod_con(invBusNum_1, invBusId, 'REGFMB1U', 8, 2.65) # KiPLL (pu), PLL integral gain (> 0)
ierr = psspy.change_wnmod_con(invBusNum_1, invBusId, 'REGFMB1U', 9, 0.2) # DwPLLmax (pu), PLL upper limit (≥ 0)
ierr = psspy.change_wnmod_con(invBusNum_1, invBusId, 'REGFMB1U', 10, -0.2) # DwPLLmin (pu), PLL lower limit (≤ 0)
ierr = psspy.change_wnmod_con(invBusNum_1, invBusId, 'REGFMB1U', 11, 0) # Tp (s), filter time constant in the VSM power loop
ierr = psspy.change_wnmod_con(invBusNum_1, invBusId, 'REGFMB1U', 12, 0.5) # H (s), VSM inertia constant (> 0)
ierr = psspy.change_wnmod_con(invBusNum_1, invBusId, 'REGFMB1U', 13, 0) # D1 (pu), VSM damping constant
ierr = psspy.change_wnmod_con(invBusNum_1, invBusId, 'REGFMB1U', 14, 100.0) # D2 (pu), Transient damping
ierr = psspy.change_wnmod_con(invBusNum_1, invBusId, 'REGFMB1U', 15, 50.0) # wD (per second), washout block angular frequency
ierr = psspy.change_wnmod_con(invBusNum_1, invBusId, 'REGFMB1U', 16, 1.0) # ImaxSS (pu), Steady state current limit (> 0)
ierr = psspy.change_wnmod_con(invBusNum_1, invBusId, 'REGFMB1U', 17, 0.9) # Kf, factor to determine Idmax and Iqmax/
ierr = psspy.change_wnmod_con(invBusNum_1, invBusId, 'REGFMB1U', 18, 2.00) # Ki (pu), Integral gain to limit steady active current (> 0)
ierr = psspy.change_wnmod_con(invBusNum_1, invBusId, 'REGFMB1U', 19, 1.5) # ImaxF (pu), Transient fault current limit (ImaxF > ImaxSS)
ierr = psspy.change_wnmod_con(invBusNum_1, invBusId, 'REGFMB1U', 20, 0.02) # Tpf (s), active power measurement filter time constant
ierr = psspy.change_wnmod_con(invBusNum_1, invBusId, 'REGFMB1U', 21, 0.02) # Tqf (s), reactive power measurement filter time constant
ierr = psspy.change_wnmod_con(invBusNum_1, invBusId, 'REGFMB1U', 22, 0) # Tvf (s), voltage measurement filter time constant
ierr = psspy.change_wnmod_con(invBusNum_1, invBusId, 'REGFMB1U', 23, 0) # Tif (s), current measurement filter time constant
ierr = psspy.change_wnmod_con(invBusNum_1, invBusId, 'REGFMB1U', 24, 1.00) # Ke, Scaling on Idmax, (0 for generator, 0 ≤ Ke ≤ 1 for storage)
ierr = psspy.change_wnmod_con(invBusNum_1, invBusId, 'REGFMB1U', 25, 0.05) # VPLLfrz (pu), voltage below which the PLL is frozen (≤ 0.1)

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
    # psspy.var_channel([-1,variableNumber+6],"TERM_I_" + str(GFM_bus_list[idx]) + "_" + str(GFM_ID_list[idx]))
    # psspy.var_channel([-1,variableNumber+7],"INTRN_Edroop_" + str(GFM_bus_list[idx]) + "_" + str(GFM_ID_list[idx]))


""" Running dynamic simulation """
psspy.dynamics_solution_params([99,_i,_i,_i,_i,_i,_i,_i],[ 1.0,_f, 0.0042, 0.02,_f,_f,_f,_f],'')
psspy.strt_2([1, 0],outFilePath)

psspy.run(0, eventStartTime,999,1,999)

ierr = psspy.dist_bus_fault_3(3, 0.0, [1, 1, faultBusNum, 0, 1], [30,0,0.0,0.0,0.0,0.0])
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
