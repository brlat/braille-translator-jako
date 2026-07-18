# 日韓混在テキスト点字変換ツール (braille-translator-jako)

日本語と韓国語が混在するテキストを文字単位で自動判定し、それぞれの言語に適した点字エンジンを用いてユニコード点字（Unicode Braille Patterns: U+2800〜U+28FF）に変換する Python スクリプトです。

---

## 🛠 必要な環境設定

本ツールを実行するには、以下の環境設定が必要です。

### 1. C言語ライブラリ `liblouis` のインストール (必須)
韓国語の点字変換を行うため、システム側に `liblouis` の共有ライブラリがインストールされている必要があります。

*   **macOS (Homebrew)**:
    ```bash
    brew install liblouis
    ```
*   **Ubuntu / Debian**:
    ```bash
    sudo apt-get install liblouis-dev
    ```
*   **Windows**:
    [liblouis の公式サイト](https://liblouis.io/) または GitHub リリースからビルド済みのDLLを入手し、システム環境変数 `PATH` に含めるか、スクリプトと同じディレクトリに `liblouis.dll` を配置してください。

### 2. Python 環境
*   Python 3.8 以上

---

## 📦 インストール方法

1. このリポジトリをクローンするか、フォルダ内のファイルをダウンロードします。
2. フォルダ内で以下のコマンドを実行し、必要な Python 依存関係をインストールします。

```bash
pip install -r requirements.txt
```

*(※ 日本語の形態素解析・点字変換パッケージである `libkuraji` が辞書データ付きでインストールされます)*

---

## 🚀 使用方法

メインスクリプト `braille_translator.py` を使用して変換を行います。

### 1. コマンドライン引数から直接変換
```bash
python braille_translator.py "こんにちは 안녕하세요"
```
**出力:**
```text
⠪⠴⠇⠗⠄⠀⠣⠒⠉⠱⠶⠚⠣⠠⠝⠬
```
*(半角・全角スペースは、デフォルトで点字用の空白文字 `⠀` (U+2800) に自動的に統一されます)*

### 2. 標準入力（パイプ）から変換
```bash
echo "日本語と한국어が混ざったテストです。" | python braille_translator.py
```
**出力:**
```text
⠇⠮⠴⠐⠪⠞⠚⠣⠒⠈⠍⠁⠎⠐⠡⠀⠵⠐⠱⠂⠕⠀⠟⠹⠞⠐⠟⠹⠲
```

### 3. ファイルを指定して変換
`-f` / `--file` で入力ファイルを、`-o` / `--output` で出力ファイルを指定できます。
```bash
python braille_translator.py -f input.txt -o output.txt
```

### 4. オプション一覧
```text
$ python braille_translator.py --help
usage: braille_translator.py [-h] [-f FILE] [-o OUTPUT] [--keep-ascii-spaces] [-v] [text]

日本語と韓国語が混在するテキストをユニコード点字に変換します。

positional arguments:
  text                  変換するテキスト（省略した場合はファイル指定または標準入力から読み込みます）

options:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  変換するテキストファイルのパス
  -o OUTPUT, --output OUTPUT
                        出力ファイルパス（省略した場合は標準出力に書き出します）
  --keep-ascii-spaces   半角スペースを点字空白文字 (U+2800) に変換せず、そのまま残します
  -v, --verbose         チャンク分割などの詳細情報を標準エラー出力に表示します
```

---

## ⚖️ 著作権とライセンス (Copyright & Licenses)

### 本ツール (braille-translator-jako)
*   **ライセンス**: MIT License
*   **著作権**: Copyright (c) 2026 poohbear
*   詳細は [LICENSE](./LICENSE) ファイルを参照してください。

### 依存ソフトウェア・ライブラリのライセンス
本スクリプトは、以下の優れたオープンソースソフトウェアを利用しています。それぞれのライセンス条項が適用されます。

1.  **libkuraji** (日本語点字変換エンジン)
    *   **リポジトリ**: [nishimotz/libkuraji](https://github.com/nishimotz/libkuraji)
    *   **著作権**: Copyright (c) Takuya Nishimoto, NVDA Japanese Team.
    *   **ライセンス**: LGPL v2.1 or later
2.  **liblouis** (韓国語点字変換エンジン)
    *   **リポジトリ**: [liblouis/liblouis](https://github.com/liblouis/liblouis)
    *   **著作権**: Copyright (C) The Liblouis Authors.
    *   **ライセンス**: LGPL v2.1 or later (ライブラリ本体)
