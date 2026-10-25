from alembic import op
import sqlalchemy as sa
revision='0002'
down_revision='0001'
branch_labels=None
depends_on=None
def upgrade():
 op.add_column('tickets',sa.Column('priority',sa.Integer,nullable=True))
 op.execute('UPDATE tickets SET priority=1 WHERE priority IS NULL')
 with op.batch_alter_table('tickets') as batch:
  batch.alter_column('priority',existing_type=sa.Integer,nullable=False)
  batch.create_check_constraint('ck_ticket_priority','priority BETWEEN 0 AND 3')
def downgrade():
 with op.batch_alter_table('tickets') as batch:
  batch.drop_constraint('ck_ticket_priority',type_='check')
  batch.drop_column('priority')
