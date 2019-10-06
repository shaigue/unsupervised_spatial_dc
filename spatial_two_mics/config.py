import os

os.environ["CUDA_VISIBLE_DEVICES"] = "1,2,3"

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIMIT_PATH = "/mnt/data/Speech/timit-wav"
# my dataset dir
DATASETS_DIR = "C:\\Users\\shaig\\Documents\\CS_Technion\\2019_b\\Deep Learning Project\\repos\\unsupervised_spatial_dc\\tf_samples"
# DATASETS_DIR = "/mnt/nvme/spatial_two_mics_data/"
MODELS_DIR = "/mnt/nvme/spatial_two_mics_models/"
RESULTS_DIR = "/mnt/nvme/spatial_two_mics_results/"
MODELS_RAW_PHASE_DIR = "/mnt/nvme/spatial_two_mics_models_raw_phase/"
MODELS_GROUND_TRUTH = "/mnt/nvme/spatial_two_mics_models_ground_truth/"
FINAL_RESULTS_DIR = "/mnt/nvme/spatial_two_mics_final_eval_results/"

