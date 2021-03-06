import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


df_adm = pd.read_csv('PATH TO ADMISSION FILE')
df_adm.ADMITTIME = pd.to_datetime(df_adm.ADMITTIME, format = '%Y-%m-%d %H:%M:%S', errors = 'coerce')
df_adm.DISCHTIME = pd.to_datetime(df_adm.DISCHTIME, format = '%Y-%m-%d %H:%M:%S', errors = 'coerce')
df_adm.DEATHTIME = pd.to_datetime(df_adm.DEATHTIME, format = '%Y-%m-%d %H:%M:%S', errors = 'coerce')

df_adm = df_adm.sort_values(['SUBJECT_ID','ADMITTIME'])
df_adm = df_adm.reset_index(drop = True)
df_adm['NEXT_ADMITTIME'] = df_adm.groupby('SUBJECT_ID').ADMITTIME.shift(-1)
df_adm['NEXT_ADMISSION_TYPE'] = df_adm.groupby('SUBJECT_ID').ADMISSION_TYPE.shift(-1)
rows = df_adm.NEXT_ADMISSION_TYPE == 'ELECTIVE'
df_adm.loc[rows,'NEXT_ADMITTIME'] = pd.NaT
df_adm.loc[rows,'NEXT_ADMISSION_TYPE'] = np.NaN

df_adm = df_adm.sort_values(['SUBJECT_ID','ADMITTIME'])

df_adm[['NEXT_ADMITTIME','NEXT_ADMISSION_TYPE']] = df_adm.groupby(['SUBJECT_ID'])[['NEXT_ADMITTIME','NEXT_ADMISSION_TYPE']].fillna(method = 'bfill')
df_adm['DAYS_NEXT_ADMIT']=  (df_adm.NEXT_ADMITTIME - df_adm.DISCHTIME).dt.total_seconds()/(24*60*60)

df_notes = pd.read_csv('PATH TO NOTES FILE')
df_notes = df_notes.sort_values(by=['SUBJECT_ID','HADM_ID','CHARTDATE'])
df_adm_notes = pd.merge(df_adm[['SUBJECT_ID','HADM_ID','ADMITTIME','DISCHTIME','DAYS_NEXT_ADMIT','NEXT_ADMITTIME','ADMISSION_TYPE','DEATHTIME']],
                        df_notes[['SUBJECT_ID','HADM_ID','CHARTDATE','TEXT']], 
                        on = ['SUBJECT_ID','HADM_ID'],
                        how = 'left')

df_adm_notes.ADMITTIME_C = df_adm_notes.ADMITTIME.apply(lambda x: str(x).split(' ')[0])
df_adm_notes['ADMITTIME_C'] = pd.to_datetime(df_adm_notes.ADMITTIME_C, format = '%Y-%m-%d', errors = 'coerce')
df_adm_notes['CHARTDATE'] = pd.to_datetime(df_adm_notes.CHARTDATE, format = '%Y-%m-%d', errors = 'coerce')
df_adm_notes['DURATION'] = (df_adm_notes['DISCHTIME']-df_adm_notes['ADMITTIME']).dt.total_seconds()/(24*60*60)


###Less than 2 days on admission notes

df_less_n = df_adm_notes[((df_adm_notes['CHARTDATE']-df_adm_notes['ADMITTIME_C']).dt.total_seconds()/(24*60*60))<2]
df_less_n=df_less_n[df_less_n['TEXT'].notnull()]
df_less_n['OUTPUT_LABEL'] = (df_less_n.DAYS_NEXT_ADMIT < 30).astype('int')


# Notes preprocessing 
df_less_n['TEXT']=df_less_n['TEXT'].fillna(' ')
df_less_n['TEXT']=df_less_n['TEXT'].str.replace('\n',' ')
df_less_n['TEXT']=df_less_n['TEXT'].str.replace('\r',' ')
df_less_n['TEXT']=df_less_n['TEXT'].apply(str.strip)
df_less_n['TEXT']=df_less_n['TEXT'].str.lower()


import re
def preprocess1(x):
    y=re.sub('\\[(.*?)\\]','',x) #remove de-identified brackets
    y=re.sub('[0-9]+\.','',y) #remove 1.2. since the segmenter segments based on this
    y=re.sub('dr\.','doctor',y)
    y=re.sub('m\.d\.','md',y)
    y=re.sub('admission date:','',y)
    y=re.sub('discharge date:','',y)
    y=re.sub('--|__|==','',y)
    return y


df_less_n['TEXT']=df_less_n['TEXT'].apply(lambda x: preprocess1(x))
df_less_n['TEXT_len']=df_less_n['TEXT'].apply(lambda x: len(x.split()))

#to get 318 words chunks for readmission tasks
from tqdm import tqdm
df_len = len(df_concat)
want=pd.DataFrame({'ID':[],'TEXT':[],'Label':[]})
for i in (range(df_len)):
    x=df_concat.TEXT.iloc[i].split()
    n=int(len(x)/318)
    for j in range(n):
        want=want.append({'TEXT':' '.join(x[j*318:(j+1)*318]),'Label':df_concat.Label.iloc[i],'ID':df_concat.HADM_ID.iloc[i]},ignore_index=True)
    if len(x)%318>10:
        want=want.append({'TEXT':' '.join(x[-(len(x)%318):]),'Label':df_concat.Label.iloc[i],'ID':df_concat.HADM_ID.iloc[i]},ignore_index=True)
    if i%1000 == 0:
        print (f'iteration {i}/{df_len}')        
        

want.to_csv('less_2_days_notes.csv')







