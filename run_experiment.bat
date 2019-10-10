C:/Users/shaig/Miniconda3/envs/dl-project/python.exe ^
 "c:/Users/shaig/Documents/CS_Technion/2019_b/Deep Learning Project/repos/unsupervised_spatial_dc/spatial_two_mics/dnn/experiments/my_experiment.py" ^
 --train "C:\\Users\\shaig\\Documents\\CS_Technion\\2019_b\\Deep Learning Project\\repos\\unsupervised_spatial_dc\\output\\rotor_speech-256-128-128-overfitting" ^
 --test "C:\\Users\\shaig\\Documents\\CS_Technion\\2019_b\\Deep Learning Project\\repos\\unsupervised_spatial_dc\\output\\rotor_speech-256-128-128-overfitting" ^
 --val "C:\\Users\\shaig\\Documents\\CS_Technion\\2019_b\\Deep Learning Project\\repos\\unsupervised_spatial_dc\\output\\rotor_speech-256-128-128-overfitting" ^
 --batch_size 32 ^
 --epochs 100 ^
 --n_layers 2 ^
 --embedding_depth 40 ^
 --hidden_size 1024 ^
 --bidirectional ^
 --training_labels ground_truth ^
<<<<<<< HEAD
 --eval_per 1 ^
 --learning_rate 0.001 ^
 --dropout 0.0 ^
=======
 --eval_per 5 ^
 --learning_rate 0.001 ^
 --dropout 0.1 ^
>>>>>>> fb0481f1ea4d09fa7737d8233068b5463245a5ca
 --early_stop_patience 7 ^
 --lr_patience 3 ^
 --lr_gamma_decay 0.2 ^
 --save_best 5 ^
 --num_workers 5 ^
 --experiment_name "overfitting_experiment"