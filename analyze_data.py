import csv
import os
from functools import partial

from acousticsim.main import acoustic_similarity_mapping

from acousticsim.helper import get_vowel_points
from acousticsim.praat.wrapper import (to_pitch_praat, to_formants_praat,
                                        to_intensity_praat, to_mfcc_praat)

from acousticsim.distance.point import point_distance, euclidean
from acousticsim.distance.dct import dct_distance
from acousticsim.distance.dtw import dtw_distance
from acousticsim.distance.xcorr import xcorr_distance


praat_path = r'C:\Users\michael\Documents\Praat\praatcon.exe'

data_dir = r'C:\Users\michael\Documents\Data\ATI_new'

model_dir = os.path.join(data_dir, 'Models')

shadower_dir = os.path.join(data_dir, 'Shadowers')

female_models = os.listdir(os.path.join(model_dir,'Female'))

male_models = os.listdir(os.path.join(model_dir,'Male'))

female_shadowers = os.listdir(os.path.join(shadower_dir,'Female'))

male_shadowers = os.listdir(os.path.join(shadower_dir,'Male'))

## Representations
# MFCC (acousticsim)
# MFCC (Praat)
# Formants (Praat)
# Intensity (Praat)
# Pitch (Praat)
# AmpEnvs (acousticsim)

## Distance functions
# DTW
# XCorr
# DCT
# Vowel midpoint
# Vowel third

def callback(*value):
    print(*value)

praat_mfcc = partial(to_mfcc_praat, praat_path )

praat_formants = partial(to_formants_praat, praat_path)

praat_intensity = partial(to_intensity_praat, praat_path )

praat_pitch = partial(to_pitch_praat, praat_path )

def midpoint_distance(rep_one, rep_two):
    base, _ = os.path.splitext(rep_one._filepath)
    one_textgrid = base + '.TextGrid'
    begin,end = get_vowel_points(one_textgrid, tier_name = 'Vowel', vowel_label = 'V')
    if begin is None or end is None:
        print(one_textgrid)
    point_one = begin + ((end - begin)/2)

    base, _ = os.path.splitext(rep_two._filepath)
    two_textgrid = base + '.TextGrid'
    begin,end = get_vowel_points(two_textgrid, tier_name = 'Vowel', vowel_label = 'V')
    if begin is None or end is None:
        print(one_textgrid)
    point_two = begin + ((end - begin)/2)
    return point_distance(rep_one, rep_two, point_one, point_two)

def third_distance(rep_one, rep_two):
    base, _ = os.path.splitext(rep_one._filepath)
    one_textgrid = base + '.TextGrid'
    begin,end = get_vowel_points(one_textgrid, tier_name = 'Vowel', vowel_label = 'V')
    point_one = begin + ((end - begin)/3)

    base, _ = os.path.splitext(rep_two._filepath)
    two_textgrid = base + '.TextGrid'
    begin,end = get_vowel_points(two_textgrid, tier_name = 'Vowel', vowel_label = 'V')
    point_two = begin + ((end - begin)/3)
    return point_distance(rep_one, rep_two, point_one, point_two)

def vowel_dist(dist_func, rep_one, rep_two):
    base, _ = os.path.splitext(rep_one._filepath)
    one_textgrid = base + '.TextGrid'
    one_begin,one_end = get_vowel_points(one_textgrid, tier_name = 'Vowel', vowel_label = 'V')

    base, _ = os.path.splitext(rep_two._filepath)
    two_textgrid = base + '.TextGrid'
    two_begin,two_end = get_vowel_points(two_textgrid, tier_name = 'Vowel', vowel_label = 'V')

    return dist_func(rep_one[one_begin, one_end], rep_two[two_begin, two_end])

def duration_distance(rep_one, rep_two):
    base, _ = os.path.splitext(rep_one._filepath)
    one_textgrid = base + '.TextGrid'
    one_begin,one_end = get_vowel_points(one_textgrid, tier_name = 'Vowel', vowel_label = 'V')
    if one_begin is None:
        one_begin = 0
    if one_end is None:
        one_end = rep_one._duration
    one_durations = [one_begin, one_end - one_begin, rep_one._duration - one_end]

    base, _ = os.path.splitext(rep_two._filepath)
    two_textgrid = base + '.TextGrid'
    two_begin,two_end = get_vowel_points(two_textgrid, tier_name = 'Vowel', vowel_label = 'V')
    if two_begin is None:
        two_begin = 0
    if two_end is None:
        two_end = rep_two._duration
    two_durations = [two_begin, two_end - two_begin, rep_two._duration - two_end]

    return euclidean(one_durations, two_durations)

vowel_dtw = partial(vowel_dist,dtw_distance)
vowel_dct = partial(vowel_dist,dct_distance)
vowel_xcorr = partial(vowel_dist,xcorr_distance)

def load_axb():
    path_mapping = list()
    with open(os.path.join(data_dir,'axb.txt'),'r') as f:
        reader = csv.DictReader(f, delimiter = '\t')
        for line in reader:
            shadower = line['Shadower'][-3:]
            model = line['Model'][-3:]
            word = line['Word']
            if model in female_models:
                model_path = os.path.join(model_dir, 'Female',model, '{}_{}.wav'.format(model,word))
            else:
                model_path = os.path.join(model_dir, 'Male',model, '{}_{}.wav'.format(model,word))
            if shadower in female_shadowers:
                baseline_path = os.path.join(shadower_dir, 'Female',shadower, '{}_{}_baseline.wav'.format(shadower,word))
                shadowed_path = os.path.join(shadower_dir, 'Female',shadower, '{}_{}_shadowing{}.wav'.format(shadower,word, model))
            else:
                baseline_path = os.path.join(shadower_dir, 'Male',shadower, '{}_{}_baseline.wav'.format(shadower,word))
                shadowed_path = os.path.join(shadower_dir, 'Male',shadower, '{}_{}_shadowing{}.wav'.format(shadower,word, model))
            path_mapping.append((baseline_path, model_path, shadowed_path))
    return list(set(path_mapping))

def output_acousticsim(path_mapping, output, output_filename):
    with open(output_filename, 'w') as f:
        writer = csv.writer(f, delimiter = '\t')
        writer.writerow(['Shadower', 'Model', 'Word', 'BaseToModel', 'ShadToModel'])
        for pm in path_mapping:
            baseline_prod = os.path.basename(pm[0])
            model_prod = os.path.basename(pm[1])
            shad_prod = os.path.basename(pm[2])
            shadower = shad_prod[:3]
            model,ext = os.path.splitext(model_prod)
            model, word = model.split('_')
            writer.writerow([shadower, model, word, output[(baseline_prod,model_prod)],
                                                output[(shad_prod,model_prod)]])

def get_mfcc_dtw(path_mapping):
    asim = acoustic_similarity_mapping(path_mapping, rep = 'mfcc',
                                    match_function = 'dtw', use_multi=True,
                                    num_cores = 6)
    return asim

def get_mfcc_vowel_mid(path_mapping):

    asim = acoustic_similarity_mapping(path_mapping, rep = 'mfcc',
                                    match_function = midpoint_distance, use_multi=True,
                                    num_cores = 6, call_back = callback)
    return asim

def convert_path_mapping(path_mapping):
    new_path_mapping = set()
    for mapping in path_mapping:
        new_path_mapping.add((mapping[0],mapping[1]))
        new_path_mapping.add((mapping[2],mapping[1]))
    return list(new_path_mapping)

def calc_asim(path_mapping, rep, match_func, cache = None):
    asim, cache = acoustic_similarity_mapping(path_mapping, rep = rep,
                                    match_function = match_func, use_multi=True,
                                    num_cores = 4, cache = cache, return_rep = True)
    return asim, cache

if __name__ == '__main__':

    rep_dict = {'mfcc': 'mfcc',
                'mfcc_praat':praat_mfcc,
                'ampenv': 'envelopes',
                'pitch_praat': praat_pitch,
                'intensity_praat': praat_intensity,
                'formants_praat': praat_formants
                }
    dist_dict = {'dtw': 'dtw',
                'dct': 'dct',
                'xcorr': 'xcorr',
                'dtw_vowel': vowel_dtw,
                'dct_vowel': vowel_dct,
                'xcorr_vowel': vowel_xcorr,
                'midpoint': midpoint_distance,
                'third': third_distance}

    path_mapping = load_axb()
    for_asim = convert_path_mapping(path_mapping)
    for k,v in rep_dict.items():
        cache = None
        for k2,v2 in dist_dict.items():
            if os.path.exists('{}_{}.txt'.format(k, k2)):
                continue
            print(k, k2)
            asim, cache = calc_asim(for_asim, v, v2, cache = cache)
            output_acousticsim(path_mapping, asim, '{}_{}.txt'.format(k, k2))
    #Duration distance
    asim, cache = calc_asim(for_asim, v, duration_distance, cache = cache)
    output_acousticsim(path_mapping, asim, 'segmental_duration.txt')
