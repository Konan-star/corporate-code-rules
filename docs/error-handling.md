# エラーハンドリング規約

## 1. 基本方針

エラーは適切に捕捉し、ログに記録し、ユーザーに分かりやすく伝える必要があります。

## 2. 例外処理の基本ルール

### 2.1 具体的な例外を捕捉する
```python
# 良い例
try:
    user = User.objects.get(id=user_id)
except User.DoesNotExist:
    logger.warning(f"User not found: {user_id}", extra={"trace_id": trace_id})
    raise UserNotFoundException(f"ユーザーID {user_id} が見つかりません")

# 悪い例
try:
    user = User.objects.get(id=user_id)
except Exception:  # 範囲が広すぎる
    logger.error("エラーが発生しました")
    raise
```

### 2.2 例外の再発生
- 元の例外情報を保持する
- より具体的な例外に変換する場合は `from` を使用

```python
# 良い例
try:
    data = external_api.fetch_data()
except RequestException as e:
    logger.error(f"External API error", extra={"trace_id": trace_id, "error": str(e)})
    raise ServiceUnavailableError("外部サービスが利用できません") from e
```

## 3. カスタム例外クラス

### 3.1 基底例外クラス
すべてのカスタム例外は、プロジェクト共通の基底クラスを継承する

```python
class BaseApplicationError(Exception):
    """アプリケーション例外の基底クラス"""
    def __init__(self, message: str, error_code: str = None, trace_id: str = None):
        self.message = message
        self.error_code = error_code
        self.trace_id = trace_id
        super().__init__(message)
```

### 3.2 ドメイン別例外クラス
```python
# 認証関連
class AuthenticationError(BaseApplicationError):
    """認証エラー"""
    pass

class AuthorizationError(BaseApplicationError):
    """認可エラー"""
    pass

# ビジネスロジック関連
class ValidationError(BaseApplicationError):
    """バリデーションエラー"""
    pass

class BusinessRuleViolationError(BaseApplicationError):
    """ビジネスルール違反"""
    pass
```

## 4. ログ出力規約

### 4.1 ログレベルの使い分け
- **DEBUG**: 開発時のデバッグ情報
- **INFO**: 正常な処理フロー
- **WARNING**: 回復可能なエラー
- **ERROR**: 回復不可能なエラー
- **CRITICAL**: システム停止レベルの致命的エラー

### 4.2 必須項目
エラーログには以下を必ず含める：
- **trace_id**: リクエスト追跡用ID
- **user_id**: 影響を受けたユーザー（該当する場合）
- **error_type**: エラーの種類
- **timestamp**: 発生時刻

```python
logger.error(
    "Payment processing failed",
    extra={
        "trace_id": trace_id,
        "user_id": user.id,
        "error_type": "payment_gateway_timeout",
        "amount": amount,
        "currency": "JPY"
    },
    exc_info=True  # スタックトレースを含める
)
```

### 4.3 個人情報の取り扱い
**重要**: 個人情報（PII）は絶対にログに出力しない

```python
# 悪い例
logger.error(f"Failed to process payment for {user.email}")  # メールアドレスが露出

# 良い例
logger.error(f"Failed to process payment for user", extra={"user_id": user.id})
```

## 5. API エラーレスポンス

### 5.1 統一フォーマット
すべてのAPIエラーレスポンスは以下の形式に従う：

```python
{
    "data": null,
    "error": {
        "code": "USER_NOT_FOUND",
        "message": "指定されたユーザーが見つかりません",
        "details": {
            "user_id": "12345"
        }
    },
    "meta": {
        "trace_id": "550e8400-e29b-41d4-a716-446655440000",
        "timestamp": "2024-01-15T09:30:00Z"
    }
}
```

### 5.2 HTTPステータスコードの使い分け
- **400**: クライアントエラー（バリデーションエラー等）
- **401**: 認証エラー
- **403**: 認可エラー
- **404**: リソースが見つからない
- **409**: 競合（重複登録等）
- **500**: サーバー内部エラー
- **503**: サービス利用不可

## 6. リトライとフォールバック

### 6.1 リトライポリシー
外部サービスの呼び出しには必ずリトライ機構を実装する

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def call_external_service():
    """外部サービスを呼び出す"""
    pass
```

### 6.2 フォールバック
重要な機能にはフォールバック処理を実装

```python
def get_user_preferences(user_id: str) -> dict:
    try:
        # キャッシュから取得を試みる
        return cache.get(f"user_prefs:{user_id}")
    except CacheConnectionError:
        logger.warning("Cache unavailable, fetching from database")
        # データベースから取得
        return database.get_user_preferences(user_id)
```

## 7. セキュリティ考慮事項

### 7.1 エラーメッセージの情報漏洩防止
本番環境では、詳細なエラー情報を外部に露出しない

```python
if settings.DEBUG:
    error_detail = str(exception)
else:
    error_detail = "内部エラーが発生しました。サポートにお問い合わせください。"
```

### 7.2 パスワード関連エラー
認証失敗時は、IDとパスワードのどちらが間違っているか明示しない

```python
# 悪い例
if not user_exists:
    raise AuthError("ユーザーが存在しません")
elif not password_match:
    raise AuthError("パスワードが間違っています")

# 良い例
if not user_exists or not password_match:
    raise AuthError("IDまたはパスワードが正しくありません")
```
