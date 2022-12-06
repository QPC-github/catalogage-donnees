"""remove-on-cascade-delete

Revision ID: f839718bc095
Revises: 82c5fa04f06f
Create Date: 2022-12-06 12:45:15.174155

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "f839718bc095"
down_revision = "82c5fa04f06f"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("dataset_tag_tag_id_fkey", "dataset_tag", type_="foreignkey")
    op.create_foreign_key(None, "dataset_tag", "tag", ["tag_id"], ["id"])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "dataset_tag", type_="foreignkey")
    op.create_foreign_key(
        "dataset_tag_tag_id_fkey",
        "dataset_tag",
        "tag",
        ["tag_id"],
        ["id"],
        ondelete="CASCADE",
    )
    # ### end Alembic commands ###
