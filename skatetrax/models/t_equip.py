from sqlalchemy import Column, Integer, Float, String, DateTime, UUID, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped
from uuid import uuid4, UUID as UUIDV4
from datetime import datetime, timezone
from .base import Base


class uSkaterEquipManifest(Base):
    '''
    This table keeps track of items purchased along the skater's jouney
    excluding boots and blades.  This is a good place for things like
    tights, gloves, bags and other associated items that don't really
    have specified lifetimes but may need replaced or even avoided in the
    future.
    '''

    __tablename__ = 'uSkaterEquipment'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    date_created = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    equip_manufacturer = Column(String)
    equip_model = Column(String)
    equip_notes = Column(String)
    equip_size = Column(String)
    equip_color = Column(String)
    equip_vendor = Column(String)
    equip_cost = Column(Float)
    equip_url = Column(String)
    uSkaterUUID = Column(UUID, ForeignKey("uSkaterConfig.uSkaterUUID", ondelete='CASCADE'))

    def __init__(
        self,
        date_created,
        equip_manufacturer,
        equip_model,
        equip_notes,
        equip_size,
        equip_color,
        equip_vendor,
        equip_cost,
        uSkaterUUID
            ):

        self.date_created = date_created
        self.equip_manufacturer = equip_manufacturer
        self.equip_model = equip_model
        self.equip_notes = equip_notes
        self.equip_size = equip_size
        self.equip_color = equip_color
        self.equip_vendor = equip_vendor
        self.equip_cost = equip_cost
        self.uSkaterUUID = uSkaterUUID


class uSkateConfig(Base):
    '''
    This table describes a pair of skates, as a combo, per skater.
    A combo contains a set of blades, and a set of boots.

    By default, there should be a 'rental' skate config available
    to evey user, for new skaters that havent purchased skates yet.

    sConfigType is a key for ice skates vs roller/pic/box skates.
    sActiveFlag is determines if a combo is currently in use.

    Every field is required for this to work correctly, but is all
    either true/false or foreign key data except for the date.
    '''

    __tablename__ = 'uSkateConfig'
    __table_args__ = {'extend_existing': True}

    sConfigID: Mapped[UUIDV4] = mapped_column(primary_key=True, default=uuid4)
    date_created = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    uSkaterUUID = Column(UUID)
    uSkaterBladesID = Column(UUID)
    uSkaterBootsID = Column(UUID)
    sConfigType = Column(Integer)  # surface type
    sActiveFlag = Column(Integer)

    def __init__(
        self,
        sConfigID,
        date_created,
        uSkaterBladesID,
        uSkaterBootsID,
        uSkaterUUID,
        sConfigType,
        sActiveFlag
    ):

        self.sConfigID = sConfigID
        self.date_created = date_created
        self.uSkaterBladesID = uSkaterBladesID
        self.uSkaterBootsID = uSkaterBootsID
        self.uSkaterUUID = uSkaterUUID
        self.sConfigType = sConfigType
        self.sActiveFlag = sActiveFlag


class uSkaterBlades(Base):
    '''
    This table contains all data we would ever want to have about blades.
    Where did they come from, where did they go, and how much did it cost us.
    ID's are for foreign keys, so that any boot and can be used with any blade
    '''

    __tablename__ = 'uSkaterBlades'
    __table_args__ = {'extend_existing': True}

    bladesID: Mapped[UUIDV4] = mapped_column(primary_key=True, default=uuid4)
    date_created = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    bladesName = Column(String)
    bladesModel = Column(String)
    bladesSize = Column(String)
    bladesPurchaseAmount = Column(Float)
    uSkaterUUID = Column(UUID)

    def __init__(
        self,
        date_created,
        bladesID,
        bladesName,
        bladesModel,
        bladesSize,
        bladesPurchaseAmount,
        uSkaterUUID
            ):

        self.date_created = date_created
        self.bladesID = bladesID
        self.bladesName = bladesName
        self.bladesModel = bladesModel
        self.bladesSize = bladesSize
        self.bladesPurchaseAmount = bladesPurchaseAmount
        self.uSkaterUUID = uSkaterUUID


class uSkaterBoots(Base):
    '''
    This table contains all data we would ever want to have about boots.
    Where did they come from, where did they go, and how much did it cost us.
    ID's are for foreign keys, so that any boot and can be used with any blade
    '''

    __tablename__ = 'uSkaterBoots'
    __table_args__ = {'extend_existing': True}

    bootsID: Mapped[UUIDV4] = mapped_column(primary_key=True, default=uuid4)
    date_created = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    bootsName = Column(String)
    bootsModel = Column(String)
    bootsSize = Column(String)
    bootsPurchaseAmount = Column(Float)
    uSkaterUUID = Column(UUID)

    def __init__(
        self,
        date_created,
        bootsID,
        bootsName,
        bootsModel,
        bootsSize,
        bootsPurchaseAmount,
        uSkaterUUID
            ):

        self.date_created = date_created
        self.bootsID = bootsID
        self.bootsName = bootsName
        self.bootsModel = bootsModel
        self.bootsSize = bootsSize
        self.bootsPurchaseAmount = bootsPurchaseAmount
        self.uSkaterUUID = uSkaterUUID
