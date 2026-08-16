"""add_product_name_snapshot_ondelete_rules_fix_nullable

What this migration does
------------------------
1. order_items  — adds product_name VARCHAR(200) NOT NULL (snapshot column)
2. order_items  — makes product_id nullable  (supports ON DELETE SET NULL)
3. order_items  — adds named FKs with ondelete rules:
                    order_id   -> orders.id    ON DELETE CASCADE
                    product_id -> products.id  ON DELETE SET NULL
4. orders       — adds named FK:
                    user_id -> users.id         ON DELETE CASCADE
5. cart_items   — adds named FKs:
                    user_id    -> users.id      ON DELETE CASCADE
                    product_id -> products.id   ON DELETE RESTRICT

SQLite note
-----------
SQLite has no ALTER TABLE ... DROP CONSTRAINT.  Alembic's batch_alter_table
works by copying the table to a new definition, so we do NOT need explicit
drop_constraint calls — we simply declare the desired final state inside the
batch context and Alembic writes the correct CREATE TABLE from scratch.

Revision ID: 1f5419995e19
Revises: 4306687c1bea
Create Date: 2026-08-16 14:26:51.180599
"""
from alembic import op
import sqlalchemy as sa


revision = '1f5419995e19'
down_revision = '4306687c1bea'
branch_labels = None
depends_on = None


def upgrade():
    # ------------------------------------------------------------------ #
    # order_items                                                          #
    # ------------------------------------------------------------------ #
    with op.batch_alter_table('order_items', schema=None) as batch_op:
        # Add the product_name snapshot column.
        # SQLite requires a server_default when adding NOT NULL to an existing
        # table; we remove the default immediately after so new rows must
        # supply the value explicitly.
        batch_op.add_column(
            sa.Column('product_name', sa.String(length=200),
                      nullable=False, server_default='')
        )
        batch_op.alter_column(
            'product_name',
            existing_type=sa.String(length=200),
            server_default=None,
            nullable=False,
        )
        # Make product_id nullable to allow ON DELETE SET NULL.
        batch_op.alter_column(
            'product_id',
            existing_type=sa.INTEGER(),
            nullable=True,
        )
        # Declare named FKs with ondelete rules.
        # Batch mode recreates the table, so no prior drop_constraint needed.
        batch_op.create_foreign_key(
            'fk_order_items_order_id',
            'orders', ['order_id'], ['id'],
            ondelete='CASCADE',
        )
        batch_op.create_foreign_key(
            'fk_order_items_product_id',
            'products', ['product_id'], ['id'],
            ondelete='SET NULL',
        )

    # ------------------------------------------------------------------ #
    # orders                                                               #
    # ------------------------------------------------------------------ #
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.create_foreign_key(
            'fk_orders_user_id',
            'users', ['user_id'], ['id'],
            ondelete='CASCADE',
        )

    # ------------------------------------------------------------------ #
    # cart_items                                                           #
    # ------------------------------------------------------------------ #
    with op.batch_alter_table('cart_items', schema=None) as batch_op:
        batch_op.create_foreign_key(
            'fk_cart_items_user_id',
            'users', ['user_id'], ['id'],
            ondelete='CASCADE',
        )
        batch_op.create_foreign_key(
            'fk_cart_items_product_id',
            'products', ['product_id'], ['id'],
            ondelete='RESTRICT',
        )


def downgrade():
    with op.batch_alter_table('cart_items', schema=None) as batch_op:
        batch_op.drop_constraint('fk_cart_items_user_id',    type_='foreignkey')
        batch_op.drop_constraint('fk_cart_items_product_id', type_='foreignkey')

    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.drop_constraint('fk_orders_user_id', type_='foreignkey')

    with op.batch_alter_table('order_items', schema=None) as batch_op:
        batch_op.drop_constraint('fk_order_items_order_id',   type_='foreignkey')
        batch_op.drop_constraint('fk_order_items_product_id', type_='foreignkey')
        batch_op.alter_column('product_id', existing_type=sa.INTEGER(), nullable=False)
        batch_op.drop_column('product_name')
