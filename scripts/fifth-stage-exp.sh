# David Omrai
# 8.01.2024

# Data location
data_loc="./data/wuf75-325/wuf75-325-M"

# Create new output file
mkdir results 2> /dev/null
out_name="./results/5p"

# Change the number of flips
temps=(
  "300"
  "400"
  "500"
  "600"
)
cool_fs=(
  "99"
  "999"
  "9999"
)

# Number of repeats
repeats_num=10

# loop function to get paralized

for cool_f in ${cool_fs[@]}; do
  for INSTANCE in $data_loc/*; do 
    echo "running ${cool_f} ${INSTANCE}"
    for i in $(seq 1 $repeats_num); do
        for temp in  ${temps[@]}; do
        ./samwsat.py -i ${INSTANCE} -t $temp -n 1 -c 0.${cool_f} >> ${out_name}-${temp}-${cool_f}.txt 2> /dev/null &
      done
      wait
    done
  done
done

