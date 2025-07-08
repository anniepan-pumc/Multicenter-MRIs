import nibabel as nib
import pandas as pd
import re
import os
from pathlib import Path
import json
import shutil

class nii_selection:
    def __init__(self, data_path, path_to_csv_file,pattern,dst_path):
        self.data_path = Path(data_path)
        self.path_to_csv_file = Path(path_to_csv_file)
        self.nii_files = self.get_files(pattern)
        self.csv_file = self.get_csv_file()
        self.dst_path = Path(dst_path) if dst_path else self.data_path

    def get_files(self,pattern,):
        files = {}
        # Check if the path exists and is a directory
        if not self.data_path.exists() or not self.data_path.is_dir():
            return files
        # Iterate through hospital folders
        for p_path in self.data_path.iterdir():
            if p_path.is_dir():
                # Extract patient ID
                p_match = re.match(pattern, p_path.name)
                if p_match:
                    p_id = p_match.group(0)
                    if p_id not in files:
                        files[p_id] = [p_path]
                    # Iterate through files
                    for file_path in p_path.rglob('*'):
                        if file_path.is_file() and not file_path.name.startswith('._'):
                            if file_path.name.endswith(".nii.gz") or file_path.name.endswith(".nii"):
                                # For .nii.gz files, we need to remove both extensions
                                if file_path.name.endswith(".nii.gz"):
                                    file_path = str(file_path.parent/Path(file_path.name[:-7]))  # Remove .nii.gz
                                else:
                                    file_path = str(file_path.parent/Path(file_path.name[:-4]))  # Remove .nii
                                files[p_id].append(file_path)
        return files
    
    def get_csv_file(self):
        csv_file = pd.read_csv(self.path_to_csv_file,dtype=str,encoding='utf-8-sig')
        return csv_file
    
    def get_csv_file_with_ID(self, ID):
        pID_files = self.csv_file[self.csv_file['ResearchID'] == ID]
        return pID_files
    
    def get_nii_img_with_path(self, path):
        img = nib.load(Path(path))
        return img
    
    def get_meta_data(self, path):
        if Path(path).name.startswith('._'): # Corrected typo here
            return None
        encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'big5']
        
        for encoding in encodings:
            try:
                with open(path, 'r', encoding=encoding) as file:
                    data = json.load(file)
                return data
            except UnicodeDecodeError:
                continue
            except json.JSONDecodeError:
                continue
            except Exception as e:
                print(f"Error reading file {path} with {encoding} encoding: {e}")
                continue
                
        # If none of the encodings worked
        print(f"Failed to read JSON file {path} with any supported encoding")
        return {}

    def get_params_from_metadata(self,metadata,params):
        if params is str:
            return metadata[params]
        elif params is list:
            for p in params:
                if p in metadata:
                    return metadata[p]
        else:
            return None

    
    def find_matching_rows_in_csv(self, metadata, csv_df):
        # Define fields to match
        match_fields = ['SeriesDescription', 'ProtocolName', 'Manufacturer', 'SeriesInstanceUID']	

        match_metadata = pd.DataFrame({field: metadata[field] for field in match_fields if field in metadata}, index=[0])
        # Find matching rows
        matching_rows = csv_df[csv_df.apply(lambda row: all(row[field] == metadata[field] for field in match_fields if field in metadata), axis=1)]
        return matching_rows


    def def_nii_file_with_type(self, marker='备注p'):
        for i, pid in enumerate(self.nii_files.keys()):
            print(f"\nProcessing patient: {pid}")
            nii_files = self.nii_files[pid]
            csv_file = self.csv_file
            print(f"Total number of NIfTI files: {len(nii_files)} ")

            for n in nii_files[1:]:
                parent_dir = nii_files[0]
                json_path = n + '.json'
                nii_path = n + '.nii.gz'
                bval_path = n + '.bval'
                bvec_path = n + '.bvec'
                    
                # Check if files exist
                if not os.path.exists(json_path) or not os.path.exists(nii_path):
                    print(f"Missing files - JSON: {json_path}, NII: {nii_path}")
                    continue
                
                # Get metadata
                meta_data = self.get_meta_data(json_path)
                if not meta_data:
                    print("Failed to read metadata")
                    continue
                
                # Find matching rows
                matching_rows = self.find_matching_rows_in_csv(meta_data, csv_file)
                if matching_rows.empty:
                    print(f"{n}:No matching rows found in CSV")
                    continue
                
                try:
                    label = matching_rows[marker].values[0]
                    study_round = matching_rows['StudyRound'].values[0]
                    study_date = matching_rows['StudyDate'].values[0]
                    series_number = meta_data['SeriesNumber']
                    series_description = meta_data['SeriesDescription']
                    
                    print(f"Label: {label}")
                    print(f"Series Number: {series_number}")
                    print(f"Study Date: {study_date}")
                    print(parent_dir)

                    hpid = int(self.data_path.name.split("+")[0])
                    p_num_id = int(pid.split("+")[0]) if pid.split("+")[0].isdigit() else int(pid.split("-")[2])
                    newid = f"MAP-{hpid:03d}-{p_num_id:03d}"
                    
                    # new_name =  f"{series_number}_{series_description}_{label}"
                    new_name = f"{study_round}_{study_date}_{series_number}_{label}"
                    target_dir = os.path.join(self.dst_path, newid, study_round, label)
                    os.makedirs(target_dir, exist_ok=True)
                    
                    # Move files
                    # Move and rename files``
                    if self.dst_path != self.data_path:
                        if os.path.exists(nii_path) and os.path.exists(json_path):
                            new_nii_path = os.path.join(target_dir, new_name + '.nii.gz')
                            new_json_path = os.path.join(target_dir, new_name + '.json')
                            new_bval_path = os.path.join(target_dir, new_name + '.bval')
                            new_bvec_path = os.path.join(target_dir, new_name + '.bvec')
                            
                            if os.path.exists(bval_path):
                                shutil.copy(bval_path, new_bval_path)
                            if os.path.exists(bvec_path):
                                shutil.copy(bvec_path, new_bvec_path)
                            shutil.copy(nii_path, new_nii_path)
                            shutil.copy(json_path, new_json_path)
                            print(f"Files copyed and renamed successfully to {new_name}")
                        else:
                            print("Source files not found")
                    else:
                        if os.path.exists(nii_path) and os.path.exists(json_path):
                            new_nii_path = os.path.join(target_dir, new_name + '.nii.gz')
                            new_json_path = os.path.join(target_dir, new_name + '.json')
                            new_bval_path = os.path.join(target_dir, new_name + '.bval')
                            new_bvec_path = os.path.join(target_dir, new_name + '.bvec')
                            
                            if os.path.exists(bval_path):
                                shutil.move(bval_path, new_bval_path)
                            if os.path.exists(bvec_path):
                                shutil.move(bvec_path, new_bvec_path)
                            shutil.move(nii_path, new_nii_path)
                            shutil.move(json_path, new_json_path)
                            print(f"Files moved and renamed successfully to {new_name}")
                        else:
                            print("Source files not found")
                        
                except Exception as e:
                    print(f"Error processing file: {e}")
                    continue


if __name__ == "__main__":
    
    import argparse

    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--source_dir', type=str, help='input file path',required=True)
    parser.add_argument('--output_dir', type=str, help='output file path',required=True)
    parser.add_argument('--metadata', type=str, help='metadata notebook path',required=True)
    parser.add_argument('--pattern',default=r'^\d+\+\w+',help='file name pattern')

    args = parser.parse_args()

    path_to_nii_folder = Path(args.source_dir)
    path_to_csv_file = Path(args.metadata)
    dst_path = Path(args.output_dir)
    pattern=args.pattern
    for hp_path in path_to_nii_folder.iterdir():
        print(hp_path)
        if hp_path.is_dir():
            dst_path_new = dst_path/hp_path.name
            if not dst_path_new.exists():
                dst_path_new.mkdir(parents=True)
            dataset = nii_selection(hp_path, path_to_csv_file, pattern,dst_path_new)
            dataset.def_nii_file_with_type(marker='备注')


    