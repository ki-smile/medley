#!/usr/bin/env python
"""
Database models for MEDLEY
SQLAlchemy models for analysis history, ratings, and analytics
"""

import json
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func

Base = declarative_base()

class Analysis(Base):
    """Analysis history tracking"""
    __tablename__ = 'analyses'
    
    id = Column(String(100), primary_key=True)
    title = Column(String(200))
    case_text = Column(Text, nullable=False)
    case_hash = Column(String(64), index=True)  # For deduplication
    
    # Analysis configuration
    use_free_models = Column(Boolean, default=True)
    selected_models = Column(JSON)  # List of model IDs
    model_count = Column(Integer)
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_seconds = Column(Integer)
    
    # Status
    status = Column(String(20), default='pending')  # pending, running, completed, failed, cancelled
    error_message = Column(Text)
    
    # Results summary
    primary_diagnosis = Column(String(200))
    consensus_rate = Column(Float)
    models_responded = Column(Integer)
    models_failed = Column(Integer)
    unique_diagnoses = Column(Integer)
    
    # Storage paths
    json_file = Column(String(500))
    pdf_file = Column(String(500))
    
    # User tracking
    session_id = Column(String(100), index=True)
    ip_address = Column(String(50))
    user_agent = Column(Text)
    
    # Cost tracking
    estimated_cost = Column(Float, default=0.0)
    actual_cost = Column(Float, default=0.0)
    
    # Relationships
    ratings = relationship("DiagnosisRating", back_populates="analysis", cascade="all, delete-orphan")
    model_responses = relationship("ModelResponse", back_populates="analysis", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'status': self.status,
            'primary_diagnosis': self.primary_diagnosis,
            'consensus_rate': self.consensus_rate,
            'models_responded': self.models_responded,
            'unique_diagnoses': self.unique_diagnoses,
            'duration_seconds': self.duration_seconds,
            'use_free_models': self.use_free_models
        }


class ModelResponse(Base):
    """Individual model responses"""
    __tablename__ = 'model_responses'
    
    id = Column(Integer, primary_key=True)
    analysis_id = Column(String(100), ForeignKey('analyses.id'), nullable=False)
    
    model_name = Column(String(100), nullable=False)
    model_origin = Column(String(50))
    
    # Response data
    diagnosis = Column(String(200))
    confidence = Column(Float)
    response_json = Column(JSON)
    
    # Performance
    response_time = Column(Float)
    tokens_used = Column(Integer)
    cost = Column(Float, default=0.0)
    
    # Status
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    analysis = relationship("Analysis", back_populates="model_responses")


class DiagnosisRating(Base):
    """User ratings for diagnoses"""
    __tablename__ = 'diagnosis_ratings'
    
    id = Column(Integer, primary_key=True)
    analysis_id = Column(String(100), ForeignKey('analyses.id'), nullable=False)
    
    diagnosis_name = Column(String(200), nullable=False)
    rating = Column(Integer)  # 1-5 stars
    is_correct = Column(Boolean)  # User feedback on correctness
    
    feedback = Column(Text)
    session_id = Column(String(100))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    analysis = relationship("Analysis", back_populates="ratings")


class ShareableLink(Base):
    """Shareable URLs with expiry"""
    __tablename__ = 'shareable_links'
    
    id = Column(Integer, primary_key=True)
    share_id = Column(String(100), unique=True, nullable=False, index=True)
    analysis_id = Column(String(100), ForeignKey('analyses.id'), nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    
    access_count = Column(Integer, default=0)
    max_access_count = Column(Integer, default=100)
    
    is_active = Column(Boolean, default=True)
    created_by_session = Column(String(100))


class UsageAnalytics(Base):
    """Usage tracking for analytics"""
    __tablename__ = 'usage_analytics'
    
    id = Column(Integer, primary_key=True)
    
    event_type = Column(String(50), nullable=False)  # page_view, analysis_start, api_call, etc.
    event_data = Column(JSON)
    
    session_id = Column(String(100), index=True)
    ip_address = Column(String(50))
    user_agent = Column(Text)
    
    page_url = Column(String(500))
    referrer = Column(String(500))
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class ModelPerformance(Base):
    """Aggregated model performance metrics"""
    __tablename__ = 'model_performance'
    
    id = Column(Integer, primary_key=True)
    model_name = Column(String(100), unique=True, nullable=False)
    
    # Counters
    total_queries = Column(Integer, default=0)
    successful_queries = Column(Integer, default=0)
    failed_queries = Column(Integer, default=0)
    
    # Performance metrics
    avg_response_time = Column(Float)
    avg_tokens_used = Column(Float)
    total_cost = Column(Float, default=0.0)
    
    # Diagnostic metrics
    consensus_participation_rate = Column(Float)
    unique_diagnoses_count = Column(Integer, default=0)
    
    # User ratings
    avg_rating = Column(Float)
    rating_count = Column(Integer, default=0)
    
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DatabaseManager:
    """Database management utilities"""
    
    def __init__(self, db_url: str = "sqlite:///medley.db"):
        self.engine = create_engine(db_url, echo=False)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def save_analysis(self, analysis_data: Dict[str, Any]) -> Analysis:
        """Save analysis to database"""
        session = self.get_session()
        try:
            analysis = Analysis(**analysis_data)
            session.add(analysis)
            session.commit()
            session.refresh(analysis)
            return analysis
        finally:
            session.close()
    
    def get_analysis(self, analysis_id: str) -> Optional[Analysis]:
        """Get analysis by ID"""
        session = self.get_session()
        try:
            return session.query(Analysis).filter_by(id=analysis_id).first()
        finally:
            session.close()
    
    def get_recent_analyses(self, session_id: str = None, limit: int = 10) -> list:
        """Get recent analyses"""
        session = self.get_session()
        try:
            query = session.query(Analysis)
            if session_id:
                query = query.filter_by(session_id=session_id)
            
            analyses = query.order_by(Analysis.created_at.desc()).limit(limit).all()
            return [a.to_dict() for a in analyses]
        finally:
            session.close()
    
    def save_rating(self, analysis_id: str, diagnosis: str, rating: int, 
                   is_correct: bool = None, feedback: str = None, 
                   session_id: str = None) -> DiagnosisRating:
        """Save diagnosis rating"""
        session = self.get_session()
        try:
            rating_obj = DiagnosisRating(
                analysis_id=analysis_id,
                diagnosis_name=diagnosis,
                rating=rating,
                is_correct=is_correct,
                feedback=feedback,
                session_id=session_id
            )
            session.add(rating_obj)
            session.commit()
            return rating_obj
        finally:
            session.close()
    
    def track_event(self, event_type: str, event_data: Dict = None,
                    session_id: str = None, ip_address: str = None,
                    user_agent: str = None, page_url: str = None) -> None:
        """Track usage event"""
        session = self.get_session()
        try:
            event = UsageAnalytics(
                event_type=event_type,
                event_data=event_data or {},
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent,
                page_url=page_url
            )
            session.add(event)
            session.commit()
        finally:
            session.close()
    
    def update_model_performance(self, model_name: str, success: bool,
                                response_time: float = None, tokens: int = None,
                                cost: float = 0.0) -> None:
        """Update model performance metrics"""
        session = self.get_session()
        try:
            perf = session.query(ModelPerformance).filter_by(model_name=model_name).first()
            
            if not perf:
                perf = ModelPerformance(model_name=model_name)
                session.add(perf)
            
            perf.total_queries += 1
            if success:
                perf.successful_queries += 1
            else:
                perf.failed_queries += 1
            
            if response_time:
                if perf.avg_response_time:
                    # Running average
                    perf.avg_response_time = (
                        (perf.avg_response_time * (perf.total_queries - 1) + response_time) 
                        / perf.total_queries
                    )
                else:
                    perf.avg_response_time = response_time
            
            if tokens:
                if perf.avg_tokens_used:
                    perf.avg_tokens_used = (
                        (perf.avg_tokens_used * (perf.total_queries - 1) + tokens)
                        / perf.total_queries
                    )
                else:
                    perf.avg_tokens_used = tokens
            
            perf.total_cost += cost
            
            session.commit()
        finally:
            session.close()
    
    def create_shareable_link(self, analysis_id: str, hours: int = 24,
                             session_id: str = None) -> str:
        """Create shareable link with expiry"""
        import secrets
        from datetime import timedelta
        
        session = self.get_session()
        try:
            share_id = secrets.token_urlsafe(32)
            
            link = ShareableLink(
                share_id=share_id,
                analysis_id=analysis_id,
                expires_at=datetime.utcnow() + timedelta(hours=hours),
                created_by_session=session_id
            )
            
            session.add(link)
            session.commit()
            
            return share_id
        finally:
            session.close()
    
    def get_shareable_analysis(self, share_id: str) -> Optional[Dict]:
        """Get analysis via shareable link"""
        session = self.get_session()
        try:
            link = session.query(ShareableLink).filter_by(
                share_id=share_id,
                is_active=True
            ).first()
            
            if not link:
                return None
            
            # Check expiry
            if link.expires_at < datetime.utcnow():
                link.is_active = False
                session.commit()
                return None
            
            # Check access count
            if link.access_count >= link.max_access_count:
                link.is_active = False
                session.commit()
                return None
            
            # Increment access count
            link.access_count += 1
            session.commit()
            
            # Get analysis
            analysis = session.query(Analysis).filter_by(id=link.analysis_id).first()
            if analysis:
                return analysis.to_dict()
            
            return None
        finally:
            session.close()


# Initialize global database manager
db_manager = None

def init_database(db_url: str = None):
    """Initialize database"""
    global db_manager
    db_manager = DatabaseManager(db_url or "sqlite:///medley.db")
    return db_manager


if __name__ == "__main__":
    # Test database creation
    db = init_database("sqlite:///test_medley.db")
    print("Database initialized successfully!")
    
    # Test saving an analysis
    test_analysis = {
        'id': 'test_001',
        'title': 'Test Analysis',
        'case_text': 'Test case description',
        'case_hash': 'abc123',
        'use_free_models': True,
        'model_count': 17,
        'status': 'completed',
        'primary_diagnosis': 'Test Diagnosis',
        'consensus_rate': 75.5,
        'models_responded': 15,
        'models_failed': 2
    }
    
    analysis = db.save_analysis(test_analysis)
    print(f"Saved analysis: {analysis.id}")
    
    # Test retrieving
    retrieved = db.get_analysis('test_001')
    print(f"Retrieved: {retrieved.to_dict() if retrieved else 'Not found'}")