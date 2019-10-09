import os
import sys

root_dir = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    '../../')
sys.path.insert(0, root_dir)

from spatial_two_mics.data_generator.my_dregon_dataset_creator_and_storage import create_dataset

# create small but significant dataset
create_dataset(n_train=256, n_test=128, n_val=128, types_to_mix=['rotor', 'speech'], output_dir='output')
