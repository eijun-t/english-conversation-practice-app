import csv
import os

def load_conversation_csv(filepath):
    """
    指定したCSVファイルを読み込み、リスト形式で返すユーティリティ関数
    エラー時はわかりやすいメッセージを表示
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"ファイルが見つかりません: {filepath}")

    data = []
    try:
        with open(filepath, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            # 必要なカラムがあるかチェック
            required_fields = {'id', 'japanese_source', 'english_reference'}
            if not required_fields.issubset(reader.fieldnames):
                raise ValueError(f"CSVのカラムが正しくありません。必要なカラム: {required_fields}")
            for row in reader:
                data.append(row)
    except UnicodeDecodeError:
        raise ValueError("ファイルの文字コードがUTF-8ではありません。UTF-8で保存してください。")

    return data 