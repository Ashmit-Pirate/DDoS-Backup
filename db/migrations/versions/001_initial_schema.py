"""001_initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-08-25 23:55:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable uuid-ossp extension if available in PostgreSQL
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')

    # detections table
    op.create_table(
        'detections',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('source_ip', sa.String(), nullable=False),
        sa.Column('gatekeeper_confidence', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('predicted_class', sa.String(), nullable=False),
        sa.Column('confidence', sa.Numeric(precision=5, scale=4), nullable=False),
        sa.CheckConstraint(
            "predicted_class IN ('Benign','LDAP','MSSQL','NetBIOS','Portmap','Syn','UDP','UDPLag')",
            name='check_detection_predicted_class'
        ),
        sa.CheckConstraint('confidence >= 0 AND confidence <= 1', name='check_detection_confidence_range')
    )
    op.create_index('idx_detections_time', 'detections', ['timestamp'], unique=False)

    # risk_assessments table
    op.create_table(
        'risk_assessments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('detection_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('detections.id', ondelete='CASCADE'), nullable=False),
        sa.Column('risk_score', sa.Integer(), nullable=False),
        sa.Column('severity', sa.String(), nullable=False),
        sa.Column('factors', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint('risk_score BETWEEN 0 AND 100', name='check_risk_score_range'),
        sa.CheckConstraint("severity IN ('LOW','MEDIUM','HIGH')", name='check_severity_values')
    )

    # mitigation_actions table
    op.create_table(
        'mitigation_actions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('risk_assessment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('risk_assessments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('attack_type', sa.String(), nullable=False),
        sa.Column('action_type', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('source_ip', sa.String(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('PLANNED','SIMULATED','ACTIVE','COMPLETED')", name='check_mitigation_status_values')
    )
    op.create_index('idx_mitigation_source', 'mitigation_actions', ['source_ip', 'status'], unique=False)

    # events table
    op.create_table(
        'events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('attack_type', sa.String(), nullable=False),
        sa.Column('severity', sa.String(), nullable=False),
        sa.Column('confidence', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('action', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True)
    )
    op.create_index('idx_events_time', 'events', ['timestamp'], unique=False)
    op.create_index('idx_events_attack_type', 'events', ['attack_type'], unique=False)

    # system_status table
    op.create_table(
        'system_status',
        sa.Column('id', sa.Integer(), primary_key=True, default=1),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint('id = 1', name='check_singleton_id'),
        sa.CheckConstraint(
            "status IN ('NORMAL','ATTACK_DETECTED','CLASSIFIED','MITIGATING','RECOVERING','RECOVERED')",
            name='check_system_status_values'
        )
    )

    # config table
    op.create_table(
        'config',
        sa.Column('key', sa.String(), primary_key=True),
        sa.Column('value', sa.String(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )


def downgrade() -> None:
    op.drop_table('config')
    op.drop_table('system_status')
    op.drop_index('idx_events_attack_type', table_name='events')
    op.drop_index('idx_events_time', table_name='events')
    op.drop_table('events')
    op.drop_index('idx_mitigation_source', table_name='mitigation_actions')
    op.drop_table('mitigation_actions')
    op.drop_table('risk_assessments')
    op.drop_index('idx_detections_time', table_name='detections')
    op.drop_table('detections')
