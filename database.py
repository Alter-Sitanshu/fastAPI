import sqlalchemy as sql
from sqlalchemy import event,func,Enum
from typing import Optional
import datetime
from sqlalchemy.orm import mapped_column, Mapped, DeclarativeBase
import re
from enum import Enum as PyEnum

# I want to keep track of the users,
# Doctors and their details to look up,
# Appointments table will have a many to many connecion between doc and user.
# USER - id, first_name, last_name, address, phone, mail
# DOCTOR - doc_id, first_name, last_name, specialization, address, qualification,
# experience, fee, languages, contact 

class Base(DeclarativeBase):
    # Base class for the models
    pass

class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(sql.Integer, primary_key = True, autoincrement = True)
    first_name: Mapped[str] = mapped_column(sql.String(50), nullable = False)
    last_name: Mapped[Optional[str]] = mapped_column(sql.String(50), nullable = True)
    phone: Mapped[str] = mapped_column(sql.String(12), nullable = False, unique = True)
    email: Mapped[str] = mapped_column(sql.String(255), nullable = False)
    address: Mapped[str] = mapped_column(sql.TEXT, nullable = False)
    active: Mapped[bool] = mapped_column(sql.Boolean, default = False, nullable = False)

class Doctor(Base):
    __tablename__ = "doctors"

    doc_id: Mapped[int] = mapped_column(sql.Integer, primary_key = True, autoincrement = True)
    first_name: Mapped[str] = mapped_column(sql.String(50), nullable = False)
    last_name: Mapped[Optional[str]] = mapped_column(sql.String(50), nullable = True)
    phone: Mapped[str] = mapped_column(sql.String(12), nullable = False, unique = True)
    specialisation: Mapped[str] = mapped_column(sql.String(30), nullable = False)
    experience: Mapped[int] = mapped_column(sql.Integer, nullable = False, server_default = 0)
    fee: Mapped[int] = mapped_column(sql.Integer, nullable = False)
    email: Mapped[str] = mapped_column(sql.String(255), nullable = False, unique = True)
    address: Mapped[str] = mapped_column(sql.TEXT, nullable = False)
    hashed_password: Mapped[str] = mapped_column(sql.String(60), nullable = False)
    token: Mapped[Optional[str]] = mapped_column(sql.String(256), nullable = True, server_default = None)

    __table_args__ = (
        sql.CheckConstraint("experience >= 0", name = "exp_constraint"),
    )

# Status Table for better DB integration
class BookingStatus(PyEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELED = "canceled"

# Bookings table caters a M2M relation between User and Doc
class Bookings(Base):
    __tablename__ = "bookings"

    book_id: Mapped[int] = mapped_column(sql.Integer, autoincrement = True, primary_key = True)
    user_id: Mapped[int] = mapped_column(sql.ForeignKey("users.user_id", ondelete = "CASCADE"), nullable = False)
    doc_id: Mapped[int] = mapped_column(sql.ForeignKey("doctors.doc_id", ondelete = "CASCADE"), nullable = False)
    booking_time: Mapped[datetime.datetime] = mapped_column(sql.DateTime(timezone = True), nullable = False)
    booked_at: Mapped[datetime.datetime] = mapped_column(sql.DateTime(timezone = True), 
                                                         server_default = func.now(), nullable = False,
                                                         onupdate = func.now())
    status: Mapped[BookingStatus] = mapped_column(Enum(BookingStatus),
                                                  server_default=BookingStatus.PENDING.value,
                                                  nullable=False)

# Checking before insertion and updation of name and phone number
@event.listens_for([User,Doctor], "before_insert")
@event.listens_for([User, Doctor], "before_update")
def validate_name(mapper, connection, target):
    if not (re.match(r"^[A-Za-z\s]+$", target.first_name or "") and
             re.match(r"^[A-Za-z ]+$", target.last_name or "")):
        raise ValueError("Name must only contain letters and spaces. No numbers allowed!")
    
@event.listens_for([User,Doctor], "before_insert")
@event.listens_for([User, Doctor], "before_update")
def validate_phone(mapper, connection, target):
    if not re.match(r"^\d+$", target.phone or ""):
        raise ValueError("Phone number must contain only digits.")
    