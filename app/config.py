import argparse
import json
import logging
import sys
from pathlib import Path

log_format = '%(asctime)s %(name)s[%(module)s] %(levelname)s: %(message)s'
logging.basicConfig(format=log_format, level=logging.INFO)


class Config:
    def __init__(self):
        self.city_id = 0
        self.debug = False
        self.db_echo = False
        self.log_format = log_format

        self.db_info = {
            'db': '',
            'host': '',
            'user': '',
            'password': ''
        }

        self.lian_jia = {
            'ua': 'HomeLink7.7.6; Android 7.0',
            'app_id': '20161001_android',
            'app_secret': '7df91ff794c67caee14c3dacd5549b35'
        }

    @classmethod
    def load(cls, d):
        the_config = Config()

        the_config.debug = d.get('debug', False)
        the_config.db_echo = d.get('db_echo', False)
        the_config.db_info.update(d.get('db_info', {}))

        return the_config


def load_config():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help='config file name')
    parser.add_argument('city_id', help='city id', type=int, nargs='?', default=110000)
    args = parser.parse_args()

    config_name = args.config or 'config.json'
    logging.info('使用配置文件 "{}".'.format(config_name))

    config_file = Path(__file__).parent.joinpath('../conf/', config_name)

    if not config_file.exists():
        config_name = 'config.default.json'
        logging.warning('配置文件不存在, 使用默认配置文件 "{}".'.format(config_name))
        config_file = config_file.parent.joinpath(config_name)

    try:
        # 略坑, Path.resolve() 在 3.5 和 3.6 上表现不一致... 若文件不存在 3.5 直接抛异常, 而 3.6
        # 只有 Path.resolve(strict=True) 才抛, 但 strict 默认为 False.
        # 感觉 3.6 的更合理些...
        config_file = config_file.resolve()
        config_dict = json.loads(config_file.read_text())
    except Exception as e:
        sys.exit('# 错误: 配置文件载入失败: {}'.format(e))

    the_config = Config.load(config_dict)
    the_config.city_id = args.city_id

    return the_config


config = load_config()
