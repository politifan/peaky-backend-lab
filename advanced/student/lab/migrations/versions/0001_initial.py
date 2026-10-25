from alembic import op
import sqlalchemy as sa
revision='0001'
down_revision=None
branch_labels=None
depends_on=None
def upgrade():
    op.create_table('schema_state',sa.Column('id',sa.Integer,primary_key=True),sa.Column('version',sa.Integer,nullable=False))
    op.create_table('stock',sa.Column('tenant',sa.String(120),primary_key=True),sa.Column('available',sa.Integer,nullable=False),sa.CheckConstraint('available >= 0',name='ck_stock_nonnegative'))
    op.create_table('reservation',sa.Column('id',sa.Integer,primary_key=True),sa.Column('tenant',sa.String(120),nullable=False),sa.Column('key',sa.String(120),nullable=False),sa.Column('qty',sa.Integer,nullable=False),sa.UniqueConstraint('tenant','key',name='uq_reservation_key'),sa.CheckConstraint('qty > 0',name='ck_reservation_positive'))
    op.create_table('item',sa.Column('tenant',sa.String(120),primary_key=True),sa.Column('id',sa.Integer,primary_key=True),sa.Column('owner',sa.String(120),nullable=False),sa.Column('name',sa.String(200),nullable=False))
    op.create_table('resource',sa.Column('name',sa.String(120),primary_key=True),sa.Column('token',sa.Integer,nullable=False),sa.Column('value',sa.String(200),nullable=False))
    op.create_table('account',sa.Column('tenant',sa.String(120),primary_key=True),sa.Column('balance',sa.Integer,nullable=False))
    op.create_table('inbox',sa.Column('event',sa.String(120),primary_key=True),sa.Column('tenant',sa.String(120),nullable=False),sa.Column('delta',sa.Integer,nullable=False))
    op.create_table('outbox',sa.Column('id',sa.Integer,primary_key=True),sa.Column('tenant',sa.String(120),nullable=False),sa.Column('event',sa.String(120),nullable=False,unique=True),sa.Column('payload',sa.String(500),nullable=False),sa.Column('state',sa.String(20),nullable=False),sa.Column('due',sa.Integer,nullable=False),sa.Column('lease_until',sa.Integer,nullable=False),sa.Column('token',sa.Integer,nullable=False))
def downgrade():
    for name in ['outbox','inbox','account','resource','item','reservation','stock','schema_state']:op.drop_table(name)
