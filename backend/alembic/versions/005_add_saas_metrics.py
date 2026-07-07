"""
Database migration for SaaS metrics tables.
Run: alembic revision --autogenerate -m "Add SaaS metrics tables"
Then: alembic upgrade head
"""

from alembic import op
import sqlalchemy as sa


def upgrade():
    """Create new tables for SaaS metrics."""
    
    # UserMetric table
    op.create_table(
        'user_metrics',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('event_type', sa.String(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('metadata', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_metrics_timestamp'), 'user_metrics', ['timestamp'])
    op.create_index(op.f('ix_user_metrics_user_id'), 'user_metrics', ['user_id'])

    # AnalysisMetric table
    op.create_table(
        'analysis_metrics',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('analysis_id', sa.String(), nullable=True),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('resume_word_count', sa.Integer(), nullable=True),
        sa.Column('jd_word_count', sa.Integer(), nullable=True),
        sa.Column('ats_score', sa.Integer(), nullable=True),
        sa.Column('keyword_score', sa.Integer(), nullable=True),
        sa.Column('semantic_score', sa.Float(), nullable=True),
        sa.Column('quality_score', sa.Integer(), nullable=True),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('optimizer_used', sa.Boolean(), nullable=True),
        sa.Column('optimizer_time_ms', sa.Integer(), nullable=True),
        sa.Column('pdf_generated', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_analysis_metrics_analysis_id'), 'analysis_metrics', ['analysis_id'])
    op.create_index(op.f('ix_analysis_metrics_created_at'), 'analysis_metrics', ['created_at'])
    op.create_index(op.f('ix_analysis_metrics_user_id'), 'analysis_metrics', ['user_id'])

    # SubscriptionMetric table
    op.create_table(
        'subscription_metrics',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('plan', sa.String(), nullable=True),
        sa.Column('analyses_this_month', sa.Integer(), nullable=True),
        sa.Column('analyses_limit', sa.Integer(), nullable=True),
        sa.Column('ai_optimizations_this_month', sa.Integer(), nullable=True),
        sa.Column('ai_optimizations_limit', sa.Integer(), nullable=True),
        sa.Column('template_used', sa.String(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('last_active_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_subscription_metrics_user_id'), 'subscription_metrics', ['user_id'])

    # DailyStats table
    op.create_table(
        'daily_stats',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('date', sa.String(), nullable=True),
        sa.Column('total_active_users', sa.Integer(), nullable=True),
        sa.Column('new_users', sa.Integer(), nullable=True),
        sa.Column('returning_users', sa.Integer(), nullable=True),
        sa.Column('total_resumes_uploaded', sa.Integer(), nullable=True),
        sa.Column('total_analyses_run', sa.Integer(), nullable=True),
        sa.Column('total_optimizations_run', sa.Integer(), nullable=True),
        sa.Column('total_pdfs_generated', sa.Integer(), nullable=True),
        sa.Column('avg_ats_score', sa.Float(), nullable=True),
        sa.Column('avg_processing_time_ms', sa.Float(), nullable=True),
        sa.Column('pro_users', sa.Integer(), nullable=True),
        sa.Column('enterprise_users', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date')
    )
    op.create_index(op.f('ix_daily_stats_date'), 'daily_stats', ['date'])


def downgrade():
    """Drop SaaS metrics tables."""
    op.drop_index(op.f('ix_daily_stats_date'), table_name='daily_stats')
    op.drop_table('daily_stats')
    op.drop_index(op.f('ix_subscription_metrics_user_id'), table_name='subscription_metrics')
    op.drop_table('subscription_metrics')
    op.drop_index(op.f('ix_analysis_metrics_created_at'), table_name='analysis_metrics')
    op.drop_index(op.f('ix_analysis_metrics_user_id'), table_name='analysis_metrics')
    op.drop_index(op.f('ix_analysis_metrics_analysis_id'), table_name='analysis_metrics')
    op.drop_table('analysis_metrics')
    op.drop_index(op.f('ix_user_metrics_timestamp'), table_name='user_metrics')
    op.drop_index(op.f('ix_user_metrics_user_id'), table_name='user_metrics')
    op.drop_table('user_metrics')
