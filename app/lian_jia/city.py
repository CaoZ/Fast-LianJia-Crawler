from datetime import datetime

from sqlalchemy import Column, types
from sqlalchemy.schema import ForeignKey

from util.orm import AlchemyMixin, Base


class City(AlchemyMixin, Base):
    __tablename__ = 'cities'

    id = Column(types.Integer, primary_key=True)
    name = Column(types.String, nullable=False)
    districts_count = Column(types.Integer, nullable=False)

    def __init__(self, info):
        self.id = info['city_id']
        self.name = info['city_name']
        self.districts_count = len(info['district'])


class District(AlchemyMixin, Base):
    __tablename__ = 'districts'

    id = Column(types.Integer, primary_key=True)
    city_id = Column(types.Integer, ForeignKey(City.id), nullable=False)
    name = Column(types.String, nullable=False)
    quan_pin = Column(types.String, nullable=False)
    biz_circles_count = Column(types.Integer, nullable=False)

    def __init__(self, city_id, info):
        self.id = int(info['district_id'])
        self.city_id = city_id
        self.name = info['district_name']
        self.quan_pin = info['district_quanpin']
        self.biz_circles_count = len(info['bizcircle'])
        self.updated_at = Column(types.DateTime, default=datetime.now)


class BizCircle(AlchemyMixin, Base):
    __tablename__ = 'biz_circles'

    id = Column(types.Integer, primary_key=True)
    # 一个商圈可能靠近多个行政区, 如: 西城区、东城区下都出现了安定门
    city_id = Column(types.Integer, ForeignKey(City.id), nullable=False)
    district_id = Column(types.ARRAY(types.Integer, dimensions=1, as_tuple=True), nullable=False)
    name = Column(types.String, nullable=False)
    quan_pin = Column(types.String, nullable=False)
    communities_count = Column(types.Integer, nullable=False, default=0)
    updated_at = Column(types.DateTime, nullable=False, default=datetime.now)
    communities_updated_at = Column(types.DateTime)

    def __init__(self, city_id, district_id, info):
        self.id = int(info['bizcircle_id'])
        self.city_id = city_id
        self.district_id = [district_id]
        self.name = info['bizcircle_name']
        self.quan_pin = info['bizcircle_quanpin']
