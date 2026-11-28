"""fix ten star rating constraint"""

from alembic import op

revision = "7e2a91c4d6b8"
down_revision = "5bd792a89746"
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