from alembic import op
import sqlalchemy as sa
revision='0001'
down_revision=None
branch_labels=None
depends_on=None
def upgrade():
 op.create_table('users',sa.Column('id',sa.Integer,primary_key=True),sa.Column('username',sa.String(50),nullable=False,unique=True),sa.Column('password_hash',sa.String(255),nullable=False))
 op.create_table('tickets',sa.Column('id',sa.Integer,primary_key=True),sa.Column('owner_id',sa.Integer,sa.ForeignKey('users.id'),nullable=False),sa.Column('title',sa.String(80),nullable=False),sa.Column('request_key',sa.String(100),nullable=False),sa.Column('request_title',sa.String(80),nullable=False),sa.Column('request_priority',sa.Integer,nullable=False),sa.UniqueConstraint('owner_id','request_key',name='uq_ticket_owner_key'))
 op.create_index('ix_tickets_owner_id','tickets',['owner_id'])
def downgrade():
 op.drop_table('tickets')
 op.drop_table('users')
