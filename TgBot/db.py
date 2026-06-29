import os
import sqlite3


class DataBase:
    def __init__(self, table_name=None, db_url=None):
        self.table_name = table_name
        self.db_url = db_url or os.getenv('DATABASE_URL') or 'sqlite:///./tracked_products.db'
        self.conn = self._connect()
        self._ensure_tracked_products_table()

    def _connect(self):
        if self.db_url.startswith('sqlite:///'):
            path = self.db_url[len('sqlite:///'):]
        elif self.db_url.startswith('sqlite://'):
            path = self.db_url[len('sqlite://'):]
        else:
            raise ValueError(
                'Unsupported DATABASE_URL format. Use sqlite:///path/to.db for local testing.'
            )

        directory = os.path.dirname(path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        connection = sqlite3.connect(path, check_same_thread=False)
        connection.execute('PRAGMA foreign_keys = ON')
        connection.row_factory = sqlite3.Row
        return connection

    def _execute(self, query, params=None, commit=False):
        params = params or ()
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        if commit:
            self.conn.commit()
        return cursor

    def _ensure_tracked_products_table(self):
        self._execute(
            '''
            CREATE TABLE IF NOT EXISTS tracked_products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_url TEXT NOT NULL,
                product_name TEXT,
                current_price REAL,
                target_price REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            ''',
            commit=True,
        )

    def add_tracked_product(self, user_id, product_url, product_name, current_price, target_price=None):
        self._execute(
            '''
            INSERT INTO tracked_products (user_id, product_url, product_name, current_price, target_price)
            VALUES (?, ?, ?, ?, ?)
            ''',
            (user_id, product_url, product_name, current_price, target_price),
            commit=True,
        )
        return self._execute('SELECT last_insert_rowid() AS id').fetchone()['id']

    def get_user_tracked_products(self, user_id):
        cursor = self._execute(
            'SELECT * FROM tracked_products WHERE user_id = ? ORDER BY created_at DESC',
            (user_id,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def remove_tracked_product(self, item_id, user_id):
        cursor = self._execute(
            'DELETE FROM tracked_products WHERE id = ? AND user_id = ?',
            (item_id, user_id),
            commit=True,
        )
        return cursor.rowcount > 0

    def get_all_tracked_products(self):
        cursor = self._execute('SELECT * FROM tracked_products ORDER BY id')
        return [dict(row) for row in cursor.fetchall()]

    def update_product_price(self, item_id, current_price):
        self._execute(
            'UPDATE tracked_products SET current_price = ? WHERE id = ?',
            (current_price, item_id),
            commit=True,
        )

    def get_tracked_product(self, item_id, user_id):
        cursor = self._execute(
            'SELECT * FROM tracked_products WHERE id = ? AND user_id = ?',
            (item_id, user_id),
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def close(self):
        self.conn.close()

    def __str__(self):
        return f'DataBase(db_url={self.db_url})'