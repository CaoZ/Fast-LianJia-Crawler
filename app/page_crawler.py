import logging
from datetime import datetime
from pathlib import Path
from queue import Queue
from threading import Thread

import requests

from config import config
from lian_jia.city import City
from lian_jia.community import Community
from util.orm import Session

DATA_DIR = Path(__file__).parent.joinpath('../data/').resolve()
DATA_DIR.mkdir(exist_ok=True)

_counts = {
    'total': 0,
    'completed': 0,
    'failed': 0
}


def fetch_page(city: City, community_id):
    """
    抓取小区详情页面并保存.
    :raise 若出现错误将抛出对应异常.
    """
    url = f'https://m.lianjia.com/{city.abbr}/xiaoqu/{community_id}/pinzhi'

    r = requests.get(url)
    r.raise_for_status()

    save_file = DATA_DIR.joinpath(f'{community_id}.html')
    save_file.write_bytes(r.content)


def do_fetch(city: City, communities_queue: Queue):
    # 抓取, 直到没东西可抓

    # http://docs.sqlalchemy.org/en/latest/orm/session_basics.html#is-the-session-thread-safe
    db_session = Session()

    while not communities_queue.empty():

        a_community = communities_queue.get()

        try:
            fetch_page(city, a_community.id)
            a_community.page_fetched_at = datetime.now()
        except Exception as e:
            _counts['failed'] += 1
            logging.error(f'# 抓取失败, community_id={a_community.id}, message="{e}"')

        else:
            db_session.add(a_community)
            db_session.commit()

        _counts['completed'] += 1

        if _counts['completed'] % 10 == 0:
            count_remaining = _counts["total"] - _counts["completed"]
            logging.info(f'进度={_counts["completed"]}/{_counts["total"]}, 剩余={count_remaining}')

        communities_queue.task_done()

    db_session.close()


def fetch_all_pages(city_id, threads_num=10):
    db_session = Session()

    city = db_session.query(City).filter(
        City.id == city_id
    ).first()

    if not city:
        return logging.error('请先获取目标城市信息后再进行抓取~')

    all_communities = db_session.query(Community).filter(
        Community.city_id == city_id,
        Community.page_fetched_at == None
    ).all()

    db_session.close()

    communities_queue = Queue()

    for a_community in all_communities:
        communities_queue.put(a_community)

    _counts['total'] = len(all_communities)

    logging.info(f'city_id={city.id}, city_name={city.name}, 待抓取={_counts["total"]}')
    logging.info('抓取中...')

    for _ in range(threads_num):
        worker = Thread(target=do_fetch, args=[city, communities_queue])
        worker.start()

    communities_queue.join()

    logging.info('已全部抓取完成.')


def main():
    fetch_all_pages(config.city_id, threads_num=10)


if __name__ == '__main__':
    main()
