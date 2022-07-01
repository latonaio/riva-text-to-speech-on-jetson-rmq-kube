# riva-text-to-speech-on-jetson-rmq-kube
riva-text-to-speech-on-jetson-rmq-kube は、NVIDIA Rivaのテキスト音声合成（TTS）をJetsonにおいてKube上で実行するマイクロサービスです。  
音声合成するテキストはRabbitMQから受信します。

## 動作環境
- NVIDIA
    - JetPack 4.6.1
- Docker
- Kubernetes
- GNU Make
- RabbitMQ

## NVIDIA Rivaについて
NVIDIA Rivaは音声AIアプリケーションの構築、ユースケースに合わせたカスタマイズ、リアルタイムパフォーマンスの提供を実現するためのGPU-accelerated SDKです。

## インストール
以下のコマンドでRivaをインストールし、Riva Speech Serverを立ち上げることができます。  
詳細は[Quick Start Guide](https://docs.nvidia.com/deeplearning/riva/user-guide/docs/quick-start-guide.html)を参照してください。
```
initialize-riva-server: ## Quick Start Scripts のダウンロード、Riva Speech Server の立ち上げ
	ngc registry resource download-version nvidia/riva/riva_quickstart_arm64:2.1.0
	cd riva_quickstart_arm64_v2.1.0 && bash riva_init.sh && bash riva_start.sh
```
Dockerコンテナが起動するので「Ctrl+P」+「Ctrl+Q」でコンテナから抜けます。

## 動作手順
### Riva Speech Serverの立ち上げ
以下のコマンドでRiva Speech Serverを立ち上げます。  
ただし、すでに立ち上げている場合、この操作は不要です。
```
start-riva-server: ## Riva Speech Serverの立ち上げ（2回目以降）
	bash riva_quickstart_arm64_v2.1.0/riva_start.sh
```

### Docker イメージのビルド
以下のコマンドでRiva Speech TTSを動作させるためのDocker イメージをビルドします。
```
docker-build: ## Dockerイメージのビルド
	bash docker-build.sh
```

### 環境変数の設定
`deployment.yaml`の環境変数を設定します。

- RABBITMQ_URL：RabbitMQのURL
- QUEUE_ORIGIN：音声に変換するテキストが送られてくるキュー名
- DEVICE_ID：サウンドデバイスのid
- SERVER_ADDRESS：Riva Serverのアドレス（[Jetson IP address]:[Port number(A free port on Riva Speech Server)]）

接続されているデバイスの一覧は以下の2つのコマンドで確認できます。
```
docker-run: ## Dockerコンテナの立ち上げ
	docker-compose up -d

show-device-list: ## 接続されているdeviceの一覧を表示
	docker exec -it riva-text-to-speech python3 text-to-speech/device-list.py
```

### Kubernetes上で実行
以下のコマンドで、Deploymentを作成し、TTSを開始します。  
QUEUE_ORIGINから受信したメッセージが再生されます。
```
activate-tts: ## ttsの起動
	kubectl apply -f deployment.yaml
```

