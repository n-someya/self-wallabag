# Wallabag Docker セットアップレポート

## プロジェクト概要

このレポートでは、Wallabagを自己ホスティングするためのDockerコンテナセットアップ作業の試行錯誤と最終解決策をまとめています。目標は、API Key認証とOAuth認証を適切に構成し、Google Cloud Runでのホスティングを見据えた安全なセットアップを行うことです。

## 直面した主な課題

1. **PostgreSQLデータベース接続問題**
   - テーブルが作成されていないエラー
   - ポート競合の問題（5432ポートが既に使用中）

2. **Dockerfile構成の問題**
   - パスの不一致
   - セキュリティヘッダー設定のエスケープ問題

3. **初期データベース構成とスキーマ作成**
   - 必要なテーブルが自動作成されない問題
   - 初期設定データが投入されていない問題

## 試行錯誤の過程

### 初回アプローチ

最初に既存の設定ファイルの確認と以下の問題を特定しました：
- `build-wallabag.sh`スクリプトのパス問題
- Dockerfileでのセキュリティヘッダー設定の問題
- PostgreSQLのポート競合

### 解決までの主なステップ

1. **Docker構成の修正**
   - PostgreSQLポートを5433に変更（競合回避）
   - セキュリティヘッダー設定を別ファイルに分離

2. **データベーススキーマとデータの設定**
   - `doctrine:schema:update --force`コマンドでテーブル作成
   - `wallabag:install`コマンドで初期設定データを投入
   
   **実施手順：**
   
   1. Dockerコンテナに入る：
      ```bash
      docker-compose exec wallabag bash
      ```
      
   2. Dockerコンテナ内でデータベーススキーマを更新：
      ```bash
      bin/console doctrine:schema:update --force
      ```
      このコマンドは、設定されたデータベース（PostgreSQL）にWallabagで必要なテーブルをすべて作成します。
      正常に完了すると「Successfully updated database schema」などのメッセージが表示されます。
      
   3. Wallabagの初期設定データを投入：
      ```bash
      bin/console wallabag:install
      ```
      このコマンドは対話形式で実行され、以下の項目の設定を促されます：
      - デフォルトユーザー作成（ユーザー名、パスワード、メールアドレス）
      - クライアントアプリケーション用のOAuth設定
      - デフォルトのタグやエントリ
      
   4. 初期データ投入の確認：
      ```bash
      bin/console doctrine:query:sql "SELECT * FROM wallabag_user LIMIT 5"
      ```
      このコマンドで、ユーザーテーブルにデータが正常に投入されたことを確認できます。
      
   **トラブルシューティング：**
   
   - テーブルが存在しないエラー → `doctrine:schema:update --dump-sql`で実行されるSQLを確認
   - 権限エラー → データベースユーザーに適切な権限が付与されているか確認
   - タイムアウトエラー → データベース接続設定（特にホスト名）を確認

3. **公式Wallabagイメージでの検証**
   - 構成問題を切り分けるため公式イメージを試用
   - 必要な環境変数の整理とマッピング

## 最終的な解決策

最終的に、公式Wallabagイメージを使用した`docker-compose.yml`で成功しました：

```yaml
version: '3'

services:
  db:
    image: postgres:14-alpine
    environment:
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_USER=postgres
      - POSTGRES_DB=wallabag
    volumes:
      - postgres:/var/lib/postgresql/data
    networks:
      - internal_network

  wallabag:
    image: wallabag/wallabag:latest
    environment:
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_USER=postgres
      - POSTGRES_HOST=db
      - SYMFONY__ENV__DATABASE_DRIVER=pdo_pgsql
      - SYMFONY__ENV__DATABASE_HOST=db
      - SYMFONY__ENV__DATABASE_PORT=5432
      - SYMFONY__ENV__DATABASE_NAME=wallabag
      - SYMFONY__ENV__DATABASE_USER=postgres
      - SYMFONY__ENV__DATABASE_PASSWORD=postgres
      - SYMFONY__ENV__SECRET=mysecretstring
      - SYMFONY__ENV__DOMAIN_NAME=http://localhost:8080
    ports:
      - "8080:80"
    volumes:
      - wallabag_images:/var/www/wallabag/web/assets/images
      - wallabag_data:/var/www/wallabag/data
    networks:
      - internal_network
    depends_on:
      - db

volumes:
  postgres:
  wallabag_images:
  wallabag_data:

networks:
  internal_network:
    driver: bridge
```

## 検証済み機能

1. **基本機能**
   - Webインターフェースへのアクセス確認（http://localhost:8080）
   - ユーザー認証（デフォルト認証情報: wallabag/wallabag）
   - クイックスタートページの表示

2. **API機能**
   - OAuth/API設定が適切に構成されていることを確認
   - API Clients管理画面でクライアント作成が可能
   - API認証の基本動作確認

3. **セキュリティ設定**
   - デフォルトのセキュリティヘッダー設定が適用されている
   - API Key認証が有効化されている

## Google Cloud Run向けの注意点

Google Cloud Runでホスティングするには以下の対応が必要です：

1. データベース接続設定
   - Supabase PostgreSQLへの接続文字列を適切に設定
   - SSL接続設定を有効にする

2. 環境変数の適切な設定
   - API KeyやOAuth用のシークレットを安全に管理
   - 外部URLの適切な設定

3. セキュリティヘッダーの設定
   - インターネット公開に適した強力なセキュリティヘッダー設定
   - API Key認証の適切な構成

## OAuth設定方法

Wallabag APIを利用するためのOAuth設定は以下の手順で行います：

1. **OAuthクライアントの作成**:
   - Wallabagのウェブインターフェースにログイン
   - 開発者向けのページにアクセス: `https://[あなたのwallabagドメイン]/developer/client/create`
   - アプリケーションのリダイレクトURLを入力（デスクトップアプリケーションの場合は任意のURLで可）
   - 「クライアントを作成」ボタンをクリック

2. **生成された認証情報の保存**:
   ```
   Client ID: [生成されたID]
   Client secret: [生成されたシークレット]
   ```

3. **認証情報の使用方法**:
   - これらの認証情報はアクセストークン取得時に使用
   - OAuthクライアント設定は環境変数では行えず、UIを通じてのみ操作可能

4. **有効期限の設定（オプション）**:
   - Docker環境変数で有効期限を設定可能
   ```
   -e SYMFONY__ENV__FOS_OAUTH_SERVER_ACCESS_TOKEN_LIFETIME=3600
   -e SYMFONY__ENV__FOS_OAUTH_SERVER_REFRESH_TOKEN_LIFETIME=1209600
   ```

## API Key（アクセストークン）設定方法

WallabagのAPI Keyは、OAuthのアクセストークンとして実装されています：

1. **アクセストークンの取得**:
   ```bash
   curl -s "https://[あなたのwallabagドメイン]/oauth/v2/token?grant_type=password&client_id=[Client ID]&client_secret=[Client Secret]&username=[あなたのユーザー名]&password=[あなたのパスワード]"
   ```

2. **レスポンス例**:
   ```json
   {
       "access_token": "ZGJmNTA2MDdmYTdmNWFiZjcxOWY3MWYyYzkyZDdlNWIzOTU4NWY3NTU1MDFjOTdhMTk2MGI3YjY1ZmI2NzM5MA",
       "expires_in": 3600,
       "refresh_token": "OTNlZGE5OTJjNWQwYzc2NDI5ZGE5MDg3ZTNjNmNkYTY0ZWZhZDVhNDBkZTc1ZTNiMmQ0MjQ0OThlNTFjNTQyMQ",
       "scope": null,
       "token_type": "bearer"
   }
   ```

3. **API呼び出しでの使用方法**:
   ```bash
   curl -H "Authorization: Bearer [access_token]" \
        https://[あなたのwallabagドメイン]/api/entries.json
   ```

4. **アクセストークンの更新**:
   - アクセストークンはデフォルトで1時間（3600秒）有効
   - 期限切れ後はリフレッシュトークンを使って新しいアクセストークンを取得
   ```bash
   curl -s "https://[あなたのwallabagドメイン]/oauth/v2/token?grant_type=refresh_token&client_id=[Client ID]&client_secret=[Client Secret]&refresh_token=[Refresh Token]"
   ```

## ユーザー管理と認証設定に関する調査報告

### 1. Wallabagのユーザー管理アーキテクチャ

Wallabagのユーザー管理システムは以下のコンポーネントで構成されています：

- **FOS UserBundle**：シンプルかつ拡張可能なユーザー管理を提供するSymfonyバンドル
- **User Entity**：`src/Entity/User.php`に定義されたユーザーデータモデル
- **2要素認証**：Scheb TwoFactorBundle を使用した多要素認証
- **OAuth**：API認証のためのFOSOAuthServerBundleを使用

### 2. 認証方式

Wallabagは以下の認証方式をサポートしています：

#### 2.1 標準認証
- ユーザー名/メールアドレス + パスワード認証
- `security.yml`でフォームログインとして構成
- セッションベースの認証（Cookieを使用）

#### 2.2 2要素認証（2FA）
- メールベースの2FA
- Google Authenticatorベースの2FA
- バックアップコード機能
- 設定方法：ユーザー設定画面から有効化可能

設定例（パラメータ）：
```yaml
twofactor_auth: true
twofactor_sender: no-reply@example.com
```

#### 2.3 OAuth認証（API用）
- OAuth 2.0プロトコルに準拠
- クライアントID/シークレットによる認証
- アクセストークン/リフレッシュトークンシステム
- 有効期限の設定が可能

### 3. 強固な認証のための構成ベストプラクティス

#### 3.1 パスワードポリシー強化
- 強力なパスワードポリシーを実装する（8文字以上、特殊文字/数字を含む）
- パスワード変更強制期間を設定する（環境に応じて）

#### 3.2 2要素認証の有効化
環境変数での設定方法：
```yaml
SYMFONY__ENV__SCHEB_TWO_FACTOR_GOOGLE__ENABLED: true
SYMFONY__ENV__SCHEB_TWO_FACTOR_EMAIL__ENABLED: true
SYMFONY__ENV__SCHEB_TWO_FACTOR_TRUSTED_DEVICE__ENABLED: true
SYMFONY__ENV__SCHEB_TWO_FACTOR_BACKUP_CODES__ENABLED: true
```

#### 3.3 API認証のセキュリティ強化
- アクセストークンの有効期限を適切に設定（本番環境では短めに）
- リフレッシュトークンの有効期限も適切に管理
- クライアントごとに権限を適切に制限

設定例：
```yaml
SYMFONY__ENV__FOS_OAUTH_SERVER_ACCESS_TOKEN_LIFETIME: 1800  # 30分
SYMFONY__ENV__FOS_OAUTH_SERVER_REFRESH_TOKEN_LIFETIME: 604800  # 1週間
```

### 4. 外部認証連携の実装方法

Wallabagは標準では外部認証プロバイダとの連携機能が組み込まれていませんが、以下の方法で実装可能です：

#### 4.1 OAuth/OIDC連携

Wallabagは直接的なOAuth/OIDCクライアント連携をネイティブにサポートしていませんが、カスタマイズによる実装は可能です：

1. **HWIOAuthBundle導入アプローチ**
   - Symfony HWIOAuthBundleを追加でインストール
   - Google、GitHub、Microsoft等のプロバイダ設定
   - FOSUserBundleと連携するコードの開発

カスタマイズ例（PHP）：
```php
// src/Security/GoogleAuthenticator.php
namespace App\Security;

use KnpU\OAuth2ClientBundle\Client\ClientRegistry;
use KnpU\OAuth2ClientBundle\Security\Authenticator\OAuth2Authenticator;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\Security\Core\User\UserProviderInterface;
// ...

class GoogleAuthenticator extends OAuth2Authenticator
{
    // OAuth認証の実装コード
}
```

#### 4.2 リバースプロキシ認証

Wallabagをリバースプロキシの背後に配置し、プロキシレベルで認証を行う方法：

1. **Keycloak + OAuth Proxy**
   - Keycloakで認証基盤を構築
   - OAuth Proxyを使ってWallabagへのアクセスを保護
   - ヘッダーを適切に転送してユーザー情報を維持

2. **CloudflareのAccess**
   - Cloudflare Accessでアクセス制御
   - JWTトークンを検証してアクセス許可

### 5. セキュリティ強化のためのベストプラクティス

#### 5.1 インフラストラクチャレベル
- TLS/SSL通信の強制（HTTPS Only）
- セキュリティヘッダーの適切な設定
  - Content-Security-Policy
  - X-Frame-Options
  - X-XSS-Protection

#### 5.2 アプリケーションレベル
- セッション管理の強化
  - セッションのHTTP Only + Secure設定
  - 適切なセッションライフタイム
  - CSRF保護の確実な実装

#### 5.3 デプロイメント設定
Google Cloud Run向けセキュリティ設定例：
```yaml
# セキュリティ関連の環境変数
- SYMFONY__ENV__SECRET=長くランダムな文字列
- SYMFONY__ENV__CSRF_PROTECTION=true
- SYMFONY__ENV__TRUSTED_PROXIES=10.0.0.0/8,172.16.0.0/12,192.168.0.0/16
```

## コンソールからのユーザー管理

Wallabagはコンソールから直接ユーザーを管理するための豊富なコマンドラインツールを提供しています。これらは`bin/console`経由で実行できます。本番環境では`--env=prod`オプションを追加してください。

### ユーザー作成・管理コマンド

#### 1. ユーザー作成
```bash
# 基本的なユーザー作成
bin/console fos:user:create

# パラメータを直接指定してユーザー作成
bin/console fos:user:create username user@example.com password
```

#### 2. ユーザー情報の表示・一覧
```bash
# 特定ユーザーの詳細表示
bin/console wallabag:user:show username

# ユーザー一覧の表示
bin/console wallabag:user:list

# 検索条件付きユーザー一覧
bin/console wallabag:user:list searchterm
```

#### 3. ユーザー権限の管理
```bash
# 管理者権限の付与
bin/console fos:user:promote username ROLE_SUPER_ADMIN

# 管理者権限の削除
bin/console fos:user:demote username ROLE_SUPER_ADMIN
```

#### 4. アカウント管理
```bash
# アカウントの有効化
bin/console fos:user:activate username

# アカウントの無効化
bin/console fos:user:deactivate username

# パスワードの変更
bin/console fos:user:change-password username newpassword
```

### Dockerコンテナ内での実行方法

Dockerコンテナ内でコマンドを実行するには：

```bash
# コンテナに入る
docker-compose exec wallabag bash

# コンテナ内でコマンドを実行
bin/console fos:user:create

# または直接外部から実行
docker-compose exec wallabag bin/console fos:user:create
```

### トラブルシューティング

- コマンド実行時に「Command not found」エラーが出る場合：正しいディレクトリにいるか確認
- 権限エラーが出る場合：適切な実行権限があるか確認
- データベース接続エラーが出る場合：環境変数やデータベース設定を確認

## まとめ

Wallabagは柔軟なユーザー管理機能を備えており、標準認証、2要素認証、OAuthベースのAPI認証をサポートしています。コンソールコマンドを使用することで、ユーザーの作成や管理を効率的に行うことができます。より強固なセキュリティを実現するためには、2要素認証の有効化、適切なパスワードポリシーの実装、アクセストークンの有効期限設定が重要です。

外部認証連携については、標準では組み込まれていませんが、HWIOAuthBundleの追加やリバースプロキシを使用した認証の実装が可能です。本番環境では、TLS/SSL通信の強制、適切なセキュリティヘッダーの設定、セッション管理の強化などを行い、総合的なセキュリティ対策を施すことが推奨されます。

---

## Google Cloud Run本番デプロイ（2025-12-06）

### 目標

ローカルで動作確認済みのWallabagをSupabase PostgreSQLと連携させ、Google Cloud Runで本格運用を開始する。

### 実施内容

#### 1. Supabase PostgreSQL接続の構成

**課題**:
- 既存のTerraform設定では間違ったSupabaseホスト（`db.xxxxxxxxxxxxxxxxxxxxxxx.supabase.co`）が使用されていた
- 正しいホストは`aws-0-ap-northeast-1.pooler.supabase.com`
- Wallabagの公式イメージのentrypointスクリプトが特殊な環境変数の組み合わせを要求

**解決策**:
1. 接続テストで正しいホスト名を特定
   ```bash
   psql "postgresql://postgres.xxxxxxxxxxxxxxxxxxxxxxx:PASSWORD@aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres?sslmode=require"
   ```

2. 専用データベース`wallabag_db`を作成
   ```bash
   CREATE DATABASE wallabag_db;
   ```

3. 環境変数を正しく設定
   - `POSTGRES_USER`: `postgres.xxxxxxxxxxxxxxxxxxxxxxx`（プロジェクトIDを含む完全な形式）
   - `PGDATABASE`: `postgres`（接続テスト用のデフォルトDB）
   - `SYMFONY__ENV__DATABASE_NAME`: `wallabag_db`（実際のアプリケーション用DB）
   - `POPULATE_DATABASE`: `False`（手動でマイグレーションを実行するため）

#### 2. ローカルでのSupabase接続テスト

[docker-compose.supabase.yml](docker-compose.supabase.yml)を作成し、ローカルからSupabaseに接続：

```yaml
services:
  wallabag:
    image: wallabag/wallabag:latest
    environment:
      # Supabase PostgreSQL connection
      - POSTGRES_HOST=aws-0-ap-northeast-1.pooler.supabase.com
      - POSTGRES_PORT=5432
      - POSTGRES_USER=postgres.xxxxxxxxxxxxxxxxxxxxxxx
      - POSTGRES_PASSWORD=***********************************
      - PGDATABASE=postgres
      - POPULATE_DATABASE=False

      # Symfony database configuration
      - SYMFONY__ENV__DATABASE_DRIVER=pdo_pgsql
      - SYMFONY__ENV__DATABASE_HOST=aws-0-ap-northeast-1.pooler.supabase.com
      - SYMFONY__ENV__DATABASE_PORT=5432
      - SYMFONY__ENV__DATABASE_NAME=wallabag_db
      - SYMFONY__ENV__DATABASE_USER=postgres.xxxxxxxxxxxxxxxxxxxxxxx
      - SYMFONY__ENV__DATABASE_PASSWORD=***********************************
      - SYMFONY__ENV__DATABASE_CHARSET=utf8
      - SYMFONY__ENV__DATABASE_DRIVER_OPTIONS={"sslmode":"require"}
```

#### 3. データベースマイグレーション

コンテナ起動後、手動でWallabagをインストール：

```bash
docker-compose -f docker-compose.supabase.yml exec wallabag \
  bin/console wallabag:install --env=prod --no-interaction
```

実行結果：
```
Step 1 of 4: Checking system requirements.
✓ PDO Driver (pdo_pgsql)   OK!
✓ Database connection      OK!
✓ Database version         OK!

Step 2 of 4: Setting up database.
Database successfully setup.

Step 3 of 4: Administration setup.
Administration successfully setup.

Step 4 of 4: Config setup.
Config successfully setup.

[OK] wallabag has been successfully installed.
```

デフォルトユーザー：
- ユーザー名: `wallabag`
- パスワード: `wallabag`

#### 4. Dockerイメージのプッシュ

既存のArtifact Registryリポジトリを確認：
```bash
gcloud artifacts repositories describe wallabag \
  --project=YOUR_GCP_PROJECT_ID --location=us-central1
```

公式Wallabagイメージをタグ付けしてプッシュ：
```bash
docker tag wallabag/wallabag:latest \
  us-central1-docker.pkg.dev/YOUR_GCP_PROJECT_ID/wallabag/wallabag:latest

docker push \
  us-central1-docker.pkg.dev/YOUR_GCP_PROJECT_ID/wallabag/wallabag:latest
```

#### 5. Terraform設定の更新

**[backend/src/terraform/terraform.tfvars](backend/src/terraform/terraform.tfvars)**を更新：

```hcl
# Supabase Configuration
supabase_host             = "aws-0-ap-northeast-1.pooler.supabase.com"
supabase_port             = 5432
supabase_db_password      = "***********************************"

# Database Connection Information
env_vars = {
  "SYMFONY__ENV__DATABASE_HOST"           = "aws-0-ap-northeast-1.pooler.supabase.com"
  "SYMFONY__ENV__DATABASE_NAME"           = "wallabag_db"
  "SYMFONY__ENV__DATABASE_USER"           = "postgres.xxxxxxxxxxxxxxxxxxxxxxx"
  "SYMFONY__ENV__DATABASE_DRIVER_OPTIONS" = "{\"sslmode\":\"require\"}"
  "POSTGRES_USER"                         = "postgres.xxxxxxxxxxxxxxxxxxxxxxx"
  "PGDATABASE"                            = "postgres"
  "POPULATE_DATABASE"                     = "False"
}

# Container Image
container_image = "us-central1-docker.pkg.dev/YOUR_GCP_PROJECT_ID/wallabag/wallabag:latest"
```

**[backend/src/terraform/main.tf](backend/src/terraform/main.tf)**の修正：
- 重複していたSupabase関連のlocal変数を削除
- `env_vars`変数から直接設定を取得するように変更

**[backend/src/terraform/outputs.tf](backend/src/terraform/outputs.tf)**の修正：
- 存在しないlocal変数への参照を修正
- `var.env_vars`から直接値を取得

**[backend/src/terraform/iam.tf](backend/src/terraform/iam.tf)**の修正：
- `google_cloud_run_service_iam_policy.api_auth`をコメントアウト
- `google_cloud_run_service_iam_member.api_endpoints`をコメントアウト
- `cloud_run.tf`の`noauth`ポリシーとの競合を回避

#### 6. Google Cloud Runへのデプロイ

Terraformでデプロイを実行：

```bash
terraform init
terraform plan
terraform apply -auto-approve
```

デプロイ結果：
- サービスURL: **https://your-service-XXXXXXXXXX-xx.a.run.app**
- リージョン: `us-central1`
- イメージ: `us-central1-docker.pkg.dev/YOUR_GCP_PROJECT_ID/wallabag/wallabag:latest`

#### 7. 動作確認

サービスの稼働確認：

```bash
# HTTPレスポンスコード確認
curl -s -o /dev/null -w "%{http_code}" https://your-service-XXXXXXXXXX-xx.a.run.app
# 結果: 302 (正常なリダイレクト)

# ページタイトル確認
curl -sL https://your-service-XXXXXXXXXX-xx.a.run.app | grep -o "<title>.*</title>"
# 結果: <title>Welcome to wallabag! – wallabag</title>
```

ログ確認：
```bash
gcloud run services logs read wallabag \
  --region=us-central1 --project=YOUR_GCP_PROJECT_ID --limit=20
```

ログ出力（抜粋）：
```
2025-12-06 06:49:09 [OK] All assets were successfully installed.
2025-12-06 06:49:09 wallabag is ready!
2025-12-06 06:54:25 GET 302 https://your-service-XXXXXXXXXX-xx.a.run.app/
2025-12-06 06:54:33 GET 200 https://your-service-XXXXXXXXXX-xx.a.run.app/login
```

### 本番環境の構成

#### アーキテクチャ

```
┌─────────────────────────────────────────┐
│   Google Cloud Run (us-central1)        │
│   ┌─────────────────────────────────┐   │
│   │  Wallabag Container             │   │
│   │  - Public Access Enabled        │   │
│   │  - Memory: 512Mi                │   │
│   │  - CPU: 1                       │   │
│   │  - Max Instances: 2             │   │
│   └─────────────┬───────────────────┘   │
└─────────────────┼───────────────────────┘
                  │
                  │ SSL/TLS
                  │ (sslmode=require)
                  ▼
┌─────────────────────────────────────────┐
│   Supabase PostgreSQL                   │
│   (aws-0-ap-northeast-1.pooler.supabase)│
│   ┌─────────────────────────────────┐   │
│   │  Database: wallabag_db          │   │
│   │  User: postgres.ggqgjhxtbwvd... │   │
│   │  Port: 5432                     │   │
│   └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

#### セキュリティ設定

1. **データベース接続**
   - SSL/TLS必須（`sslmode=require`）
   - 専用データベース（`wallabag_db`）使用
   - パスワードはGoogle Secret Managerで管理

2. **Cloud Run設定**
   - 公開アクセス有効（`allUsers`に`roles/run.invoker`権限）
   - サービスアカウント: `wallabag@YOUR_GCP_PROJECT_ID.iam.gserviceaccount.com`
   - Secret Managerアクセス権限付与

3. **監視とログ**
   - Cloud Monitoring有効
   - レスポンス遅延アラート（2秒超）
   - エラー率アラート（5%超）
   - Cloud Loggingで全リクエストログ記録

### トラブルシューティング履歴

#### 問題1: ホスト名解決エラー

**エラー**:
```
psql: error: could not translate host name "db.xxxxxxxxxxxxxxxxxxxxxxx.supabase.co" to address: Name does not resolve
```

**原因**: Supabaseの直接接続ホストではなく、Poolerホストを使用する必要があった

**解決**: `.env.example`に記載されていた正しいホスト名（`aws-0-ap-northeast-1.pooler.supabase.com`）を使用

#### 問題2: データベース名の解釈

**エラー**:
```
psql: error: connection to server ... failed: FATAL: database "postgres.xxxxxxxxxxxxxxxxxxxxxxx" does not exist
```

**原因**: Wallabagのentrypointスクリプトが`$POSTGRES_USER.$POSTGRES_DB`という形式でデータベース名を構築していた

**解決**:
- `PGDATABASE=postgres`環境変数を追加して接続テスト用DBを指定
- `SYMFONY__ENV__DATABASE_NAME=wallabag_db`で実際のアプリケーション用DBを指定

#### 問題3: マイグレーションエラー

**エラー**:
```
Unknown database type factor_type requested, Doctrine\DBAL\Platforms\PostgreSQL120Platform may not support it.
```

**原因**: Wallabagの古いマイグレーションとPostgreSQL 15の互換性問題

**解決**:
1. 専用データベース`wallabag_db`を新規作成
2. `POPULATE_DATABASE=False`で自動セットアップを無効化
3. コンテナ起動後に`bin/console wallabag:install`を手動実行

#### 問題4: Terraform IAMポリシー競合

**エラー**: `google_cloud_run_service_iam_policy.api_auth`と`noauth`ポリシーの競合

**解決**: `iam.tf`の認証ポリシーをコメントアウトし、`noauth`ポリシーのみ使用

### 成功要因

1. **段階的なアプローチ**
   - まずローカル環境でSupabase接続を確認
   - マイグレーションを検証してからCloud Runにデプロイ

2. **公式イメージの使用**
   - カスタムビルドではなく公式イメージ（`wallabag/wallabag:latest`）を使用
   - 実績のある設定で安定性を確保

3. **適切な環境変数設定**
   - Wallabagのentrypointスクリプトの動作を理解
   - 必要な環境変数を正確に設定

### 今後の改善点

1. **カスタムドメイン設定**
   - 現在は`*.run.app`ドメインを使用
   - 独自ドメインの設定で専門的な印象を向上

2. **バックアップ戦略**
   - Supabaseデータベースの定期バックアップ
   - Point-in-Time Recovery (PITR)の有効化

3. **モニタリング強化**
   - アプリケーションレベルのメトリクス追加
   - エラー通知チャネルの設定

4. **セキュリティ強化**
   - デフォルトユーザーのパスワード変更
   - 2要素認証の有効化推奨

### 結論

WallabagをSupabase PostgreSQLと連携させ、Google Cloud Runで正常に本格運用を開始できました。ローカル環境での十分な検証により、本番デプロイがスムーズに完了しました。

**本番URL**: https://your-service-XXXXXXXXXX-xx.a.run.app
**ログイン情報**: wallabag / wallabag（初回ログイン後に変更推奨）