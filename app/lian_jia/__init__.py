from util.orm import Base, engine
from .city import City, District, BizCircle
from .community import Community

Base.metadata.create_all(engine)
