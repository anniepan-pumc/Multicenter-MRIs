bash dcm2niix_MAP.sh
python metadata_sum.py --source_dir /* --output_dir /*
python MAP_series_marker.py --input /*.csv --output /*.csv --marker *
python nii_selection.py --source_dir /* --output_dir /* --metadata /*.csv
python metadata_sum.py --source_dir /* --output_dir /* --pattern '* - *' --split_char '-'
python MAP_series_marker.py --input /*.csv --output /*.csv --marker *
python study_sumup.py --input /*.csv --output /*.csv