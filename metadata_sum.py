import json
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import re 

def get_metadata(src_path,destination_dir,pattern=r'^\d+\+\w+',split_char="+"):
    source_dir = Path(src_path)
    destination_dir = Path(destination_dir)
    if not destination_dir.exists():
        destination_dir.mkdir(parents=True)

    for hpf in tqdm(source_dir.iterdir(), desc='Center progress Loop', leave=True):
        if hpf.is_dir():
            for pid in tqdm(hpf.iterdir(), desc=f'{hpf.name} Patient Loop', leave=False):
                if pid.is_dir():
                    metadata = []
                    for file_path in pid.glob('**/*.json'):
                        if file_path.name.startswith('.'):
                            continue
                        try:
                            # First try UTF-8
                            with open(file_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                        except UnicodeDecodeError:
                            try:
                                # If UTF-8 fails, try GBK
                                with open(file_path, 'r', encoding='gbk') as f:
                                    data = json.load(f)
                            except:
                                # If both fail, skip this file
                                continue
                        metadata.append(data)
                    if metadata:
                        df = pd.DataFrame(metadata)
                        # Check for pattern like "123+Name"
                        if re.match(pattern, pid.name):
                            if split_char == '+':
                                df['pid'] = pid.name.split('+')[0]
                                df['pName'] = pid.name.split('+')[1]
                            elif split_char == '-':
                                df['hpid'] = pid.name.split('-')[1]
                                df['pid'] = pid.name.split('-')[2]
                            else:
                                df['pid'] = re.match(pattern, pid.name).group(0)
                                df['pName'] = pid.name[len(df['pid']):].strip()
                            df.to_csv(destination_dir / f"{pid.name}_metadata.csv", index=False, encoding='utf-8-sig')

def sum_metadata(metadata_dir,pattern=r'^\d+\+\w+'):
    metadata_dir = Path(metadata_dir)
    summary_df = pd.DataFrame()
    for file_path in metadata_dir.glob('*.csv'):
        if re.match(pattern,file_path.name):
            df = pd.read_csv(file_path)
            summary_df = pd.concat([summary_df, df], ignore_index=True)

    # summary_df = summary_df.drop_duplicates()  # Remove duplicate rows
    summary_df = summary_df.dropna(axis=1, thresh=len(summary_df)*0.5)  # Drop columns with >50% NaN
    summary_df.to_csv(metadata_dir / 'summary_metadata.csv', index=False, encoding='utf-8-sig')



if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--source_dir', type=str, help='input file path',required=True)
    parser.add_argument('--output_dir', type=str, help='output file path',required=True)
    parser.add_argument('--pattern',default=r'^\d+\+',help='file name pattern')
    parser.add_argument('--split_char',default="+",help='file name split char')

    args = parser.parse_args()

    source_dir = Path(args.source_dir)
    destination_dir = Path(args.output_dir)
    print('Please check pattern and split character are wrote in correct way, current pattern is {}, split char is {}'.format(args.pattern,args.split_char))
    get_metadata(source_dir,destination_dir,pattern=args.pattern,split_char=args.split_char)
    sum_metadata(destination_dir,pattern=args.pattern)




