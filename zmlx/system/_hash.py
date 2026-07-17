import hashlib
from typing import Optional


def get_hash(text: str, length: Optional[int] = None) -> str:
    """
    计算文本的哈希值. 返回前length个字符.
    默认返回前30个字符.
    Args:
        text (str): 输入文本
        length (int, optional): 哈希值长度，默认为None
    Returns:
        str: 计算得到的哈希值
    """
    hash_obj = hashlib.sha256(text.encode('utf-8'))
    if length is None:
        length = 30
    return hash_obj.hexdigest()[:length]
