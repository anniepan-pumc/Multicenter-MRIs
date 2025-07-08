# Marker for series selection


import pandas as pd
import re
from datetime import datetime
import numpy as np
from pathlib import Path

def combine_json(json_dir):
    json_dir = Path(json_dir)
    df = pd.DataFrame()
    for file_path in json_dir.glob('*.csv'):
        if file_path.name.startswith('.'):
            continue
        # First try UTF-8
        sub_df = pd.read_csv(file_path, encoding='utf-8-sig', dtype=str)
        df = pd.concat([df, sub_df], ignore_index=True)
    df.dropna(inplace=True)
    df.to_csv(json_dir / 'summary_metadata.csv', index=False, encoding='utf-8-sig')

class MAP_series_marker:
    def __init__(self, df, marker='备注p'):
        self.df = df
        self.marker = marker    
        self.sequence_patterns = {
            'T2': r'T2|t2_blade_tra_p2|Prop T2 TRF|T2 tra',
            'T2Flair': r'Flair|t2_tirm_tra_dark-fluid|t2_tirm_cor_dark-fluid|t2_tse_dark-fluid|OCor fs T2 FLAIR|t2_tra_dark-fluid_p3|T2_tse_dark_fluid_tra|T2_FLAIR_tra|t2_trim_tra_dark-fluid_p3|T2_trim_tra_dark-fluid',
            'T1': r'T1|MPRAGE|MultiPlanar Reconstruction|s3DI_MC_HR|BRAVO|s3D_PCA_SAG|OAx T1 FLAIR|T1_tse_dark_fluid_tra|Oax T1 Flair|T1_trim_tra_dark-fluid|t1_fl2d_tra_p2|t1_fl2d_sag_4mm|t1_tse_dark-fluid_tra_p2|t1_trim_tra_p2|t1_fl2d_tra_p1|t1_tse_dark-fluid_tra_p2|T1_trim_tra_dark-fluid|t1_fl2d_sag_4mm',
            'DWI': r'DWI|scan_trace|DW_SSh|b=0',
            'ADC': r'ADC|Apparent Diffusion Coefficient',
            'TOF': r'TOF|mra|PC_3D_10_tra',
            'ASL': r'asl|Perfusion_Weighted',
            'DTI': r'dti',
            'SWI': r'SWI|SWAN|Phase Ob_Ax_I|hemo|t2_swi|SWI_tra|SWI_t2|t2_fl3d_tra|SWI_fl3d_tra|Pha_Images|FILT_PHA|Mag_Images|FILT_MAG|Ax SWAN',
            'QSM': r'qsm',
            'Plaque': r'Plaque',
            'bold': r'bold|Resting_state'
        }
        self.others_pattern = r'loc|range|report|survey|Screen Save|FGRE|Projection|Processed|Calibration|T1-SPACE|Vs3D_PCA|PosDisp|SPAIR|AutoSave|PSD20210113|angio|DSA|Topogram|BOLUS|Angio3D|Spine|AbdRoutine|Scout|CAROTIDS|mip|min IP|minP'
        self.delete_pattern = r'TSE SENSE|tse_sag_320|tse_sag_384|AbdRoutine|ThorRoutine|CerebrumSeq|STIR|Plane Pilot|Protocol|electronic film|Basic Reading|DEFAULT PS SERIES|Thorax|Carotid|MobiV'
    


    def update_sequence_patterns(self, new_patterns):
        self.sequence_patterns.update(new_patterns)
    
    def update_others_pattern(self, new_pattern):
        self.others_pattern = new_pattern

    def update_delete_pattern(self, new_pattern):
        self.delete_pattern = new_pattern

    def map_series_rule(self):
        self.df[self.marker] = ''
        self._apply_sequence_rules()
        self._apply_manufacturer_rules()
        self._apply_3d_sequence_rules()
        self._apply_SWI_Pha_Mag_rules()
        self.study_round_naming_rule()
        return self.df

    def _apply_sequence_rules(self):
        for index, row in self.df.iterrows():
            # Apply main sequence patterns
            if pd.isna(row['SeriesDescription']):
                row['SeriesDescription'] = row['ProtocolName']

            for sequence_type, pattern in self.sequence_patterns.items():
                if re.search(pattern, str(row['SeriesDescription']), re.IGNORECASE):
                    self.df.at[index, self.marker] = sequence_type

            # Apply others pattern
            if (re.search(self.others_pattern, str(row['SeriesDescription']), re.IGNORECASE) or
                re.search(r"loc", str(row['ProtocolName']), re.IGNORECASE) or
                re.match(r'^[A-Z]{5}$', str(row['SeriesDescription'])) or
                row['SeriesDescription'] in ['A', '2', 'HF']):
                self.df.at[index, self.marker] = "Others"

            # Apply delete pattern
            if (re.search(r"jpg|pjn", str(row['Manufacturer']), re.IGNORECASE) or
                re.search(self.delete_pattern, str(row['SeriesDescription']), re.IGNORECASE) or
                re.search(self.delete_pattern, str(row['ProtocolName']), re.IGNORECASE)):
                self.df.at[index, self.marker] = "delete"
    
    def _apply_SWI_Pha_Mag_rules(self):
        pha_mag_patterns = {
            'SWI_Pha':r'Pha_Images|FILT_PHA',
            'SWI_Mag': r'Mag_Images',
        }
        for index, row in self.df.iterrows():
            if row[self.marker] == 'SWI':
                if re.search(r'PHA', str(row['SeriesDescription']), re.IGNORECASE):
                    self.df.at[index, self.marker] = "SWI_Pha"
                else:
                    self.df.at[index, self.marker] = "SWI"

    def _apply_manufacturer_rules(self):
        toshiba_patterns = {
            'T2Flair': r'Flair',
            'T2': r'T2',
            'T1': r'T1'
        }

        for index, row in self.df.iterrows():
            if (row['Manufacturer'] == 'TOSHIBA_MEC' and 
                (row[self.marker] == '' or pd.isna(row[self.marker]))):
                for sequence_type, pattern in toshiba_patterns.items():
                    if re.search(pattern, str(row['ProtocolName']), re.IGNORECASE):
                        self.df.at[index, self.marker] = sequence_type

    def _apply_3d_sequence_rules(self):
        for index, row in self.df.iterrows():
            if row[self.marker] == 'T1':
                if re.search(r"iso|MPRAGE|3D|MP-RAGE|BRAVO|0.55mm|MultiPlanar Reconstruction|MPRAGE-2_6", 
                           str(row['SeriesDescription']), re.IGNORECASE):
                        self.df.at[index, self.marker] = "3DT1" if row['SpacingBetweenSlices'] < 1.5 or row['SpacingBetweenSlices'] != None else "delete"
    
    def study_round_naming_rule(self):
        '''
        marking study round based on study date
        '''
        self.df['StudyRound'] = ''
        ids = self.df['pid'].unique()
        self.df['StudyDate'] = self.df['AcquisitionDateTime'].str[:10]
        self.df['StudyDate'] = pd.to_datetime(self.df['StudyDate'], format='%Y-%m-%d')
        for id in ids:
            id_df = self.df[self.df['pid'] == id].sort_values('StudyDate')
            round_num = 0
            last_date = None
            for date in id_df['StudyDate']:
                if last_date is None or (date - last_date).days > 180:
                    round_num += 1
                    last_date = date
                self.df.loc[(self.df['pid'] == id) & (self.df['StudyDate'] == date), 'StudyRound'] = "V" + str(round_num)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--input', type=str, help='input file path',required=True)
    parser.add_argument('--output', type=str, help='output file path',required=True)
    parser.add_argument('--marker',default='备注',help='marker column name')

    args = parser.parse_args()

    df = pd.read_csv(args.input,encoding='utf-8-sig')
    marker = MAP_series_marker(df,marker='备注')
    df = marker.map_series_rule()
    df.to_csv(args.output, index=False, encoding='utf-8-sig')