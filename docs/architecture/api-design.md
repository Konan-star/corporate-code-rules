# API設計ガイドライン

## 1. 基本原則

- RESTful設計に準拠
- 一貫性のあるインターフェース
- 前方互換性の維持
- 適切なバージョニング

## 2. URL設計

### 2.1 基本構造
```
https://api.example.com/v1/{リソース名}/{リソースID}/{サブリソース}
```

### 2.2 命名規則
- **複数形**を使用（users, orders, products）
- **ケバブケース**を使用（user-profiles, order-items）
- 動詞は使わない（名詞のみ）

```
# 良い例
GET /v1/users
GET /v1/users/123
GET /v1/users/123/orders
POST /v1/orders

# 悪い例
GET /v1/getUsers
GET /v1/user  # 単数形
POST /v1/create-order  # 動詞を含む
```

## 3. HTTPメソッド

### 3.1 メソッドの使い分け
- **GET**: リソースの取得（冪等）
- **POST**: リソースの作成
- **PUT**: リソースの完全更新（冪等）
- **PATCH**: リソースの部分更新
- **DELETE**: リソースの削除（冪等）

### 3.2 レスポンスステータス
```python
# 成功
200 OK          # GET, PUT, PATCH の成功
201 Created     # POST の成功（リソース作成）
204 No Content  # DELETE の成功

# クライアントエラー
400 Bad Request # 不正なリクエスト
401 Unauthorized # 認証エラー
403 Forbidden    # 認可エラー
404 Not Found    # リソースが存在しない
409 Conflict     # 競合（重複など）

# サーバーエラー
500 Internal Server Error # サーバー内部エラー
503 Service Unavailable  # 一時的なサービス停止
```

## 4. レスポンスフォーマット

### 4.1 統一フォーマット（必須）
すべてのAPIレスポンスは以下の形式に従う：

```json
{
    "data": {
        // 実際のレスポンスデータ
    },
    "error": null,
    "meta": {
        "request_id": "550e8400-e29b-41d4-a716-446655440000",
        "timestamp": "2024-01-15T09:30:00Z",
        "version": "1.0"
    }
}
```

### 4.2 成功レスポンスの例
```json
// 単一リソース
{
    "data": {
        "id": "123",
        "name": "田中太郎",
        "email": "tanaka@example.com",
        "created_at": "2024-01-15T09:30:00Z"
    },
    "error": null,
    "meta": {
        "request_id": "550e8400-e29b-41d4-a716-446655440000"
    }
}

// 複数リソース
{
    "data": {
        "items": [
            {"id": "1", "name": "商品A"},
            {"id": "2", "name": "商品B"}
        ],
        "total_count": 150,
        "page": 1,
        "per_page": 20
    },
    "error": null,
    "meta": {
        "request_id": "550e8400-e29b-41d4-a716-446655440000"
    }
}
```

### 4.3 エラーレスポンスの例
```json
{
    "data": null,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "入力値が不正です",
        "details": {
            "email": "有効なメールアドレスを入力してください"
        }
    },
    "meta": {
        "request_id": "550e8400-e29b-41d4-a716-446655440000"
    }
}
```

## 5. バージョニング（必須）

### 5.1 URLパスベース
```
https://api.example.com/v1/users
https://api.example.com/v2/users
```

### 5.2 バージョン管理ポリシー
- メジャーバージョンのみURLに含める（v1, v2）
- 後方互換性のない変更時のみバージョンアップ
- 古いバージョンは最低1年間サポート

## 6. ページネーション（必須）

### 6.1 limit/offset 方式
リストAPIには必ずページネーションを実装：

```
GET /v1/users?limit=20&offset=40

レスポンス：
{
    "data": {
        "items": [...],
        "total_count": 150,
        "limit": 20,
        "offset": 40,
        "has_next": true,
        "has_previous": true
    }
}
```

### 6.2 デフォルト値
- limit のデフォルト: 20
- limit の最大値: 100

## 7. フィルタリングとソート

### 7.1 フィルタリング
```
GET /v1/users?status=active&created_after=2024-01-01
```

### 7.2 ソート
```
GET /v1/users?sort=created_at&order=desc
```

## 8. 認証と認可

### 8.1 認証方式
Bearer トークンを使用：
```
Authorization: Bearer <access_token>
```

### 8.2 Rate Limiting
レスポンスヘッダーに必ず含める：
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## 9. データ形式

### 9.1 日時フォーマット
ISO 8601 形式（UTC）を使用：
```
2024-01-15T09:30:00Z
```

### 9.2 NULL値の扱い
- 値が存在しない場合は `null` を返す
- 空配列と `null` を区別する

## 10. セキュリティ

### 10.1 HTTPS必須
すべてのAPIエンドポイントはHTTPSでのみ提供

### 10.2 CORS設定
必要最小限のオリジンのみ許可

### 10.3 入力検証
すべての入力パラメータを検証

## 11. 企業固有のルール

### 11.1 監査ログ
すべてのAPIアクセスをログに記録：
- アクセス時刻
- ユーザーID
- IPアドレス
- リクエスト内容（機密情報は除外）

### 11.2 APIドキュメント
- OpenAPI 3.0 仕様で記述
- Swagger UIで閲覧可能にする
- 実装と同時にドキュメントを更新

### 11.3 新規エンドポイントの承認
新規APIエンドポイントの追加には、アーキテクチャチームのレビューと承認が必要です。

## 12. パフォーマンス要件

### 12.1 レスポンスタイム
- 単一リソース取得: 200ms以内
- リスト取得: 500ms以内
- リソース作成/更新: 300ms以内

### 12.2 キャッシュ
適切なキャッシュヘッダーを設定：
```
Cache-Control: private, max-age=300
ETag: "33a64df551425fcc55e4d42a1"
```
