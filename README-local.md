# Wallabag ローカル実行ガイド

このガイドでは、Google Cloud Runにデプロイされているwallabagアプリケーションをローカル環境で実行する方法を説明します。

## 前提条件

- Docker と Docker Compose がインストールされていること

## セットアップ手順

### 1. 簡単な起動方法

最も簡単な方法は、提供されている簡易セットアップスクリプトを使用することです：

```bash
chmod +x start-local-wallabag.sh
./start-local-wallabag.sh
```

このスクリプトは以下を行います：
1. 必要なdocker-compose設定を作成
2. PostgreSQLデータベースコンテナを起動
3. WallabagコンテナをPostgreSQLデータベースと連携して起動
4. アクセスURLとログイン情報の提供

### 2. 手動セットアップ

手動でセットアップする場合は、以下の手順に従います：

```bash
# docker-compose-local.ymlを作成（スクリプト内容を参照）

# コンテナを起動
docker-compose -f docker-compose-local.yml up -d
```

起動すると、以下のURLでアクセスできます：
http://localhost:8080

デフォルトのログイン情報：
- ユーザー名: wallabag
- パスワード: wallabag

> **注意**: 初回ログイン後、パスワードを変更することをお勧めします。

### 3. コンテナの停止

```bash
docker-compose -f docker-compose-local.yml down
```

## カスタムビルドの使用方法

カスタム設定でWallabagをビルドして使用したい場合は、以下の手順に従います：

1. 元のdocker-compose.yml設定を使用
2. .env ファイルを設定
3. docker-compose upコマンドで起動

## トラブルシューティング

問題が発生した場合は、以下のコマンドでコンテナのログを確認できます：

```bash
docker-compose -f docker-compose-local.yml logs wallabag
```

## 一般的な問題と解決策

### データベース接続エラー

Wallabagがデータベースに接続できない場合：

1. PostgreSQLコンテナが正常に実行されているか確認
2. データベース認証情報が正しいか確認
3. データベースが完全に初期化された後、Wallabagコンテナを再起動

### コンテナが起動しない

ログを確認してください：

```bash
docker-compose -f docker-compose-local.yml logs wallabag
```

### ログイン問題

デフォルトの認証情報：

- ユーザー名: wallabag
- パスワード: wallabag

これらが機能しない場合は、パスワードをリセットする必要があります：

```bash
docker-compose -f docker-compose-local.yml exec wallabag bin/console --env=prod wallabag:user:reset-password wallabag
```

### カスタム開発

コード修正を伴うローカル開発の場合：

1. volumeを使用してローカルコードをマウントします：

```yaml
volumes:
  - ./your-code-path:/var/www/wallabag
```

2. コンテナ内のwww-dataユーザーに対してファイルのアクセス権が正しく設定されていることを確認します。