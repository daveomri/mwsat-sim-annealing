# David Omrai
# 8.01.2024

# Data location
data_loc="./data/wuf75-325/wuf75-325-M"

# Create new output file
mkdir results1 2> /dev/null
out_name="./results1/5p"

# Change the number of flips
wress=(
  "1"
  "2"
  "3"
  "4"
)

# Number of repeats
repeats_num=10

# loop function to get paralized


for INSTANCE in $data_loc/*; do 
  echo "running ${INSTANCE}"
  for i in $(seq 1 $repeats_num); do
      for wres in  ${wress[@]}; do
      ./samwsat.py -i ${INSTANCE} -t 300 -n $wres -c 0.999 >> ${out_name}-${wres}.txt 2> /dev/null &
    done
    wait
  done
done


