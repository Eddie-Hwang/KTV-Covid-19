import argparse
import os, sys
import math
import kss

from webvtt import WebVTT
from utils import load_data, save_data, get_all_doc, SubtitleWrapper, Doc2Vec
from tqdm import tqdm
from multiprocessing import Pool


parser = argparse.ArgumentParser()
parser.add_argument('-script', default='./pickle_files/filtered.pickle')
parser.add_argument('-save_path', default='./pickle_files')
parser.add_argument('-vtt_path', default='./videos')
parser.add_argument('-vtt_lang', default='ko')
parser.add_argument('-sp_duration', type=int, default=2)
parser.add_argument('-threshold', type=int, default=3)
parser.add_argument('-num_proc', type=int, default=1)
parser.add_argument('-use_kkma', type=bool, default=True)
args = parser.parse_args()

def main():
    # process()
    if not(os.path.exists(os.path.join(args.save_path, 'aligned.pickle'))):
        aligned_vtts = process()
    else:
        aligned_vtts = load_data(os.path.join(args.save_path, 'aligned.pickle'))
        write_subtitle(aligned_vtts)

def write_subtitle(aligned_vtt_dict):
    for idx in aligned_vtt_dict:
        subtitle = SubtitleWrapper()
        vtts = aligned_vtt_dict[idx]
        for vtt in vtts:
            subtitle.write_caption(vtt['start'], vtt['end'], 
                                kss.split_sentences(vtt['text']))
        subtitle.save_caption(os.path.join(args.vtt_path, idx))
    print('[INFO] aligned subtitles saved.')

def process():
    scripts = load_data(args.script)
    # get all documents in script
    docs = get_all_doc(scripts)
    # to caculate doc similirity
    doc2vec = Doc2Vec()
    if args.use_kkma:
        if os.path.exists(os.path.join(args.save_path, 'doc_nouns.pickle')):
            doc_nouns = load_data(os.path.join(args.save_path, 'doc_nouns.pickle'))
        else:
            doc_nouns = list()
            for doc in tqdm(docs):
                nouns = doc2vec.get_nouns(doc)
                doc_nouns.append(' '.join(nouns))
            save_data(os.path.join(args.save_path, 'doc_nouns.pickle'), doc_nouns)
            print('[INFO] doc_nouns.pickle saved.')
            sys.exit(-1)
        # fit tf-idf
        doc2vec.fit_doc2vec(doc_nouns)
    else:
        # with Pool(args.num_proc) as p:
        #     doc_nouns = list(tqdm(p.imap(doc2vec.get_nouns, docs), total=len(docs)))
        doc2vec.fit_doc2vec(docs)

    aligned_script = dict()
    success = 0
    for vid_idx in tqdm(scripts):
        try:
            # load script
            script = scripts[vid_idx]
            # script = scripts['mRMYgwIVwUM']
            # load vtt file
            # vtts = load_vtt('mRMYgwIVwUM', args.vtt_lang)
            vtts = load_vtt(vid_idx, args.vtt_lang)
            aligned_vtt = do_alignment(script, vtts, doc2vec)
            aligned_script[vid_idx] = aligned_vtt
            success += 1
        except:
            pass
            
    save_data(os.path.join(args.save_path, 'aligned.pickle'), aligned_script)
    write_scipt_with_time(os.path.join(args.save_path, 'aligned.txt'), aligned_script)
    print('alignment finished. {}/{}'.format(success, len(scripts)))

    return aligned_script

def write_scipt_with_time(path, script_dict):
    with open(path, 'w') as f:
        for idx in script_dict:
            script_list = script_dict[idx]
            f.write('video_index: {}\n'.format(idx))
            for s_dict in script_list:
                f.write('\n{}\nstart:{}\tend:{}\tduration:{}\n'.format(
                    s_dict['text'], s_dict['start'], 
                    s_dict['end'], s_dict['duration']))
            f.write('\n\n')

def do_alignment(script, vtts, doc2vec):
    script_temp = list()
    vtt_temp = list()
    script_iter = False
    vtt_iter = False
    start = ''
    start_in_sec = 0
    aligned_vtt = list()
    for i in range(len(vtts)):
        if script_iter:
            script_temp.append(script.pop(0))
        elif vtt_iter:
            vtt = vtts.pop(0)
            vtt_temp.append(vtt['text'])
        else:
            vtt = vtts.pop(0)
            script_temp.append(script.pop(0))
            vtt_temp.append(vtt['text'])
            start = vtt['start']
            start_in_sec = vtt['start_in_sec']

        # join
        s_text = ' '.join(script_temp)
        vtt_text = ' '.join(vtt_temp)
        # get nouns from each doc
        if args.use_kkma:
            s_text_nouns = ' '.join(doc2vec.get_nouns(s_text))
            vtt_text_nouns = ' '.join(doc2vec.get_nouns(vtt_text))
        else:
            s_text_nouns = ' '.join(doc2vec.get_split(s_text))
            vtt_text_nouns = ' '.join(doc2vec.get_split(vtt_text))
        # get sentence length difference
        # joined_s = ''.join(s_text.split(' '))
        # joined_v = ''.join(vtt_text.split(' '))
        diff_len = len(s_text_nouns.split(' ')) - len(vtt_text_nouns.split(' '))
        # diff_len = len(joined_s) - len(joined_v)
        
        # get score similarity
        score_sim = float(doc2vec.get_similarity(s_text_nouns, vtt_text_nouns))
        # score_penalty = math.exp(abs(diff_len)) * 0.005
        score_penalty = math.exp(abs(diff_len)) * 0.01
        score = score_sim - score_penalty
        
        # if score_penalty > 0.8:
        if not(score > 0.25):
            if diff_len > 0:
                vtt_iter = True
                script_iter = False
            elif diff_len < 0: # iter script text
                script_iter = True
                vtt_iter = False
        else: 
            # append vtt info
            aligned_vtt.append({
                'start': start,
                'end': vtt['end'],
                'duration': vtt['end_in_sec'] - start_in_sec,
                'text': s_text})
            script_iter = False
            vtt_iter = False
            script_temp = list()
            vtt_temp = list()
        if len(script) == 0:
            break
         
    return aligned_vtt  

def load_vtt(vid_idx, lang):
    vtt_file = os.path.join(args.vtt_path, '{}.{}.vtt'.format(vid_idx, lang))
    # vtts = WebVTT.read(vtt_file)
    vtts = SubtitleWrapper().read_caption(vtt_file)
    vtt_list = list()
    for seq, vtt in enumerate(vtts):
        vtt_sents = vtt.text.split('\n')
        vtt_info = {
            'start': vtt.start,
            'end': vtt.end,
            'start_in_sec': vtt.start_in_seconds,
            'end_in_sec': vtt.end_in_seconds,
            'text': vtt_sents[-1], 
        }
        sp_duration = vtt.end_in_seconds - vtt.start_in_seconds
        if sp_duration > args.sp_duration:
            vtt_list.append(vtt_info)

    return vtt_list

if __name__ == '__main__':
    main()