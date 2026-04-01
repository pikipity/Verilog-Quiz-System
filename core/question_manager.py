"""
题目管理器 - 负责题目下载、更新和抽题
"""
import os
import json
import hashlib
import random
import requests
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from config import SERVER_URL, QUESTIONS_DIR, SUBMISSIONS_DIR
from core.crypto_manager import crypto_manager


class QuestionManager:
    """
    题目管理器
    
    职责：
    1. 从服务器检查并下载题目
    2. 管理抽题逻辑（基于机器指纹的确定性随机）
    3. 加密保存参考答案
    """
    
    def __init__(self):
        self.server_url = SERVER_URL
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'VerilogQuiz/0.1.0'
        })
    
    def check_update(self) -> Tuple[bool, List[int]]:
        """
        检查服务器是否有新题目
        
        Returns:
            (是否有更新, 有更新的周次列表)
        """
        try:
            # 下载manifest
            manifest_url = f"{self.server_url}/manifest.json"
            response = self.session.get(manifest_url, timeout=10)
            response.raise_for_status()
            manifest = response.json()
            
            available_weeks = manifest.get('weeks', [])
            updated_weeks = []
            
            for week_str in available_weeks:
                week_num = int(week_str.replace('week', ''))
                
                # 检查本地是否已有
                local_info = os.path.join(QUESTIONS_DIR, week_str, "info.json")
                
                if not os.path.exists(local_info):
                    # 本地没有，需要下载
                    updated_weeks.append(week_num)
                else:
                    # 可以添加版本检查逻辑
                    pass
            
            return len(updated_weeks) > 0, updated_weeks
            
        except Exception as e:
            print(f"检查更新失败: {e}")
            return False, []
    
    def download_week(self, week: int) -> bool:
        """
        下载指定周的题目
        
        Args:
            week: 周次
            
        Returns:
            是否成功
        """
        week_str = f"week{week}"
        week_url = f"{self.server_url}/{week_str}"
        
        try:
            # 1. 下载info.json
            info_url = f"{week_url}/info.json"
            response = self.session.get(info_url, timeout=10)
            response.raise_for_status()
            info = response.json()
            
            # 保存本地
            week_dir = os.path.join(QUESTIONS_DIR, week_str)
            os.makedirs(week_dir, exist_ok=True)
            
            with open(os.path.join(week_dir, "info.json"), 'w', encoding='utf-8') as f:
                json.dump(info, f, ensure_ascii=False, indent=2)
            
            # 2. 抽题
            total = info.get('total_questions', 0)
            select_count = info.get('select_count', 0)
            pool = info.get('question_pool', [])
            
            drawn_questions = self._draw_questions(week, pool, select_count)
            
            # 保存抽题结果
            draw_result = {
                "week": week,
                "drawn_questions": drawn_questions,
                "draw_time": self._get_timestamp()
            }
            
            with open(os.path.join(week_dir, "draw_result.json"), 'w', encoding='utf-8') as f:
                json.dump(draw_result, f, ensure_ascii=False, indent=2)
            
            # 3. 下载抽中的题目
            for q_id in drawn_questions:
                success = self._download_question(week_str, q_id, week_dir)
                if not success:
                    print(f"下载题目 {q_id} 失败")
                    return False
            
            return True
            
        except Exception as e:
            print(f"下载Week {week}失败: {e}")
            return False
    
    def _download_question(self, week_str: str, q_id: str, week_dir: str) -> bool:
        """
        下载单个题目
        
        Args:
            week_str: 周次字符串（如week1）
            q_id: 题目ID（如q1）
            week_dir: 本地周次目录
            
        Returns:
            是否成功
        """
        base_url = f"{self.server_url}/{week_str}/{q_id}"
        q_dir = os.path.join(week_dir, q_id)
        os.makedirs(q_dir, exist_ok=True)
        
        files_to_download = [
            ("question.md", "question.md"),
            ("testbench.v", "testbench.v"),
            ("reference.v", "reference.v"),
        ]
        
        try:
            for remote_name, local_name in files_to_download:
                url = f"{base_url}/{remote_name}"
                response = self.session.get(url, timeout=10)
                
                if response.status_code != 200:
                    if remote_name == "reference.v":
                        # reference.v是必须的
                        print(f"下载 {remote_name} 失败: {response.status_code}")
                        return False
                    else:
                        # 其他文件可选
                        continue
                
                local_path = os.path.join(q_dir, local_name)
                
                if remote_name == "reference.v":
                    # 加密保存参考答案
                    # 先写入临时文件，然后加密
                    temp_path = local_path + ".tmp"
                    with open(temp_path, 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    
                    # 加密
                    encrypted_path = local_path + ".enc"
                    crypto_manager.encrypt_file(temp_path, encrypted_path)
                    
                    # 删除临时明文文件
                    os.remove(temp_path)
                    
                    print(f"已加密保存: {encrypted_path}")
                else:
                    # 明文保存其他文件
                    with open(local_path, 'w', encoding='utf-8') as f:
                        f.write(response.text)
            
            # 下载资源文件（如图片）
            self._download_assets(base_url, q_dir)
            
            return True
            
        except Exception as e:
            print(f"下载题目 {q_id} 失败: {e}")
            return False
    
    def _download_assets(self, base_url: str, q_dir: str):
        """下载题目资源（图片等）"""
        # 暂时简化，假设资源在assets目录
        # 可以根据question.md中的图片链接动态下载
        pass
    
    def _draw_questions(self, week: int, pool: List[str], count: int) -> List[str]:
        """
        抽题算法
        
        基于机器指纹生成确定性随机序列
        
        Args:
            week: 周次
            pool: 题目池
            count: 抽取数量
            
        Returns:
            抽中的题目ID列表
        """
        # 生成机器指纹
        fingerprint = self._get_machine_fingerprint()
        
        # 结合周次生成种子
        seed_str = f"{fingerprint}_week{week}"
        seed = int(hashlib.sha256(seed_str.encode()).hexdigest(), 16)
        
        # 使用固定种子
        rng = random.Random(seed)
        
        # 抽题
        if count >= len(pool):
            drawn = pool.copy()
        else:
            drawn = rng.sample(pool, count)
        
        # 打乱顺序（使用相同种子继续）
        rng.shuffle(drawn)
        
        print(f"Week {week} 抽题结果: {drawn}")
        return drawn
    
    def _get_machine_fingerprint(self) -> str:
        """
        获取机器指纹
        
        使用硬件信息生成唯一标识
        """
        import platform
        
        try:
            # 尝试获取MAC地址
            import uuid
            mac = uuid.getnode()
            mac_str = ':'.join(('%012X' % mac)[i:i+2] for i in range(0, 12, 2))
        except:
            mac_str = ""
        
        # 组合机器信息
        info = [
            platform.node(),  # 计算机名
            platform.machine(),  # 机器类型
            platform.processor(),  # 处理器
            mac_str,
        ]
        
        fingerprint = '_'.join(filter(None, info))
        return hashlib.sha256(fingerprint.encode()).hexdigest()[:32]
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_reference_code(self, week: int, question_id: str) -> Optional[str]:
        """
        获取参考答案（临时解密）
        
        Args:
            week: 周次
            question_id: 题目ID
            
        Returns:
            参考答案代码，失败返回None
        """
        enc_path = os.path.join(
            QUESTIONS_DIR, 
            f"week{week}", 
            question_id,
            "reference.v.enc"
        )
        
        if not os.path.exists(enc_path):
            return None
        
        try:
            return crypto_manager.decrypt_file(enc_path)
        except Exception as e:
            print(f"解密参考答案失败: {e}")
            return None


# 单例实例
question_manager = QuestionManager()
