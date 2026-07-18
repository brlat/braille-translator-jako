#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
日本語・韓国語混在テキストをユニコード点字に変換するスクリプト

依存関係:
- libkuraji (日本語点字エンジン)
- liblouis (韓国語点字エンジン: C言語の共有ライブラリがシステムに必要)

使用方法:
  python braille_translator.py "こんにちは 안녕하세요"
"""

import os
import sys
import argparse
import ctypes
import ctypes.util

# libkuraji の統合辞書機能を有効化する環境変数
os.environ["LIBKURAJI_INTEGRATION"] = "1"

try:
    import libkuraji
except ImportError:
    print("Error: 'libkuraji' package is not installed.", file=sys.stderr)
    print("Please install it using: pip install 'libkuraji[integration]'", file=sys.stderr)
    sys.exit(1)

# --- liblouis ctypes wrapper ---
def load_liblouis():
    lib_path = ctypes.util.find_library("louis")
    liblouis = None
    if not lib_path:
        # macOS (Homebrew) や Linux の一般的なフォールバックパス
        fallbacks = [
            "/opt/homebrew/lib/liblouis.dylib",
            "/usr/local/lib/liblouis.dylib",
            "liblouis.so",
            "liblouis.so.20",
            "liblouis.so.2",
        ]
        for path in fallbacks:
            try:
                liblouis = ctypes.CDLL(path)
                break
            except Exception:
                pass
    else:
        try:
            liblouis = ctypes.CDLL(lib_path)
        except Exception:
            pass
    return liblouis

liblouis = load_liblouis()
if liblouis is None:
    print("Error: liblouis shared library not found.", file=sys.stderr)
    print("Please install liblouis on your system.", file=sys.stderr)
    print("  macOS: brew install liblouis", file=sys.stderr)
    print("  Ubuntu/Debian: sudo apt-get install liblouis-dev", file=sys.stderr)
    sys.exit(1)

# ctypes 関数のシグネチャ設定
liblouis.lou_charSize.restype = ctypes.c_int
liblouis.lou_charSize.argtypes = ()

liblouis.lou_translateString.restype = ctypes.c_int
liblouis.lou_translateString.argtypes = (
    ctypes.c_char_p,                 # tableList
    ctypes.POINTER(ctypes.c_char),   # inbuf
    ctypes.POINTER(ctypes.c_int),    # inlen
    ctypes.POINTER(ctypes.c_char),   # outbuf
    ctypes.POINTER(ctypes.c_int),    # outlen
    ctypes.c_void_p,                 # typeform
    ctypes.c_void_p,                 # mainPos
    ctypes.c_int,                    # mode
)

# liblouis で使用する文字幅とエンコーディングの判定
wide_char_bytes = liblouis.lou_charSize()
endianness = "be" if sys.byteorder == "big" else "le"
conversion_encoding = f"utf_{wide_char_bytes * 8}_{endianness}"

def translate_korean_louis(text: str) -> str:
    """
    liblouis を使用して韓国語テキストを点字に変換する。
    テーブルには unicode.dis (ユニコード点字へのマッピング) と ko-2006-g1.ctb を指定。
    """
    tables = "unicode.dis,ko-2006-g1.ctb"
    tables_bytes = tables.encode("utf-8")
    
    inbuf_bytes = text.encode(conversion_encoding)
    inlen = ctypes.c_int(len(inbuf_bytes) // wide_char_bytes)
    
    # バッファ長は十分に確保する
    outlen_multiplier = 4 + wide_char_bytes * 2
    outlen_val = inlen.value * outlen_multiplier
    outlen = ctypes.c_int(outlen_val)
    outbuf_bytes = ctypes.create_string_buffer(outlen_val * wide_char_bytes)
    
    success = liblouis.lou_translateString(
        tables_bytes,
        inbuf_bytes,
        ctypes.byref(inlen),
        outbuf_bytes,
        ctypes.byref(outlen),
        None,
        None,
        0
    )
    
    if not success:
        raise RuntimeError(f"liblouis translation failed for: '{text}'")
        
    translated_bytes = outbuf_bytes.raw[:outlen.value * wide_char_bytes]
    return translated_bytes.decode(conversion_encoding, errors="surrogatepass")


# --- 言語判定とチャンク分割 ---
def is_hangul(char: str) -> bool:
    """文字がハングルブロックに含まれるか判定する"""
    cp = ord(char)
    return (
        (0xAC00 <= cp <= 0xD7A3) or      # Hangul Syllables
        (0x1100 <= cp <= 0x11FF) or      # Hangul Jamo
        (0x3130 <= cp <= 0x318F) or      # Hangul Compatibility Jamo
        (0xA960 <= cp <= 0xA97F) or      # Hangul Jamo Extended-A
        (0xD7B0 <= cp <= 0xD7FF)         # Hangul Jamo Extended-B
    )

def is_japanese_char(char: str) -> bool:
    """文字が日本語ブロック（ひらがな、カタカナ、漢字等）に含まれるか判定する"""
    cp = ord(char)
    return (
        (0x3040 <= cp <= 0x309F) or      # 平仮名
        (0x30A0 <= cp <= 0x30FF) or      # 片仮名
        (0x4E00 <= cp <= 0x9FFF) or      # CJK統合漢字
        (0x3000 <= cp <= 0x303F) or      # CJKの記号・句読点
        (0xFF65 <= cp <= 0xFF9F)         # 半角カタカナ
    )

def split_text_by_language(text: str):
    """
    テキストを日本語 (JAPANESE) と韓国語 (KOREAN) のチャンクに分割する。
    記号やスペースなどの中立的な文字 (NEUTRAL) は、文脈（前後の言語）に応じてマージする。
    """
    if not text:
        return []
    
    char_types = []
    for char in text:
        if is_hangul(char):
            char_types.append('KOREAN')
        elif is_japanese_char(char):
            char_types.append('JAPANESE')
        else:
            char_types.append('NEUTRAL')
            
    # 前方伝播：NEUTRALな文字は直前の言語の属性を引き継ぐ
    current_type = 'JAPANESE'  # デフォルト言語
    for i in range(len(text)):
        if char_types[i] != 'NEUTRAL':
            current_type = char_types[i]
        else:
            char_types[i] = current_type
            
    # 後方伝播：先頭のNEUTRALな文字は、最初に現れる非中立文字の言語を引き継ぐ
    first_non_neutral = None
    for i in range(len(text)):
        if is_hangul(text[i]):
            first_non_neutral = 'KOREAN'
            break
        elif is_japanese_char(text[i]):
            first_non_neutral = 'JAPANESE'
            break
            
    if first_non_neutral:
        for i in range(len(text)):
            if is_hangul(text[i]) or is_japanese_char(text[i]):
                break
            char_types[i] = first_non_neutral

    # 同じ言語属性で連続する部分をチャンクにまとめる
    chunks = []
    current_chunk = []
    current_type = char_types[0]
    
    for char, t in zip(text, char_types):
        if t == current_type:
            current_chunk.append(char)
        else:
            chunks.append((''.join(current_chunk), current_type))
            current_chunk = [char]
            current_type = t
            
    if current_chunk:
        chunks.append((''.join(current_chunk), current_type))
        
    return chunks


# --- メイン翻訳処理 ---
def translate_mixed_text(text: str, keep_ascii_spaces: bool = False, verbose: bool = False) -> str:
    """
    混在テキストを点字に変換する。
    """
    chunks = split_text_by_language(text)
    translated_chunks = []
    
    if verbose:
        print("[Verbose] Language chunks detected:", file=sys.stderr)
        for i, (content, lang) in enumerate(chunks):
            print(f"  Chunk {i}: Type={lang}, Content='{content}'", file=sys.stderr)
            
    for content, lang in chunks:
        if lang == 'KOREAN':
            # liblouis による韓国語点字変換
            translated = translate_korean_louis(content)
            translated_chunks.append(translated)
        else:
            # libkuraji による日本語点字変換
            cells, _, _, _ = libkuraji.translate_kanji(content, unicodeIO=True)
            translated_chunks.append(cells)
            
    result = ''.join(translated_chunks)
    
    # 点字空白文字 (U+2800) への統一
    if not keep_ascii_spaces:
        # 半角スペースと全角スペースを U+2800 (⠀) に置き換える
        result = result.replace(" ", "⠀").replace("　", "⠀")
        
    return result


def main():
    parser = argparse.ArgumentParser(
        description="日本語と韓国語が混在するテキストをユニコード点字に変換します。"
    )
    parser.add_argument(
        "text",
        nargs="?",
        help="変換するテキスト（省略した場合はファイル指定または標準入力から読み込みます）"
    )
    parser.add_argument(
        "-f", "--file",
        help="変換するテキストファイルのパス"
    )
    parser.add_argument(
        "-o", "--output",
        help="出力ファイルパス（省略した場合は標準出力に書き出します）"
    )
    parser.add_argument(
        "--keep-ascii-spaces",
        action="store_true",
        help="半角スペースを点字空白文字 (U+2800) に変換せず、そのまま残します"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="チャンク分割などの詳細情報を標準エラー出力に表示します"
    )

    args = parser.parse_args()

    # テキスト入力の決定
    input_text = ""
    if args.text:
        input_text = args.text
    elif args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                input_text = f.read()
        except Exception as e:
            print(f"Error: Failed to read file {args.file}. Reason: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # 標準入力からの読み込み
        if not sys.stdin.isatty():
            input_text = sys.stdin.read()
        else:
            parser.print_help()
            sys.exit(0)

    # 変換実行
    try:
        braille_output = translate_mixed_text(
            input_text,
            keep_ascii_spaces=args.keep_ascii_spaces,
            verbose=args.verbose
        )
    except Exception as e:
        print(f"Error during translation: {e}", file=sys.stderr)
        sys.exit(1)

    # 出力
    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(braille_output)
                if not braille_output.endswith('\n'):
                    f.write('\n')
        except Exception as e:
            print(f"Error: Failed to write output to {args.output}. Reason: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        sys.stdout.write(braille_output)
        if not braille_output.endswith('\n'):
            sys.stdout.write('\n')
        sys.stdout.flush()

if __name__ == "__main__":
    main()
