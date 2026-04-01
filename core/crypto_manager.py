"""
加密管理器 - 内置密钥加密方案
"""
import os
import base64
from config import MASTER_KEY


class CryptoManager:
    """
    加密管理器
    
    使用内置固定密钥进行XOR加密，主要用于防止无意查看，
    不防专业破解。
    """
    
    def __init__(self):
        # 使用SHA256派生实际密钥
        import hashlib
        self._key = hashlib.sha256(MASTER_KEY).digest()
    
    def encrypt(self, plaintext: str) -> str:
        """
        加密字符串
        
        Args:
            plaintext: 明文内容
            
        Returns:
            Base64编码的密文
        """
        data = plaintext.encode('utf-8')
        
        # XOR加密
        encrypted = bytearray()
        for i, byte in enumerate(data):
            key_byte = self._key[i % len(self._key)]
            encrypted.append(byte ^ key_byte)
        
        # Base64编码
        return base64.b64encode(bytes(encrypted)).decode('ascii')
    
    def decrypt(self, ciphertext: str) -> str:
        """
        解密字符串
        
        Args:
            ciphertext: Base64编码的密文
            
        Returns:
            明文内容
        """
        # Base64解码
        encrypted = base64.b64decode(ciphertext.encode('ascii'))
        
        # XOR解密（XOR是对称的）
        decrypted = bytearray()
        for i, byte in enumerate(encrypted):
            key_byte = self._key[i % len(self._key)]
            decrypted.append(byte ^ key_byte)
        
        return bytes(decrypted).decode('utf-8')
    
    def encrypt_file(self, src_path: str, dst_path: str):
        """
        加密文件
        
        Args:
            src_path: 源文件路径
            dst_path: 目标加密文件路径
        """
        with open(src_path, 'r', encoding='utf-8') as f:
            plaintext = f.read()
        
        ciphertext = self.encrypt(plaintext)
        
        with open(dst_path, 'w', encoding='utf-8') as f:
            f.write(ciphertext)
    
    def decrypt_file(self, src_path: str) -> str:
        """
        解密文件
        
        Args:
            src_path: 加密文件路径
            
        Returns:
            明文内容
        """
        with open(src_path, 'r', encoding='utf-8') as f:
            ciphertext = f.read()
        
        return self.decrypt(ciphertext)


# 单例实例
crypto_manager = CryptoManager()
