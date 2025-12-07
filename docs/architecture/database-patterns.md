# データベース設計パターン

## 1. 基本方針

- データの整合性を最優先
- パフォーマンスとスケーラビリティを考慮
- 将来の拡張性を確保
- 安全性重視

## 2. 命名規則

### 2.1 テーブル名
- **複数形**を使用（users, orders, products）
- **スネークケース**を使用（user_profiles, order_items）

```sql
-- 良い例
CREATE TABLE users ( ... );
CREATE TABLE order_items ( ... );

-- 悪い例
CREATE TABLE User ( ... );      -- PascalCase
CREATE TABLE order-item ( ... ); -- ケバブケース
```

### 2.2 カラム名
- **スネークケース**を使用
- 外部キーは `{参照テーブル単数形}_id` の形式

```sql
CREATE TABLE orders (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,        -- users テーブルへの外部キー
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

### 2.3 インデックス名
`idx_{テーブル名}_{カラム名}` の形式

```sql
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_created_at ON orders(created_at);
```

## 3. 主キーとID

### 3.1 UUID v4 を使用
セキュリティとスケーラビリティのため、連番IDではなくUUIDを使用

```sql
CREATE TABLE users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    ...
);
```

### 3.2 複合主キー
関連テーブルでは必要に応じて複合主キーを使用

```sql
CREATE TABLE user_roles (
    user_id UUID NOT NULL,
    role_id UUID NOT NULL,
    PRIMARY KEY (user_id, role_id)
);
```

## 4. タイムスタンプ

### 4.1 必須カラム
すべてのテーブルに以下のカラムを含める：

```sql
created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
```

### 4.2 更新トリガー
updated_at を自動更新するトリガーを設定

```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE
    ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

## 5. 論理削除

### 5.1 deleted_at カラム
物理削除は禁止。代わりに論理削除を使用

```sql
CREATE TABLE products (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    ...
);

-- 削除時
UPDATE products SET deleted_at = CURRENT_TIMESTAMP WHERE id = ?;
```

### 5.2 一意制約との組み合わせ
論理削除を考慮した一意制約

```sql
CREATE UNIQUE INDEX idx_users_email_unique 
ON users(email) 
WHERE deleted_at IS NULL;
```

## 6. リレーション設計

### 6.1 外部キー制約
データ整合性のため、必ず外部キー制約を設定

```sql
CREATE TABLE orders (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    CONSTRAINT fk_orders_user_id 
        FOREIGN KEY (user_id) 
        REFERENCES users(id) 
        ON DELETE RESTRICT
);
```

### 6.2 カスケードポリシー
- **RESTRICT**: デフォルト（参照がある場合は削除不可）
- **CASCADE**: 親と一緒に削除（慎重に使用）
- **SET NULL**: 親削除時にNULLに設定

## 7. インデックス戦略

### 7.1 インデックスを作成すべきカラム
- 外部キー
- WHERE句で頻繁に使用されるカラム
- ORDER BY で使用されるカラム
- JOIN条件で使用されるカラム

### 7.2 複合インデックス
クエリパターンに応じて複合インデックスを作成

```sql
-- ユーザーの注文を日付順に取得する場合
CREATE INDEX idx_orders_user_id_created_at 
ON orders(user_id, created_at DESC);
```

## 8. パフォーマンス最適化

### 8.1 N+1クエリの防止
関連データは適切にJOINまたは事前ロード

```python
# 悪い例（N+1クエリ）
users = User.query.all()
for user in users:
    orders = user.orders  # 各ユーザーごとにクエリ発生

# 良い例
users = User.query.options(joinedload('orders')).all()
```

### 8.2 バッチ処理
大量データの処理はバッチで実行

```python
# 1000件ずつ処理
BATCH_SIZE = 1000
for offset in range(0, total_count, BATCH_SIZE):
    batch = query.limit(BATCH_SIZE).offset(offset).all()
    process_batch(batch)
```

## 9. マイグレーション

### 9.1 前方互換性
- カラム削除は2段階で実行（使用停止→削除）
- NOT NULL制約の追加は慎重に

### 9.2 マイグレーションファイル
必ずロールバック可能にする

```python
# Alembicの例
def upgrade():
    op.add_column('users', sa.Column('phone', sa.String(20)))

def downgrade():
    op.drop_column('users', 'phone')
```

## 10. セキュリティ

### 10.1 個人情報の暗号化
機密情報は暗号化して保存

```python
from cryptography.fernet import Fernet

class User(db.Model):
    _phone = db.Column('phone', db.String(255))
    
    @property
    def phone(self):
        return decrypt(self._phone)
    
    @phone.setter
    def phone(self, value):
        self._phone = encrypt(value)
```

### 10.2 アクセスログ
重要なテーブルへのアクセスは監査ログに記録

## 11. 企業固有のルール

### 11.1 データ保持期間
- ユーザーデータ: 退会後1年間保持
- ログデータ: 3年間保持
- 決済データ: 7年間保持

### 11.2 バックアップ
- 本番データベースは日次バックアップ
- 過去30日分を保持
- 月次で長期保存用バックアップ

### 11.3 パフォーマンス監視
- スロークエリログの監視（1秒以上）
- インデックス使用率の定期チェック
- テーブルサイズの監視

## 12. トランザクション管理

### 12.1 分離レベル
デフォルトは READ COMMITTED

### 12.2 デッドロック対策
- 更新順序を統一
- 長時間のトランザクションを避ける

```python
# 常に同じ順序で更新
with db.session.begin():
    # 必ずuser → orderの順で更新
    user.update_balance()
    order.update_status()
```
