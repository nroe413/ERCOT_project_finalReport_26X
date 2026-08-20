import os
import mhi.pscad, logging
import mhi.pscad.utilities.file as mpuf
import pandas

# Log 'INFO' messages & above.  Include level & module name.
logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(name)-26s %(message)s")
logging.getLogger('mhi.pscad').setLevel(logging.WARNING)
LOG = logging.getLogger('main')

project_name = 'VSM_REGFM_B1'

# Launch PSCAD # Insert appropriate PSCAD version here
pscad = mhi.pscad.launch(version='5.0.2', x64=True, minimize=False)


# Load the tutorial workspace
case_folder = os.getcwd()
pscad.load(case_folder + "\REGFM_B1.pswx")
project = pscad.project(project_name)
project.focus()

################### Initial Values RESETS
fault_time = project.component(2101685271)
fault_time.parameters(TF="100", )
fault_time.parameters(DF="0.1", )
GVolt = project.component(731917116)
GVolt.parameters(OH="1.0", )
GVolt.parameters(X="100", )
Gfreq = project.component(1746469063)
Gfreq.parameters(OH="1.0", )
Gfreq.parameters(X="100", )

project.parameters(time_duration="5")
project.parameters(time_step="50")

########## Runing Case
print('Frequency step Down')

Gfreq.parameters(OH="0.99667", )
Gfreq.parameters(X="3.0", )

project.run();
print('Simulation Finished')

fout = mpuf.OutFile(os.path.join(case_folder, 'VSM_REGFM_B1.gf46\VSMdata')),
fout[0].toCSV(csv=case_folder + "\REGFM_B1_res.csv")

##read the csv file
import pandas as pd
data_read = pd.read_csv(case_folder + "\REGFM_B1_res.csv")
data_col_header=data_read.columns
data_col_header_new=[]
for i in data_col_header:
    data_col_header_new.append(i.strip('" ""<>.').replace('<','').replace('>','').replace(':','').replace('"','').replace('.',''))

data_read.columns=data_col_header_new
selected_headers = ['TIME']
selected_headers += ['Vpu','Ipu','Ppu','Qpu','fm']
data_read=data_read.loc[:, selected_headers]
data_read.to_csv(case_folder + '\\' +   'B1_FreqDwn_PSD.csv',index=False)
print('Data Generated')

