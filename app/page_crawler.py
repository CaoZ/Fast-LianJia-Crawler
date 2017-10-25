import logging
from datetime import datetime
from pathlib import Path

import requests
from sqlalchemy import func

from config import config
from lian_jia.community import Community
from util.orm import Session

DATA_DIR = Path(__file__).parent.joinpath('../data/').resolve()
DATA_DIR.mkdir(exist_ok=True)


def fetch_page(community_id):
    """
    抓取小区详情页面并保存.
    :raise 若出现错误将抛出对应异常.
    """
    url = f'https://m.lianjia.com/bj/xiaoqu/{community_id}/pinzhi'

    r = requests.get(url)
    r.raise_for_status()

    save_file = DATA_DIR.joinpath(f'{community_id}.html')
    save_file.write_bytes(r.content)


def fetch_all_pages(city_id):
    db_session = Session()

    total_count = db_session.query(func.count('*')).filter(
        Community.city_id == city_id,
        Community.page_fetched_at == None
    ).scalar()

    total_got = 0

    logging.info(f'city_id={city_id}, 待抓取={total_count}')

    while True:
        per_size = 5

        # 每次随机取若干个未抓取过的小区, 以便可以开启多个进程同时抓取互不干扰
        communities = db_session.query(Community).filter(
            Community.city_id == city_id,
            Community.page_fetched_at == None
        ).order_by(func.random())[:per_size]

        if not communities:
            break

        logging.info('抓取中...')

        for a_community in communities:
            try:
                fetch_page(a_community.id)
                a_community.page_fetched_at = datetime.now()
                db_session.commit()
            except Exception as e:
                logging.error(f'# 抓取失败, community_id={a_community.id}, message="{e}"')

        total_got += len(communities)

        # 若启动多个进程进行抓取, 显示的剩余数量就不准确了, 不过是小问题, 不慌...
        logging.info(f'进度={total_got}/{total_count}, 剩余={total_count - total_got}')

    logging.info('已全部抓取完成.')
    db_session.close()


def main():
    fetch_all_pages(config.city_id)


if __name__ == '__main__':
    main()
