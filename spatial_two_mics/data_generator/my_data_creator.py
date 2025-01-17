"""!
@brief A dataset creation which is used in order to combine the
mixtures form the dataset and also store them inside a specified folder

@author Efthymios Tzinis {etzinis2@illinois.edu}
@copyright University of Illinois at Urbana Champaign
"""

import argparse
import os
import sys
import numpy as np
from random import shuffle
from pprint import pprint
from sklearn.externals import joblib

possible_combinations = [['rotor', 'chirps'], ['rotor', 'speech'], ['rotor', 'whitenoise'], ['speech', 'speech'],
                         ['chirps', 'rotor'], ['speech', 'rotor'], ['whitenoise', 'rotor']]

available_types = ['rotor', 'chirps', 'speech', 'whitenoise']

root_dir = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    '../../')
sys.path.insert(0, root_dir)

import spatial_two_mics.data_loaders.my_dregon as dregon_loader
import spatial_two_mics.data_generator.source_position_generator as \
    positions_generator
import spatial_two_mics.labels_inference.tf_label_estimator as \
    mask_estimator
import spatial_two_mics.utils.audio_mixture_constructor as \
            mix_constructor
import spatial_two_mics.utils.progress_display as progress_display


class ArtificialDatasetCreator(object):
    """
    This is a general compatible class for creating Artificial
    mixtures with positions of the different sources.
    """
    def __init__(self,
                 audio_dataset_name="dregon"):
        if audio_dataset_name.lower() == "dregon":
            self.data_loader = dregon_loader.MyDregonLoader()
            self.fs = 16000
        else:
            raise NotImplementedError("Dataset Loader: {} is not yet "
                  "implemented.".format(audio_dataset_name))


class RandomCombinations(ArtificialDatasetCreator):
    def __init__(self,
                 audio_dataset_name="dregon",
                 types=None,
                 mixture_distribution=None,
                 create_val_set=False,
                 subset_of_samples='train',
                 min_duration=2.0,
                 convolution_offset=2000,
                 return_phase_diff=True):

        super(RandomCombinations,
              self).__init__(audio_dataset_name=audio_dataset_name)

        self.mixture_distribution = mixture_distribution
        self.audio_dataset_name = audio_dataset_name
        self.data_dic = self.data_loader.load()
        self.subset_of_samples = subset_of_samples

        self.types = types
        valid_types = [(t in available_types)
                         for t in self.types]
        assert valid_types, ('Valid genders for mixtures are f and m')

        self.available_sound_samples = self.get_available_samples(
                                        subset_of_samples)
        print("All Available Samples are {}".format(
            len(self.available_sound_samples)))

        ## TODO:

        if create_val_set:
            n_available = len(self.available_sound_samples)
            self.val_samples = np.random.choice(self.available_sound_samples,
                                                 int(n_available/2),
                                                 replace=False)
        else:
            self.val_samples = []

        self.available_sound_samples = [s for s in self.available_sound_samples
                                        if s not in self.val_samples]

        self.min_samples = int(min_duration * self.fs)
        self.convolution_offset = convolution_offset
        self.return_phase_diff = return_phase_diff

    def get_available_samples(self,
                               subset):
        try:
            existing_types = sorted(list(self.data_dic[subset].keys()))
        except KeyError:
            print("Subset: {} not available".format(subset))
            raise KeyError

        valid_samples = []
        for t in existing_types:
            if t in self.types:
                for sample in self.data_dic[subset][t]:
                    valid_samples.append(sample)

        return valid_samples

    @staticmethod
    def random_combinations(iterable, r):
        iter_len = len(iterable)
        max_combs = 1
        for i in np.arange(r):
            max_combs *= (iter_len - i + 1) / (i + 1)

        already_seen = set()
        c = 0
        while c < max_combs:
            indexes = sorted(np.random.choice(iter_len, r))
            str_indexes = str(indexes)
            if str_indexes in already_seen:
                continue
            else:
                already_seen.add(str_indexes)

            c += 1
            yield [iterable[i] for i in indexes]

    def get_only_valid_mixture_combinations(self,
                                            possible_sources,
                                            samples_dic,
                                            n_mixed_sources=2,
                                            n_mixtures=0):

        mixtures_generator = self.random_combinations(possible_sources, n_mixed_sources)

        if n_mixtures <= 0:
            print("All available mixtures that can be generated would "
                  " be: {}!".format(len(list(mixtures_generator))))
            print("Please Select a number of mixtures > 0")

        valid_mixtures = []

        while len(valid_mixtures) < n_mixtures:
            possible_comb = next(mixtures_generator)
            types_in_mix = [x['type'] for x in possible_comb]
            if types_in_mix not in possible_combinations:
                continue
            # not a valid type mix

            # we do not want the same speaker twice
            # speaker_set = set([x['speaker_id'] for x in possible_comb])
            # if len(speaker_set) < len(possible_comb):
            #     continue

            # check whether all the signals have the appropriate
            # duration
            signals = [(len(self.get_wav(samples_dic, source_info))
                        >= self.min_samples + self.convolution_offset)
                       for source_info in possible_comb]
            if not all(signals):
                continue

            valid_mixtures.append(possible_comb)

        return valid_mixtures

    @staticmethod
    def get_wav(samples_dic,
                source_info):
        return samples_dic[source_info['speaker_id']][
               'sentences'][source_info['sentence_id']]['wav']

    @staticmethod
    def get_wav_path(speakers_dic,
                source_info):
        return speakers_dic[source_info['speaker_id']][
            'sentences'][source_info['sentence_id']]['path']

    def construct_mixture_info(self,
                               speakers_dic,
                               combination_info,
                               positions):
        """
        :param positions should be able to return:
               'amplitudes': array([0.28292362, 0.08583346, 0.63124292]),
               'd_thetas': array([1.37373734, 1.76785531]),
               'distances': {'m1m1': 0.0,
                             'm1m2': 0.03,
                             'm1s1': 3.015, ...
                             's3s3': 0.0},
               'taus': array([ 1.456332, -1.243543,  0]),
               'thetas': array([0.        , 1.37373734, 3.14159265]),
               'xy_positons': array([[ 3.00000000e+00, 0.00000000e+00],
                   [ 5.87358252e-01,  2.94193988e+00],
                   [-3.00000000e+00,  3.67394040e-16]])}

        :param speakers_dic should be able to return a dic like this:
                'speaker_id_i': {
                    'dialect': which dialect the speaker belongs to,
                    'gender': f or m,
                    'sentences': {
                        'sentence_id_j': {
                            'wav': wav_on_a_numpy_matrix,
                            'sr': Fs in Hz integer,
                            'path': PAth of the located wav
                        }
                    }
                }

        :param combination_info should be in the following format:
           [{'gender': 'm', 'sentence_id': 'sx298', 'speaker_id': 'mctt0'},
            {'gender': 'm', 'sentence_id': 'sx364', 'speaker_id': 'mrjs0'},
           {'gender': 'f', 'sentence_id': 'sx369', 'speaker_id': 'fgjd0'}]

        :return condensed mixture information block:
        {
            'postions':postions (argument)
            'sources_ids':
            [       {
                        'gender': combination_info.gender
                        'sentence_id': combination_info.sentence_id
                        'speaker_id': combination_info.speaker_id
                        'wav_path': the wav_path for the file
                    } ... ]
        }
        """

        new_combs_info = combination_info.copy()

        for comb in new_combs_info:
            comb.update({'wav_path':
                         self.get_wav_path(speakers_dic,
                                           comb)})

        return {'positions': positions,
                'sources_ids': new_combs_info}

    def gather_mixtures_information(self,
                                    samples,
                                    n_sources_in_mix=2,
                                    n_mixtures=0):
        """
        speakers_dic should be able to return a dic like this:
            'speaker_id_i': {
                'dialect': which dialect the speaker belongs to,
                'gender': f or m,
                'sentences': {
                    'sentence_id_j': {
                        'wav': wav_on_a_numpy_matrix,
                        'sr': Fs in Hz integer,
                        'path': PAth of the located wav
                    }
                }
            }

        combination_info should be in the following format:
           [{'gender': 'm', 'sentence_id': 'sx298', 'speaker_id': 'mctt0'},
            {'gender': 'm', 'sentence_id': 'sx364', 'speaker_id': 'mrjs0'},
           {'gender': 'f', 'sentence_id': 'sx369', 'speaker_id': 'fgjd0'}]

        """
        samples_dic = self.available_sound_samples
        possible_sources = []
        for sample in samples:
            t = samples_dic[sample]['type']
            possible_sources += [{'sample_id': sample[], 'type': t}]

        shuffle(possible_sources)

        valid_combinations = self.get_only_valid_mixture_combinations(
            possible_sources,
            samples_dic,
            n_mixed_sources=n_sources_in_mix,
            n_mixtures=n_mixtures)

        random_positioner = positions_generator.RandomCirclePositioner()

        mixtures_info = [self.construct_mixture_info(
            speakers_dic,
            combination,
            random_positioner.get_sources_locations(len(
                combination)))
            for combination in valid_combinations]

        return mixtures_info

    def update_label_masks_and_info(self,
                                    mixture_info,
                                    mixture_creator=None,
                                    ground_truth_estimator=None,
                                    soft_label_estimator=None,
                                    output_dir=None):
        name = [s_id['speaker_id'] + '-' + s_id['sentence_id']
                for s_id in mixture_info['sources_ids']]
        name = '_'.join(name)
        data = {}

        tf_mixture = mixture_creator.construct_mixture(mixture_info)
        gt_mask = ground_truth_estimator.infer_mixture_labels(tf_mixture)
        data['ground_truth_mask'] = gt_mask
        data['real_tfs'] = np.real(tf_mixture['m1_tf'])
        data['imag_tfs'] = np.imag(tf_mixture['m1_tf'])
        data['wavs'] = tf_mixture['sources_raw']
        if soft_label_estimator is not None:
            duet_mask, raw_phase_diff = \
                soft_label_estimator.infer_mixture_labels(tf_mixture)
            normalized_raw_phase = np.clip(raw_phase_diff, -2., 2.)
            normalized_raw_phase -= normalized_raw_phase.mean()
            normalized_raw_phase /= normalized_raw_phase.std() + 10e-12
            data['soft_labeled_mask'] = duet_mask
            data['raw_phase_diff'] = np.asarray(normalized_raw_phase,
                                                dtype=np.float32)

        folder_path = os.path.join(output_dir, name)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        # now just go over all the appropriate elements of mix info
        # dictionary and save them in separate files according to
        # their need
        for k, v in data.items():
            file_path = os.path.join(folder_path, k)
            joblib.dump(v, file_path, compress=0)
        return 1

    def combination_process_wrapper(self,
                                    output_dir=None,
                                    ground_truth_estimator=None,
                                    mixture_creator=None,
                                    soft_label_estimator=None):
        return lambda mix_info: \
               self.update_label_masks_and_info(
                    mix_info,
                    output_dir=output_dir,
                    ground_truth_estimator=ground_truth_estimator,
                    mixture_creator=mixture_creator,
                    soft_label_estimator=soft_label_estimator)

    def create_dataset_name(self,
                            n_samples=None,
                            n_sources=None,
                            force_delays=None):
        if force_delays is None:
            force_delays = ['random_', '_delays']
        dataset_name = '{}_{}_{}_{}_{}'.format(
            self.audio_dataset_name,
            '_'.join(map(str, n_samples)),
            n_sources,
            ''.join(t[0] for t in sorted(self.types)),
            'taus'.join(map(str, force_delays)))
        return dataset_name

    def get_mixture_combinations(self,
                                 samples,
                                 output_dir=None,
                                 n_sources_in_mix=2,
                                 n_mixtures=0,
                                 force_delays=None,
                                 get_only_ground_truth=False):

        mixtures_info = self.gather_mixtures_information(
                        samples,
                        n_sources_in_mix=n_sources_in_mix,
                        n_mixtures=n_mixtures)

        print("Created the combinations of all the speakers and "
              "ready to process each mixture separately!")

        mixture_creator = mix_constructor.AudioMixtureConstructor(
            n_fft=512, win_len=512, hop_len=128, mixture_duration=2.0,
            force_delays=force_delays)

        gt_estimator = mask_estimator.TFMaskEstimator(
                       inference_method='Ground_truth')

        if get_only_ground_truth:
            duet_estimator = None
        else:
            duet_estimator = mask_estimator.TFMaskEstimator(
                             inference_method='duet_Kmeans',
                             return_duet_raw_features=self.return_phase_diff)

        mix_info_func = self.combination_process_wrapper(
                             output_dir=output_dir,
                             ground_truth_estimator=gt_estimator,
                             mixture_creator=mixture_creator,
                             soft_label_estimator=duet_estimator)
        n_mixes = str(len(mixtures_info))
        mixtures_info = progress_display.progress_bar_wrapper(
                                         mix_info_func,
                                         mixtures_info,
                                         message='Creating '
                                                  +n_mixes+
                                                  ' Mixtures...')

        print("Successfully stored {} mixtures".format(
              sum(mixtures_info)))

    def create_and_store_all_mixtures(self,
                                      n_sources_in_mix=2,
                                      n_mixtures=0,
                                      force_delays=None,
                                      get_only_ground_truth=False,
                                      output_dir=None,
                                      selected_partition=None):

        samples = self.available_sound_samples
        if selected_partition is None:
            selected_partition = self.subset_of_samples
        else:
            if selected_partition == 'val':
                speakers = self.val_samples
            elif selected_partition == 'test':
                speakers = self.available_sound_samples
            else:
                raise ValueError("No valid partition named: {}".format(
                      selected_partition))

        storage_path = os.path.join(output_dir,
                                    self.create_dataset_name(
                                    n_samples=self.mixture_distribution,
                                    n_sources=n_sources_in_mix,
                                    force_delays=force_delays),
                                    selected_partition)

        self.get_mixture_combinations(
        samples,
        n_sources_in_mix=n_sources_in_mix,
        n_mixtures=n_mixtures,
        force_delays=force_delays,
        get_only_ground_truth=
        get_only_ground_truth,
        output_dir=storage_path)


def generate_dataset(args):
    n_train, n_test, n_val = args.n_samples

    timit_mixture_creator = RandomCombinations(
        audio_dataset_name=args.dataset,
        types=args.genders,
        mixture_distribution=args.n_samples,
        subset_of_samples='train',
        create_val_set=False)

    timit_mixture_creator.create_and_store_all_mixtures(
                            n_sources_in_mix=args.n_sources,
                            n_mixtures=n_train,
                            output_dir=args.output_path,
                            force_delays=args.force_delays)

    timit_mixture_creator = RandomCombinations(
        audio_dataset_name=args.dataset,
        types=args.genders,
        mixture_distribution=args.n_samples,
        subset_of_samples='test',
        create_val_set=True)

    timit_mixture_creator.create_and_store_all_mixtures(
        n_sources_in_mix=args.n_sources,
        n_mixtures=n_test,
        output_dir=args.output_path,
        selected_partition='test',
        force_delays=args.force_delays)

    timit_mixture_creator.create_and_store_all_mixtures(
        n_sources_in_mix=args.n_sources,
        n_mixtures=n_val,
        selected_partition='val',
        output_dir=args.output_path,
        force_delays=args.force_delays)


def get_args():
    """! Command line parser """
    parser = argparse.ArgumentParser(description='Mixture dataset '
                                                 'creator')
    parser.add_argument("--dataset", type=str,
                        help="Dataset name", default="dregon")
    parser.add_argument("--n_sources", type=int,
                        help="How many sources in each mix", default=2)
    parser.add_argument("--n_samples", type=int, nargs='+',
                        help="How many samples do u want to be "
                             "created",
                        default=[1,1,1])
    parser.add_argument("--genders", type=str, nargs='+',
                        help="Genders that will correspond to the "
                             "genders in the mixtures",
                        default=['M', 'F'])
    parser.add_argument("-o", "--output_path", type=str,
                        help="""The path that the resulting dataset 
                        would be stored. If the folder does not 
                        exist it will be created as well as its 
                        child folders train or test and val if it is 
                        selected""",
                        required=True)
    parser.add_argument("-f", "--force_delays", nargs='+', type=int,
                        help="""Whether you want to force integer 
                        delays of +- 1 in the sources e.g.""",
                        default=None)
    parser.add_argument('--val_set', action="store_true",
                        help='Force to create a separate val folder '
                             'with the same amount of the mixtures as '
                             'the initial test/train folder but using '
                             'half of the available speakers')
    return parser.parse_args()


if __name__ == "__main__":
    args = get_args()
    generate_dataset(args)

