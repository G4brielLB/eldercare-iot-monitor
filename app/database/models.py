from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(String, primary_key=True)     # PAT001, PAT002...
    name = Column(String, nullable=False)     # "Maria Silva"
    age = Column(Integer)                     # 78
    sex = Column(String)                      # "F"
    
    # Relacionamento com mensagens
    health_messages = relationship("HealthMessage", back_populates="patient")
    
    def __repr__(self):
        return f"<Patient(id='{self.id}', name='{self.name}', age={self.age})>"

class HealthMessage(Base):
    __tablename__ = "health_messages"
    
    id = Column(String, primary_key=True)     # PAT001_emergency_123456
    received_at = Column(String, nullable=False)  # timestamp recebimento
    message_type = Column(String, nullable=False) # "emergency" ou "summary"
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)  # PAT001
    timestamp = Column(String, nullable=False)    # timestamp da mensagem original
    data = Column(Text, nullable=False)           # JSON como string
    
    # Relacionamento com paciente
    patient = relationship("Patient", back_populates="health_messages")
    
    def __repr__(self):
        return f"<HealthMessage(id='{self.id}', type='{self.message_type}', patient_id='{self.patient_id}')>"