import logging
import os
from datetime import datetime, timedelta

import requests

import util
from config import config
from lian_jia import City, District, BizCircle, Community
from util.orm import Session

CITY_ID = 110000
# 行政区名称 id 映射, 如: 海淀 -> 23008618
DISTRICT_MAP = {}


def main():
    update_city()
    update_communities()


def update_city():
    """
    初始化/更新城市信息
    """
    logging.info('初始化/更新城市信息... city_id={}'.format(CITY_ID))

    city_info = get_city()
    city = City(city_info)

    db_session = Session()
    db_session.merge(city)

    for district_info in city_info['district']:
        district = District(city.id, district_info)
        logging.info('城市={}, 区域={}, 商圈数={}'.format(city.name, district.name, district.biz_circles_count))
        DISTRICT_MAP[district.name] = district.id
        db_session.merge(district)

        for biz_circle_info in district_info['bizcircle']:
            biz_circle = db_session.query(BizCircle).filter(
                BizCircle.id == int(biz_circle_info['bizcircle_id'])
            ).first()

            if biz_circle:
                # 记录已存在，可能需要更新 district_id
                if district.id not in biz_circle.district_id:
                    # biz_circle.district_id.append()、district_id += 等方式都不能更新表
                    biz_circle.district_id = biz_circle.district_id + [district.id]
            else:
                biz_circle = BizCircle(district.id, biz_circle_info)
                db_session.add(biz_circle)

    db_session.commit()
    db_session.close()

    logging.info('初始化/更新城市信息结束.')


def get_city():
    """
    获取城市信息
    """
    url = 'http://app.api.lianjia.com/config/config/initData'

    payload = {
        'params': '{{"city_id":"{}","mobile_type":"android","version":"7.7.6"}}'.format(CITY_ID),
        'fields': '{"mall_const":"e14628fb700583c1c3dc2f2a91cde0b7","xqf_filter":"aad6bacfa323f4dd3b85781dde6816cb","te_is_show":"fe2aab8915a6235c7549d6e3378d3092","city_info":"8433a68effe339dcecb19694de43d418","esf_filter":"2a3d06f861d98927ff4de4c4d459aff2","city_config_all":"db28b795dbf329d1a6d33fa747a6d6aa","nh_city_info":"ae756fcac2b4156b486bc2e54649cf48"}',
    }

    data = util.get_data(url, payload, 'POST')
    return data['city_info']['info'][0]


def update_communities():
    """
    获取/更新小区信息
    """
    days = 1
    deadline = datetime.now() - timedelta(days=days)
    logging.info('更新久于 {} 天的小区信息...'.format(days))

    db_session = Session()

    biz_circles = db_session.query(BizCircle).filter(
        (BizCircle.communities_updated_at == None) |
        (BizCircle.communities_updated_at < deadline)
    ).all()

    total_count = len(biz_circles)
    logging.info('需更新总商圈数量: {}'.format(total_count))

    for i, biz_circle in enumerate(biz_circles):
        communities = get_communities_by_biz_circle(biz_circle.id)
        logging.info('进度={}/{}, 商圈={}, 小区数={}'.format(i + 1, total_count, biz_circle.name, communities['count']))
        update_db(db_session, biz_circle, communities)

    db_session.close()

    logging.info('小区信息更新完毕.')


def get_communities_by_biz_circle(biz_circle_id):
    """
    按商圈获得小区信息
    """
    url = 'http://app.api.lianjia.com/house/community/search'

    offset = 0

    communities = {
        'count': 0,
        'list': []
    }

    while True:
        params = {
            'bizcircle_id': biz_circle_id,
            'group_type': 'community',
            'limit_offset': offset,
            'city_id': CITY_ID,
            'limit_count': 100
        }

        data = util.get_data(url, params)

        if data:
            communities['count'] = data['total_count']
            communities['list'].extend(data['list'])

            if data['has_more_data']:
                offset += len(data['list'])
            else:
                break
        else:
            # 存在没有数据的时候, 如: http://bj.lianjia.com/xiaoqu/huairouqita1/
            break

    return communities


def update_db(db_session, biz_circle, communities):
    """
    更新小区信息, 商圈信息
    """
    db_session.query(Community).filter(
        Community.biz_circle_id == biz_circle.id
    ).delete(synchronize_session=False)

    for community_info in communities['list']:
        district_id = DISTRICT_MAP[community_info['district_name']]
        community = Community(CITY_ID, district_id, biz_circle.id, community_info)
        db_session.add(community)

    biz_circle.communities_count = communities['count']
    biz_circle.communities_updated_at = datetime.now()

    db_session.commit()


def proxy_patch():
    """
    Requests 似乎不能使用系统的证书系统, 方便起见, 不验证 HTTPS 证书, 便于使用代理工具进行网络调试...
    http://docs.python-requests.org/en/master/user/advanced/#ca-certificates
    """
    import warnings
    from requests.packages.urllib3.exceptions import InsecureRequestWarning

    class XSession(requests.Session):
        def __init__(self):
            super().__init__()
            self.verify = False

    requests.Session = XSession
    warnings.simplefilter('ignore', InsecureRequestWarning)


if __name__ == '__main__':
    if config.debug and os.getenv('HTTPS_PROXY'):
        proxy_patch()

    main()
