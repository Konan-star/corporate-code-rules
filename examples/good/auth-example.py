"""
認証機能の実装例（推奨パターン）

このモジュールは、社内コーディング規約に準拠した
認証機能の実装例を示しています。
"""
import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
import jwt
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.models import User
from app.exceptions import (
    AuthenticationError,
    AuthorizationError,
    UserNotFoundException,
    BaseApplicationError
)

# ロガーの設定（規約: __name__ を使用）
logger = logging.getLogger(__name__)

# セキュリティスキーム
security = HTTPBearer()


class AuthService:
    """認証サービスクラス"""
    
    def __init__(self):
        self.jwt_secret = settings.JWT_SECRET_KEY
        self.jwt_algorithm = "HS256"
        self.access_token_expire_minutes = 60
        self.refresh_token_expire_days = 7
    
    async def authenticate_user(
        self,
        email: str,
        password: str,
        trace_id: str
    ) -> dict:
        """
        ユーザー認証を行う
        
        Args:
            email: メールアドレス
            password: パスワード（平文）
            trace_id: トレースID
            
        Returns:
            認証成功時のユーザー情報とトークン
            
        Raises:
            AuthenticationError: 認証失敗時
        """
        try:
            # ユーザーの取得
            user = await self._get_user_by_email(email, trace_id)
            
            # パスワード検証（bcryptを使用）
            if not self._verify_password(password, user.password_hash):
                # セキュリティ規約: IDとパスワードどちらが違うか明示しない
                logger.warning(
                    "Authentication failed",
                    extra={
                        "trace_id": trace_id,
                        "user_id": user.id if user else None,
                        "error_type": "invalid_credentials"
                    }
                )
                raise AuthenticationError(
                    "IDまたはパスワードが正しくありません",
                    error_code="AUTH_001",
                    trace_id=trace_id
                )
            
            # アクセストークンとリフレッシュトークンの生成
            access_token = self._create_access_token(user.id)
            refresh_token = self._create_refresh_token(user.id)
            
            logger.info(
                "User authenticated successfully",
                extra={
                    "trace_id": trace_id,
                    "user_id": user.id
                }
            )
            
            # API設計規約: 統一レスポンスフォーマット
            return {
                "data": {
                    "user": {
                        "id": str(user.id),
                        "email": user.email,
                        "name": user.name
                    },
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "token_type": "bearer"
                },
                "error": None,
                "meta": {
                    "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            }
            
        except UserNotFoundException:
            # ユーザーが見つからない場合も同じエラーメッセージ
            raise AuthenticationError(
                "IDまたはパスワードが正しくありません",
                error_code="AUTH_001",
                trace_id=trace_id
            )
        except Exception as e:
            logger.error(
                "Unexpected error during authentication",
                extra={
                    "trace_id": trace_id,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    async def _get_user_by_email(
        self,
        email: str,
        trace_id: str
    ) -> User:
        """メールアドレスからユーザーを取得"""
        user = await User.get_by_email(email)
        if not user:
            raise UserNotFoundException(
                f"User not found",
                error_code="USER_001",
                trace_id=trace_id
            )
        return user
    
    def _verify_password(
        self,
        plain_password: str,
        hashed_password: str
    ) -> bool:
        """パスワードの検証（bcrypt使用）"""
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    
    def _create_access_token(self, user_id: str) -> str:
        """アクセストークンの生成"""
        payload = {
            "sub": user_id,
            "exp": datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes),
            "iat": datetime.utcnow(),
            "type": "access"
        }
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
    
    def _create_refresh_token(self, user_id: str) -> str:
        """リフレッシュトークンの生成"""
        payload = {
            "sub": user_id,
            "exp": datetime.utcnow() + timedelta(days=self.refresh_token_expire_days),
            "iat": datetime.utcnow(),
            "type": "refresh",
            "jti": secrets.token_urlsafe(32)  # ユニークなトークンID
        }
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
    
    async def verify_token(
        self,
        credentials: HTTPAuthorizationCredentials,
        trace_id: str
    ) -> str:
        """トークンの検証"""
        try:
            payload = jwt.decode(
                credentials.credentials,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm]
            )
            
            # トークンタイプの確認
            if payload.get("type") != "access":
                raise AuthorizationError(
                    "Invalid token type",
                    error_code="AUTH_002",
                    trace_id=trace_id
                )
            
            return payload["sub"]  # user_id
            
        except jwt.ExpiredSignatureError:
            raise AuthorizationError(
                "Token has expired",
                error_code="AUTH_003",
                trace_id=trace_id
            )
        except jwt.JWTError:
            raise AuthorizationError(
                "Invalid token",
                error_code="AUTH_004",
                trace_id=trace_id
            )


# Rate limiting decorator（企業規約: すべてのAPIにrate limiting実装）
from functools import wraps
from collections import defaultdict
from datetime import datetime
import asyncio

class RateLimiter:
    """レート制限の実装"""
    
    def __init__(self, max_attempts: int = 5, window: int = 300):
        self.max_attempts = max_attempts
        self.window = window  # 秒
        self.attempts = defaultdict(list)
        self._cleanup_task = None
    
    async def check_rate_limit(self, key: str) -> bool:
        """レート制限のチェック"""
        now = datetime.utcnow()
        
        # 古いエントリをクリーンアップ
        cutoff = now - timedelta(seconds=self.window)
        self.attempts[key] = [
            attempt for attempt in self.attempts[key]
            if attempt > cutoff
        ]
        
        # 制限チェック
        if len(self.attempts[key]) >= self.max_attempts:
            return False
        
        # 新しい試行を記録
        self.attempts[key].append(now)
        return True
    
    def __call__(self, func):
        """デコレータとして使用"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # リクエストからIPアドレスを取得（実装は省略）
            client_ip = kwargs.get("client_ip", "unknown")
            
            if not await self.check_rate_limit(client_ip):
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded"
                )
            
            return await func(*args, **kwargs)
        return wrapper


# 使用例
rate_limiter = RateLimiter(max_attempts=5, window=300)

@rate_limiter
async def login_endpoint(
    email: str,
    password: str,
    trace_id: str = None,
    client_ip: str = None
):
    """ログインエンドポイント（rate limiting適用）"""
    if not trace_id:
        trace_id = str(uuid.uuid4())
    
    auth_service = AuthService()
    return await auth_service.authenticate_user(email, password, trace_id)
