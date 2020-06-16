from googleapiclient.discovery import build
from multiprocessing import Pool
from tqdm import tqdm

import urllib
import argparse
import os
import youtube_dl
import sys
import glob
import pickle

YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

parser = argparse.ArgumentParser()
parser.add_argument('-video_path', default='./videos/')
parser.add_argument('-playlist_id', default='PLQ1C5YbGRe_I4n7uYbScK9jGblO4arePG')
parser.add_argument('-max_result', type=int, default=50)
parser.add_argument('-dev_key', default='AIzaSyD-ogzPhPdoFoYztQqb5Dr7yi4wih5Jr-o')
parser.add_argument('-script_path', default='./vid_script')
parser.add_argument('-lang', default='ko')
parser.add_argument('-multi_proc', type=int, default=1)
# mode setting
parser.add_argument('-mode', default=False)
parser.add_argument('-is_query', type=bool, default=False)
parser.add_argument('-is_download', type=bool, default=False)
args = parser.parse_args()

def main():
    if args.is_resume:
        if not(os.path.exists('./video_idx.txt')):   
            vid_idx_list = fetch_video(args.playlist_id, args.max_result, args.dev_key)
            with open('video_idx.txt', 'w') as wf:
                for vid_idx in vid_idx_list:
                    wf.write(str(vid_idx))
                    wf.write('\n')
            print('[INFO] fetching and writing video index completed.')
    # read fetched video indcies and write video script dictionary
    else:
        # vid_script_dict = {}
        downloaded = 0
        skipped = 0
        vid_indices = list()
        # read and add video idex to list
        with open('video_idx.txt', 'r') as rf:
            print('[INFO] read from video idicies file.')
            for vid_idx in rf:
                vid_idx = vid_idx.rstrip()
                if vid_idx != '':
                    vid_indices.append(vid_idx)
        # download with multiprocessing
        with Pool(processes=args.multi_proc) as p:
            with tqdm(total=len(vid_indices)) as pbar:
                for i, _ in enumerate(p.imap_unordered(download_vid, vid_indices)):
                    pbar.update()
        
        print('[INFO] download completed.')

def fetch_video(playlist_id, max_result, dev_key):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=dev_key)
    result = []
    res = youtube.playlistItems().list(
            part='contentDetails',
            maxResults=max_result,
            playlistId=playlist_id).execute()
    result += res['items']
    while True:
        if len(res['items']) < max_result or 'nextPageToken' not in res:
            break
        next_page_token = res['nextPageToken']
        res = youtube.playlistItems().list(
                part='contentDetails',
                maxResults=max_result,
                playlistId=playlist_id,
                pageToken=next_page_token).execute()
        result += res['items']
        print('[INFO] {} number of videos found'.format(len(result)))

    vid_idx_list = []
    for vid_info in result:
        vid_id = vid_info['contentDetails']['videoId']
        if vid_id is not None:
            vid_idx_list.append(vid_id)

    return vid_idx_list
    
def download_vid(vid_idx):
    ydl_opts = {'format': 'best[height=720, ext=mp4]',
                'writesubtitiels': True,
                'writeautomaticsub': True,
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }],
                'outtmpl': '{}.mp4'.format(os.path.join(args.video_path, vid_idx))
                } # download options
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        download_url = 'https://youtu.be/{}'.format(vid_idx)
        try:
            # download video via given url and this check whether the video already exists or not
            vid_info = ydl.extract_info(download_url, download=True)
            # downlaod subtitle of the video
            if len(vid_info['subtitles']) != 0:
                sub_url = vid_info['subtitles'][args.lang][0]['url']
                urllib.request.urlretrieve(sub_url, '{}.{}.vtt'.format(os.path.join(args.video_path, vid_idx), args.lang))
            elif len(vid_info['automatic_captions']) != 0:
                sub_url = vid_info['automatic_captions'][args.lang][4]['url']
                urllib.request.urlretrieve(sub_url, '{}.{}.vtt'.format(os.path.join(args.video_path, vid_idx), args.lang))
        except Exception as e:
            with open('err_log.txt', 'w') as log:
                log.write('{}\t{}\n'.format(vid_idx, e))
    # return vid_info['description']

def load_data(path):
    with open(path, 'rb') as f:
        data = pickle.load(f)
    return data

def save_data(path, data):
    with open(path, 'wb') as f:
        pickle.dump(data, f)


if __name__ == "__main__":
    main()
    # data = load_data('./vid_script/script.pickle')
    # print('TEST')