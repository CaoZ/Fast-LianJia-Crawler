from datetime import datetime

from sqlalchemy import Column, types
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.schema import ForeignKey

from util.orm import AlchemyMixin, Base
from .city import City, District, BizCircle


class Community(AlchemyMixin, Base):
    __tablename__ = 'communities'

    id = Column(types.BigInteger, primary_key=True)
    city_id = Column(types.Integer, ForeignKey(City.id), nullable=False)
    district_id = Column(types.Integer, ForeignKey(District.id), nullable=False)
    biz_circle_id = Column(types.Integer, ForeignKey(BizCircle.id), nullable=False)
    name = Column(types.String(32), nullable=False)
    building_finish_year = Column(types.Integer)  # 建筑年代, 可能无此信息
    building_type = Column(types.String(32))  # 建筑类型, 可能无此信息
    second_hand_quantity = Column(types.Integer, nullable=False)
    second_hand_unit_price = Column(types.Integer)  # 二手均价, 可能无此信息
    detail = Column(JSONB)  # 详细信息键值对, 如: {"物业公司": "...", "物业电话": "...", ...}
    updated_at = Column(types.DateTime, nullable=False, default=datetime.now)
    page_fetched_at = Column(types.DateTime)

    def __init__(self, city_id, district_id, biz_circle_id, info):
        self.id = int(info['community_id'])
        self.city_id = city_id
        self.district_id = district_id
        self.biz_circle_id = biz_circle_id
        self.name = info['community_name']
        self.building_finish_year = int(info['building_finish_year']) if 'building_finish_year' in info else None
        self.building_type = info.get('building_type')
        self.second_hand_quantity = info['ershoufang_source_count']
        self.second_hand_unit_price = info['ershoufang_avg_unit_price'] if 'ershoufang_avg_unit_price' in info else None
