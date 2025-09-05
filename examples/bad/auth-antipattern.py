"""
認証機能のアンチパターン集

⚠️ 警告: このコードは悪い例を示すためのものです。
実際のプロジェクトでは使用しないでください。
"""

# ❌ 悪い例1: ハードコードされた認証情報
API_KEY = "sk-1234567890abcdef"  # 絶対にやってはいけない！
DB_PASSWORD = "admin123"  # セキュリティ規約違反

# ❌ 悪い例2: 不適切な命名
def check(u, p):  # 意味不明な関数名と引数名
    usr = get_user(u)  # 不必要な略語
    if usr:
        # ❌ 悪い例3: パスワードの平文比較（最悪！）
        if usr.password == p:
            return True
    return False

# ❌ 悪い例4: エラーハンドリングの欠如
def login(email, password):
    try:
        # すべての例外を捕捉（範囲が広すぎる）
        user = User.objects.get(email=email)
        
        # ❌ 悪い例5: セキュリティ情報の露出
        if not user:
            return {"error": "ユーザーが存在しません"}  # 攻撃者に情報を提供
        
        if user.password != password:  # 平文パスワード！
            return {"error": "パスワードが間違っています"}  # 攻撃者に情報を提供
            
        # ❌ 悪い例6: 個人情報をログに出力
        print(f"User {email} logged in with password {password}")  # 絶対ダメ！
        
        # ❌ 悪い例7: 統一されていないレスポンスフォーマット
        return {
            "user_id": user.id,
            "email": email,
            "token": "some-token"  # 適当なトークン生成
        }
        
    except Exception as e:
        # ❌ 悪い例8: エラーの握りつぶし
        print(e)  # 適切なロギングをしていない
        return {"error": "エラーが発生しました"}

# ❌ 悪い例9: グローバル変数の濫用
current_user = None  # スレッドセーフではない

def set_current_user(user):
    global current_user
    current_user = user  # 危険！

# ❌ 悪い例10: SQL インジェクションの脆弱性
def get_user_by_email_unsafe(email):
    # 絶対にやってはいけない！
    query = f"SELECT * FROM users WHERE email = '{email}'"
    return db.execute(query)

# ❌ 悪い例11: Rate Limiting なし
def login_no_rate_limit(email, password):
    # ブルートフォース攻撃を許してしまう
    return authenticate(email, password)

# ❌ 悪い例12: 不適切なクラス名
class user_auth:  # PascalCaseを使っていない
    def __init__(self):
        self.Token = None  # 変数名が大文字で始まっている
    
    # ❌ 悪い例13: 長すぎる関数
    def DoEverything(self, email, password):  # 関数名も規約違反
        # 認証、トークン生成、ログ記録、メール送信...
        # 200行のコード（単一責任の原則違反）
        pass

# ❌ 悪い例14: マジックナンバー
def create_token(user_id):
    expiry = datetime.now() + timedelta(seconds=3600)  # 3600って何？
    
# ❌ 悪い例15: 未承認ライブラリの使用
import some_random_auth_lib  # セキュリティレビュー未実施

# ❌ 悪い例16: テストなしでの実装
# このファイルに対応するテストファイルが存在しない

# ❌ 悪い例17: エラーレスポンスの不統一
def bad_error_responses():
    # 場合によって異なるフォーマット
    return {"err": "失敗"}  # ある時
    return {"error_message": "失敗"}  # 別の時
    return {"status": "error", "msg": "失敗"}  # また別の時

# ❌ 悪い例18: 同期的なI/O処理
import time
def slow_auth(email, password):
    time.sleep(5)  # 非同期にすべき
    return authenticate(email, password)

# ❌ 悪い例19: リソースの適切な解放なし
def bad_db_connection():
    conn = get_db_connection()
    result = conn.execute("SELECT * FROM users")
    # conn.close() を忘れている
    return result

# ❌ 悪い例20: 本番環境へのデバッグコード
DEBUG = True  # 本番環境でTrueのまま！
if DEBUG:
    print(f"Password: {password}")  # 本番でパスワード出力

"""
これらのアンチパターンを避けることで、
セキュアで保守性の高いコードを書くことができます。

正しい実装例は auth_example.py を参照してください。
"""
