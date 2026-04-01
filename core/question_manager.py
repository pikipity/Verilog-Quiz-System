"""
题目管理器 - 负责题目下载、更新和抽题
"""
import os
import json
import shutil
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
    
    新格式：使用独立ID管理题目，与文件夹分离
    """
    
    def __init__(self):
        self.server_url = SERVER_URL
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'VerilogQuiz/0.1.0'
        })
    
    def check_update(self) -> Tuple[str, List[int], str]:
        """
        检查服务器是否有新题目（基于时间戳）
        
        Returns:
            (状态, 需要更新的周次列表, 错误信息)
            状态: "success"(有更新), "no_update"(无更新), "error"(错误)
        """
        try:
            # 1. 获取服务器 manifest
            manifest_url = f"{self.server_url}/manifest.json"
            response = self.session.get(manifest_url, timeout=10)
            response.raise_for_status()
            manifest = response.json()
            
            available_weeks = manifest.get('weeks', [])
            updated_weeks = []
            
            for week_str in available_weeks:
                week_num = int(week_str.replace('week', ''))
                
                # 2. 下载服务器 info.json 获取时间戳
                server_info_url = f"{self.server_url}/{week_str}/info.json"
                try:
                    server_response = self.session.get(server_info_url, timeout=10)
                    server_response.raise_for_status()
                    server_info = server_response.json()
                    server_timestamp = server_info.get('updated_at', '')
                except Exception as e:
                    print(f"获取服务器 {week_str} 信息失败: {e}")
                    continue
                
                # 3. 检查本地时间戳
                local_info_path = os.path.join(QUESTIONS_DIR, week_str, "info.json")
                needs_update = False
                
                if not os.path.exists(local_info_path):
                    # 本地没有，需要下载
                    needs_update = True
                    print(f"{week_str}: 本地不存在，需要下载")
                else:
                    # 本地有，比较时间戳
                    try:
                        with open(local_info_path, 'r', encoding='utf-8') as f:
                            local_info = json.load(f)
                        local_timestamp = local_info.get('updated_at', '')
                        
                        if server_timestamp > local_timestamp:
                            needs_update = True
                            print(f"{week_str}: 服务器有更新 ({server_timestamp} > {local_timestamp})")
                        else:
                            print(f"{week_str}: 已是最新 ({local_timestamp})")
                    except Exception as e:
                        print(f"读取本地 {week_str} 信息失败: {e}")
                        needs_update = True
                
                if needs_update:
                    updated_weeks.append(week_num)
            
            if updated_weeks:
                return "success", updated_weeks, ""
            else:
                return "no_update", [], ""
            
        except requests.exceptions.ConnectionError as e:
            print(f"连接服务器失败: {e}")
            return "error", [], f"无法连接到服务器\n请检查:\n1. 服务器是否已启动\n2. 网络连接是否正常\n3. 服务器地址配置是否正确\n\n当前配置: {self.server_url}"
        except requests.exceptions.Timeout as e:
            print(f"连接超时: {e}")
            return "error", [], "连接服务器超时，请检查网络"
        except Exception as e:
            print(f"检查更新失败: {e}")
            return "error", [], f"检查更新失败: {str(e)}"
    
    def download_week(self, week: int) -> bool:
        """
        下载指定周的题目（如有更新会删除旧数据重新下载）
        
        Args:
            week: 周次
            
        Returns:
            是否成功
        """
        week_str = f"week{week}"
        week_url = f"{self.server_url}/{week_str}"
        
        try:
            # 1. 下载服务器 info.json
            info_url = f"{week_url}/info.json"
            response = self.session.get(info_url, timeout=10)
            response.raise_for_status()
            info = response.json()
            
            # 2. 检查是否需要清理旧数据
            week_dir = os.path.join(QUESTIONS_DIR, week_str)
            week_submission_dir = os.path.join(SUBMISSIONS_DIR, week_str)
            
            if os.path.exists(week_dir):
                # 检查时间戳
                try:
                    with open(os.path.join(week_dir, "info.json"), 'r', encoding='utf-8') as f:
                        local_info = json.load(f)
                    local_timestamp = local_info.get('updated_at', '')
                    server_timestamp = info.get('updated_at', '')
                    
                    if server_timestamp > local_timestamp:
                        # 服务器有更新，删除本地旧数据
                        print(f"{week_str}: 检测到更新 ({server_timestamp} > {local_timestamp})")
                        print(f"{week_str}: 删除旧目录 {week_dir}")
                        shutil.rmtree(week_dir)
                        # 同时清理提交记录
                        if os.path.exists(week_submission_dir):
                            print(f"{week_str}: 删除提交记录 {week_submission_dir}")
                            shutil.rmtree(week_submission_dir)
                        print(f"{week_str}: 旧数据已清理，准备重新下载")
                except Exception as e:
                    print(f"检查时间戳失败: {e}，将重新下载")
                    shutil.rmtree(week_dir)
            
            # 3. 保存新的 info.json
            os.makedirs(week_dir, exist_ok=True)
            info_path = os.path.join(week_dir, "info.json")
            with open(info_path, 'w', encoding='utf-8') as f:
                json.dump(info, f, ensure_ascii=False, indent=2)
            print(f"{week_str}: info.json 已保存到 {info_path}")
            
            # 2. 抽题（基于ID列表）
            questions = info.get('questions', [])
            select_count = info.get('select_count', 0)
            
            # 提取ID列表用于抽题
            id_list = [q['id'] for q in questions]
            drawn_ids = self._draw_questions(week, id_list, select_count)
            
            # 构建抽题结果（包含完整信息）
            drawn_questions = []
            for idx, qid in enumerate(drawn_ids):
                q_info = next((q for q in questions if q['id'] == qid), None)
                if q_info:
                    drawn_questions.append({
                        "id": q_info['id'],
                        "folder": q_info['folder'],
                        "title": q_info['title'],
                        "original_index": questions.index(q_info) + 1
                    })
            
            # 保存抽题结果
            draw_result = {
                "week": week,
                "drawn_questions": drawn_questions,
                "draw_time": self._get_timestamp()
            }
            
            draw_result_path = os.path.join(week_dir, "draw_result.json")
            with open(draw_result_path, 'w', encoding='utf-8') as f:
                json.dump(draw_result, f, ensure_ascii=False, indent=2)
            print(f"{week_str}: draw_result.json 已保存，抽中 {len(drawn_questions)} 道题")
            
            # 3. 下载抽中的题目（按folder下载）
            for q in drawn_questions:
                success = self._download_question(week_str, q, week_dir)
                if not success:
                    print(f"下载题目 {q['id']} (folder: {q['folder']}) 失败")
                    return False
            
            return True
            
        except Exception as e:
            print(f"下载Week {week}失败: {e}")
            return False
    
    def _download_question(self, week_str: str, q_info: dict, week_dir: str) -> bool:
        """
        下载单个题目
        
        Args:
            week_str: 周次字符串（如week1）
            q_info: 题目信息（包含id, folder, title）
            week_dir: 本地周次目录
            
        Returns:
            是否成功
        """
        folder = q_info['folder']
        qid = q_info['id']
        
        base_url = f"{self.server_url}/{week_str}/{folder}"
        # 本地存储使用ID作为子目录名
        q_dir = os.path.join(week_dir, qid)
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
                        print(f"下载 {remote_name} 失败: {response.status_code}")
                        return False
                    else:
                        continue
                
                local_path = os.path.join(q_dir, local_name)
                
                if remote_name == "reference.v":
                    # 加密保存参考答案
                    temp_path = local_path + ".tmp"
                    with open(temp_path, 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    
                    encrypted_path = local_path + ".enc"
                    crypto_manager.encrypt_file(temp_path, encrypted_path)
                    os.remove(temp_path)
                    print(f"已加密保存: {qid}/reference.v.enc")
                else:
                    # 明文保存其他文件
                    with open(local_path, 'w', encoding='utf-8') as f:
                        f.write(response.text)
            
            return True
            
        except Exception as e:
            print(f"下载题目 {qid} 失败: {e}")
            return False
    
    def _draw_questions(self, week: int, id_list: List[str], count: int) -> List[str]:
        """
        抽题算法
        
        Args:
            week: 周次
            id_list: 题目ID列表
            count: 抽取数量
            
        Returns:
            抽中的题目ID列表
        """
        # 生成机器指纹
        fingerprint = self._get_machine_fingerprint()
        
        # 结合周次生成种子
        seed_str = f"{fingerprint}_week{week}"
        seed = int(hashlib.sha256(seed_str.encode()).hexdigest(), 16)
        
        rng = random.Random(seed)
        
        # 抽题
        if count >= len(id_list):
            drawn = id_list.copy()
        else:
            drawn = rng.sample(id_list, count)
        
        # 打乱顺序
        rng.shuffle(drawn)
        
        print(f"Week {week} 抽题结果: {drawn}")
        return drawn
    
    def _get_machine_fingerprint(self) -> str:
        """获取机器指纹"""
        import platform
        import uuid
        
        try:
            mac = uuid.getnode()
            mac_str = ':'.join(('%012X' % mac)[i:i+2] for i in range(0, 12, 2))
        except:
            mac_str = ""
        
        info = [
            platform.node(),
            platform.machine(),
            platform.processor(),
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
            question_id,  # 使用ID作为目录名
            "reference.v.enc"
        )
        
        if not os.path.exists(enc_path):
            return None
        
        try:
            return crypto_manager.decrypt_file(enc_path)
        except Exception as e:
            print(f"解密参考答案失败: {e}")
            return None
    
    def get_question_info(self, week: int, question_id: str) -> Optional[dict]:
        """
        获取题目信息
        
        Args:
            week: 周次
            question_id: 题目ID
            
        Returns:
            题目信息字典，失败返回None
        """
        info_file = os.path.join(QUESTIONS_DIR, f"week{week}", "info.json")
        
        if not os.path.exists(info_file):
            return None
        
        try:
            with open(info_file, 'r', encoding='utf-8') as f:
                info = json.load(f)
            
            questions = info.get('questions', [])
            for q in questions:
                if q['id'] == question_id:
                    return q
            
            return None
        except Exception as e:
            print(f"读取题目信息失败: {e}")
            return None


# 单例实例
question_manager = QuestionManager()
