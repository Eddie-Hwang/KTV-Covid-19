import argparse
import glob
import os
import kss

from utils import load_data, save_data

parser = argparse.ArgumentParser()
parser.add_argument('-script', default='./pickle_files/script.pickle')
parser.add_argument('-save_path', default='./pickle_files')
args = parser.parse_args()

def main():
    scripts = load_data(args.script)
    filtered_scripts = dict()
    total_num_sent = 0 
    for vid_idx in scripts:
        script = preprocessing(scripts[vid_idx])
        # script = preprocessing(scripts['dZIZ9DGRCaI'])
        if len(script) > 10:   
            total_num_sent += len(script) 
            filtered_scripts[vid_idx] = script
    max_len_idx = max(filtered_scripts, key=lambda k: len(filtered_scripts[k]))
    min_len_idx = min(filtered_scripts, key=lambda k: len(filtered_scripts[k]))
     
    print('[INFO] total number of script available: {}/{}'.format(len(filtered_scripts), len(scripts)))
    print('[INFO] total numebr of sentences: {}'.format(total_num_sent))
    print('[INFO] max length of script: {} ({})'.format(max_len_idx, len(filtered_scripts[max_len_idx])))
    print('[INFO] min length of script: {} ({})'.format(min_len_idx, len(filtered_scripts[min_len_idx])))
    
    if not(os.path.exists(args.save_path)):
        os.mkdir(args.save_path)
    save_data(os.path.join(args.save_path, 'filtered.pickle'), filtered_scripts)
    write_script(os.path.join(args.save_path, 'processed_script.txt'), filtered_scripts)

def write_script(path, script_dict):
    with open(path, 'w') as f:
        for idx in script_dict:
            script_list = script_dict[idx]
            f.write('vid_idx: {}\n'.format(idx))
            for sent in script_list:
                f.write(sent + '\n')
            f.write('\n\n')

def preprocessing(script):
    lines = script.split('\n')
    filtered_lines = list()
    for line in lines:
        condition_1 = (line != '')
        condition_2 = (line.startswith('✔') or line.startswith('▶') or line.startswith('📌') or line.startswith('#') or line.startswith('📡') or line.startswith('http') or line.startswith('-') or line.startswith('[')) == False
        # condition_3 = line.startswith('○브리핑 전문○')
        # check actual briefing part
        # if condition_3:
        #     is_briefing = True
        if condition_1 and condition_2:
            sents = kss.split_sentences(line)
            for sent in sents:   
                words = sent.split(' ')
                word_list = list()
                for word in words:
                    if word.find('○') == -1 and word.find('●') == -1:
                        word_list.append(word)
                sent = ' '.join(word_list)
                sent = sent.strip()
                if sent != '' and sent != '브리핑 전문':
                    filtered_lines.append(sent)
    
    return filtered_lines

if __name__ == '__main__':
    main()