import json
import os
import time
from pathlib import Path
import dateutil.parser

from tqdm import tqdm
from requests_oauthlib import OAuth1Session


this_directory = Path(os.path.dirname(os.path.abspath(__file__)))

class Searcher(object):
    def __init__(self, config_json_file=None):
        if config_json_file is None:
            config_json_file = this_directory / "config.json"
        with open(str(config_json_file), 'r') as f:
            self.config = json.load(f)

    def search(self, q, count):
        """
        ----
        Args:
            q (str):
            count (int):
        Returns:
            {
                texts (list of str)
                dates (list of datetime.datetime)
            }

        Caution:
            ceil(count // 100) 回くらい API を叩きます．

        # パラメータ解説：https://developer.twitter.com/en/docs/tweets/search/api-reference/get-search-tweets
        """
        twitter = OAuth1Session(
            self.config["consumer_api_key"],
            self.config["consumer_api_secret_key"],
            self.config["access_token"],
            self.config["access_token_secret"],
        )
        url = 'https://api.twitter.com/1.1/search/tweets.json?tweet_mode=extended'

        stats = []
        with tqdm(total=count) as pbar:
            while True:
                params = {
                    'count': min(100, count),  # 取得するtweet数 最大100までらしい
                    'q': q,  # 検索キーワード
                    'lang': 'ja',
                    'result_type': 'recent',
                }
                if len(stats) > 0:
                    params['max_id'] = str(int(stats[-1]['id']) - 1)
                    # この値ちょうどのツイートは含まれてしまうようなので1を引く．
                res = twitter.get(url, params=params)
                res.raise_for_status()
                res.encoding = 'utf-8'
                res_obj = json.loads(res.text)
                stats += res_obj['statuses']
                pbar.update(len(res_obj['statuses']))
                if len(stats) >= count or len(res_obj['statuses']) == 0:
                    break
                time.sleep(2.0)

        # 公式RTは取り除く
        stats = [st for st in stats if 'retweeted_status' not in st]

        texts = [st['full_text'] for st in stats]
        dates = [dateutil.parser.parse(st['created_at']) for st in stats]
        return {
            "texts": texts,
            "dates": dates
        }


if __name__ == '__main__':
    searcher = Searcher()
    print(searcher.search("AtCoder", 3))
