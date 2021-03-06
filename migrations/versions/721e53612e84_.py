"""empty message

Revision ID: 721e53612e84
Revises: a5537caad779
Create Date: 2016-07-15 11:33:10.301124

"""

# revision identifiers, used by Alembic.
revision = '721e53612e84'
down_revision = 'a5537caad779'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('suit', schema=None) as batch_op:
        batch_op.add_column(sa.Column('confirmed', sa.DateTime(), nullable=True))

    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('suit', schema=None) as batch_op:
        batch_op.drop_column('confirmed')

    ### end Alembic commands ###
