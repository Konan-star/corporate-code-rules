# 命名規則

## 1. 基本原則

コードの可読性と保守性を高めるため、以下の命名規則を遵守してください。

## 2. 変数名

### 2.1 一般的な変数
- **小文字とアンダースコア**（snake_case）を使用
- 意味のある名前を使用し、略語は避ける

```python
# 良い例
user_name = "田中太郎"
total_amount = 1000
is_authenticated = True

# 悪い例
n = "田中太郎"  # 意味不明
amt = 1000     # 不必要な略語
flag = True    # 何のフラグか不明
```

### 2.2 定数
- **すべて大文字**でアンダースコア区切り
- モジュールレベルで定義

```python
# 良い例
MAX_RETRY_COUNT = 3
API_TIMEOUT_SECONDS = 30
DEFAULT_PAGE_SIZE = 20
```

## 3. 関数名

### 3.1 基本ルール
- **小文字とアンダースコア**（snake_case）を使用
- **動詞で始める**（アクションを明確に）
- 機能を明確に表現する

```python
# 良い例
def calculate_total_price(items):
    pass

def validate_user_input(data):
    pass

def fetch_user_data(user_id):
    pass

# 悪い例
def total(items):  # 動詞がない
    pass

def check(data):  # 何をチェックするか不明
    pass
```

### 3.2 特殊な関数名
- **プライベート関数**：アンダースコアで開始 `_internal_function()`
- **テスト関数**：`test_` で開始
- **非同期関数**：動詞は変えずに `async def` を使用

## 4. クラス名

### 4.1 基本ルール
- **PascalCase**（単語の先頭を大文字）を使用
- 名詞を使用
- 単数形を使用

```python
# 良い例
class UserAccount:
    pass

class PaymentProcessor:
    pass

class DatabaseConnection:
    pass

# 悪い例
class user_account:  # snake_caseは使わない
    pass

class ProcessPayments:  # 動詞で始まっている
    pass
```

## 5. モジュール名とパッケージ名

- **すべて小文字**
- 短く簡潔に
- アンダースコア使用可（ただし最小限に）

```python
# 良い例
import user_auth
import payment_gateway
import database_utils

# 悪い例
import UserAuth  # PascalCaseは使わない
import Payment_Gateway  # 不必要な大文字
```

## 6. 企業固有の命名規則

### 6.1 APIエンドポイント関連
- ハンドラー関数は `handle_` で開始
- バリデータ関数は `validate_` で開始

```python
def handle_user_registration(request):
    """ユーザー登録のハンドラー"""
    pass

def validate_email_format(email):
    """メールアドレス形式の検証"""
    pass
```

### 6.2 データベース関連
- モデルクラスは単数形
- リポジトリクラスは `Repository` で終了

```python
class User:
    """ユーザーモデル"""
    pass

class UserRepository:
    """ユーザーリポジトリ"""
    pass
```

### 6.3 ログ関連
- ロガー名は `__name__` を使用
- トレースID変数は `trace_id` で統一

```python
import logging

logger = logging.getLogger(__name__)

def process_request(trace_id: str):
    logger.info(f"Processing request", extra={"trace_id": trace_id})
```

## 7. 禁止事項

以下の命名は禁止します：

1. **1文字変数**（ループカウンタの `i`, `j`, `k` を除く）
2. **日本語変数名**（コメントは日本語OK）
3. **予約語に似た名前**（`class_`, `type_` など）
4. **連続したアンダースコア** `__var__`（Pythonの特殊メソッドを除く）

## 8. 例外的なケース

### 8.1 外部ライブラリとの整合性
外部ライブラリの規約に合わせる必要がある場合は、そちらを優先

```python
# Django の場合
class UserViewSet:  # DjangoのViewSet規約に従う
    pass
```

### 8.2 レガシーコードとの互換性
既存システムとの互換性が必要な場合は、チームリーダーと相談の上、例外を認める場合があります。
