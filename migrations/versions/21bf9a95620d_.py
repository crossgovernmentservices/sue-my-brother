"""empty message

Revision ID: 21bf9a95620d
Revises: 513803e6f38c
Create Date: 2016-08-25 13:41:07.794038

"""

# revision identifiers, used by Alembic.
revision = '21bf9a95620d'
down_revision = '513803e6f38c'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('can_accept_suits', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('is_superadmin', sa.Boolean(), nullable=True))

    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('is_superadmin')
        batch_op.drop_column('can_accept_suits')

    ### end Alembic commands ###
