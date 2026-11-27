"""update rating scale to ten stars

Revision ID: 5bd792a89746
Revises: 94ab8d4bc889
Create Date: 2026-11-28 03:27:37.260466

"""
from alembic import op
import sqlalchemy as sa


revision = '5bd792a89746'
down_revision = '94ab8d4bc889'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("ratings") as batch_op:
        batch_op.drop_constraint(
            "valid_rating_score",
            type_="check",
        )

        batch_op.create_check_constraint(
            "valid_rating_score",
            "score >= 0.5 AND score <= 10.0 "
            "AND score * 2 = CAST(score * 2 AS INTEGER)",
        )


def downgrade():
    with op.batch_alter_table("ratings") as batch_op:
        batch_op.drop_constraint(
            "valid_rating_score",
            type_="check",
        )

        batch_op.create_check_constraint(
            "valid_rating_score",
            "score >= 0.5 AND score <= 5.0 "
            "AND score * 2 = CAST(score * 2 AS INTEGER)",
        )
