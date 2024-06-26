# David Omrai
# 8.01.2024

# Data location
instname="wuf100-430"
lettrs=(
  "N"
  "M"
  "Q"
  "R"
)

# Create new output file
mkdir black-box 2> /dev/null
out_name="./black-box/bb"

# Number of repeats
repeats_num=10

# loop function to get paralized

task(){
  data_loc="./data/black-box-inst/${instname}/${instname}-${1}"
  for INSTANCE in $data_loc/*; do 
    echo "running ${INSTANCE}"
    for i in $(seq 1 $repeats_num); do
      ./samwsat.py -i ${INSTANCE} -t 300 -n 2 -c 0.999 >> ${out_name}-${instname}-${1}.txt 2> /dev/null
    done
  done
}

for lettr in ${lettrs[@]}; do 
  task $lettr  &
done


