import pytest
from english_conversation_practice_app.utils.csv_loader import load_conversation_csv

# 正常系テスト
def test_load_conversation_csv_success():
    csv_path = "data/business_english_mvp_3cols.csv"
    data = load_conversation_csv(csv_path)
    assert isinstance(data, list)
    assert len(data) > 0
    assert set(data[0].keys()) == {"id", "japanese_source", "english_reference"}

# ファイルが存在しない場合
def test_load_conversation_csv_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_conversation_csv("data/not_exist.csv")

# カラムが足りない場合
def test_load_conversation_csv_wrong_columns(tmp_path):
    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text("id,japanese_source\n1,テスト\n")
    with pytest.raises(ValueError):
        load_conversation_csv(str(bad_csv))

# 文字コードエラー（Shift-JISで保存した場合など）
def test_load_conversation_csv_encoding_error(tmp_path):
    bad_csv = tmp_path / "bad_encoding.csv"
    bad_csv.write_bytes("id,japanese_source,english_reference\n1,テスト,test\n".encode("shift_jis"))
    with pytest.raises(ValueError):
        load_conversation_csv(str(bad_csv)) 