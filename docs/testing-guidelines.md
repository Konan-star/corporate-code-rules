# テストガイドライン

## 1. テストの基本方針

- すべての新機能には対応するテストを作成する
- バグ修正時は、そのバグを再現するテストを先に作成する
- テストカバレッジは80%以上を維持する

## 2. テストの種類と責務

### 2.1 単体テスト（Unit Tests）
- 個々の関数やメソッドの動作を検証
- 外部依存はモック化
- 実行時間: 各テスト100ms以内

### 2.2 統合テスト（Integration Tests）
- 複数のコンポーネント間の連携を検証
- データベース接続を含む
- 実行時間: 各テスト1秒以内

### 2.3 E2Eテスト（End-to-End Tests）
- ユーザーシナリオ全体を検証
- 本番に近い環境で実行
- 実行時間: 制限なし

## 3. テストの命名規則

### 3.1 テストファイル名
- `test_` で開始
- テスト対象のモジュール名を含める

```python
# 対象: user_service.py
# テスト: test_user_service.py
```

### 3.2 テスト関数名
- `test_` で開始
- 何をテストしているか明確に記述
- 日本語コメントで補足可

```python
def test_create_user_with_valid_data():
    """正常なデータでユーザーを作成できること"""
    pass

def test_create_user_with_duplicate_email_raises_error():
    """重複したメールアドレスでエラーが発生すること"""
    pass
```

## 4. テストの構造

### 4.1 AAA パターン
すべてのテストは Arrange-Act-Assert パターンに従う

```python
def test_calculate_total_price():
    # Arrange（準備）
    items = [
        {"name": "商品A", "price": 1000, "quantity": 2},
        {"name": "商品B", "price": 500, "quantity": 1}
    ]
    
    # Act（実行）
    total = calculate_total_price(items)
    
    # Assert（検証）
    assert total == 2500
```

### 4.2 テストフィクスチャ
共通のテストデータはフィクスチャとして定義

```python
import pytest

@pytest.fixture
def sample_user():
    """テスト用ユーザーデータ"""
    return {
        "id": "test_user_123",
        "name": "テスト太郎",
        "email": "test@example.com"
    }

def test_user_update(sample_user):
    # sample_user を使用してテスト
    pass
```

## 5. モックとスタブ

### 5.1 外部サービスのモック
外部APIやサービスは必ずモック化

```python
from unittest.mock import Mock, patch

@patch('payment_service.charge')
def test_process_payment(mock_charge):
    # 成功レスポンスを設定
    mock_charge.return_value = {"status": "success", "transaction_id": "12345"}
    
    result = process_payment(user_id="user123", amount=1000)
    
    # モックが正しく呼ばれたことを確認
    mock_charge.assert_called_once_with(user_id="user123", amount=1000)
    assert result["success"] is True
```

### 5.2 時刻のモック
テストの再現性のため、現在時刻は固定

```python
from freezegun import freeze_time

@freeze_time("2024-01-15 10:00:00")
def test_create_timestamp():
    timestamp = create_timestamp()
    assert timestamp == "2024-01-15T10:00:00Z"
```

## 6. データベーステスト

### 6.1 テストデータベース
- 本番データベースとは完全に分離
- 各テスト実行前にクリーンな状態にリセット

### 6.2 トランザクション
各テストはトランザクション内で実行し、終了後にロールバック

```python
@pytest.fixture
def db_session():
    """テスト用データベースセッション"""
    session = create_test_session()
    yield session
    session.rollback()
    session.close()
```

## 7. 非同期処理のテスト

### 7.1 async/await のテスト
```python
import pytest
import asyncio

@pytest.mark.asyncio
async def test_async_fetch_user():
    user = await fetch_user_async("user123")
    assert user["id"] == "user123"
```

## 8. パフォーマンステスト

### 8.1 実行時間の検証
重要な処理には実行時間の上限を設定

```python
import time

def test_search_performance():
    start_time = time.time()
    
    results = search_users("test")
    
    execution_time = time.time() - start_time
    assert execution_time < 0.5  # 500ms以内
```

## 9. テストデータ

### 9.1 個人情報の取り扱い
- 本番データをテストで使用しない
- テストデータは明確に識別可能にする

```python
# 良い例
test_user = {
    "name": "テストユーザー001",
    "email": "test.user001@example.com"
}

# 悪い例
test_user = {
    "name": "山田太郎",  # 実在しそうな名前
    "email": "yamada@realcompany.co.jp"  # 実在しそうなドメイン
}
```

## 10. CI/CD 統合

### 10.1 プルリクエスト時
- すべてのテストが自動実行される
- カバレッジレポートが生成される
- テスト失敗時はマージ不可

### 10.2 テストの並列実行
- 単体テストは並列実行可能にする
- 統合テストは順次実行

## 11. 企業固有のルール

### 11.1 テストレビュー
- 本番コードと同様に、テストコードもレビュー対象
- 2名以上のレビュー承認が必要

### 11.2 セキュリティテスト
- 認証・認可に関わる機能は必ずセキュリティテストを含める
- SQLインジェクション、XSSなどの脆弱性テストを実施

```python
def test_sql_injection_prevention():
    """SQLインジェクション攻撃を防げること"""
    malicious_input = "'; DROP TABLE users; --"
    
    # エラーが発生するか、安全に処理されることを確認
    with pytest.raises(ValidationError):
        search_users(malicious_input)
```