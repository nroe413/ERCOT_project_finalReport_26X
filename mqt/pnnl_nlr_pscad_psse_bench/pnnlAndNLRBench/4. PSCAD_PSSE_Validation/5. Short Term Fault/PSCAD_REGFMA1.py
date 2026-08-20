import os
import mhi.pscad, logging
import mhi.pscad.utilities.file as mpuf
import pandas

# Log 'INFO' messages & above.  Include level & module name.
logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(name)-26s %(message)s")
logging.getLogger('mhi.pscad').setLevel(logging.WARNING)
LOG = logging.getLogger('main')

project_name = 'REGFM_A1'

# Launch PSCAD # Insert appropriate PSCAD version here
pscad = mhi.pscad.launch(version='5.0.2', x64=True, minimize=False)


# Load the tutorial workspace
case_folder = os.getcwd()
pscad.load(case_folder + "\REGFM_A1_PNNL.pswx")
project = pscad.project(project_name)
project.focus()

################### Initial Values RESETS
fault_time = project.component(963051497)
fault_time.parameters(TF="100", )
fault_time.parameters(DF="0.1", )
fault = project.component(1556776980)
fault.parameters(RON="0.001", )
GVolt = project.component(696389395)
GVolt.parameters(OH="1.0", )
GVolt.parameters(X="100", )
Gfreq = project.component(2018508786)
Gfreq.parameters(OH="1.0", )
Gfreq.parameters(X="100", )

########## Runing Case
print('0.1s Fault Test')
project.parameters(time_duration="5")
project.parameters(time_step="15")

fault_time.parameters(TF="3", )
fault_time.parameters(DF="0.1", )
fault.parameters(RON="0.001", )

project.run();
print('Simulation Finished')

fout = mpuf.OutFile(os.path.join(case_folder, 'REGFM_A1.gf46\REGFM_A1_data')),
fout[0].toCSV(csv=case_folder + "\REGFM_A1_res.csv")

##read the csv file
import pandas as pd
data_read = pd.read_csv(case_folder + "\REGFM_A1_res.csv")
data_col_header=data_read.columns
data_col_header_new=[]
for i in data_col_header:
    data_col_header_new.append(i.strip('" ""<>.').replace('<','').replace('>','').replace(':','').replace('"','').replace('.',''))

data_read.columns=data_col_header_new
selected_headers = ['TIME']
selected_headers += ['V_pu','I_pu','P_pu','Q_pu','f_drp']
data_read=data_read.loc[:, selected_headers]
data_read.to_csv(case_folder + '\\' +   'A1_flt01s_PSD.csv',index=False)
print('Data Generated')
