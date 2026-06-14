"""
超星学习通签到模块
处理活动列表获取和签到操作
"""

import re
import time
from typing import List, Dict, Optional
from curl_cffi import requests as cffi_requests


class ChaoxingSign:
    """超星学习通签到管理类"""
    
    # API端点
    ACTIVITY_LIST_URL = "https://mobilelearn.chaoxing.com/ppt/activeAPI/taskactivelist"
    SIGN_URL = "https://mobilelearn.chaoxing.com/pptSign/stuSignajax"
    
    # 默认请求头
    DEFAULT_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
        'Referer': 'https://mobilelearn.chaoxing.com/',
    }
    
    def __init__(self, cookies: Dict[str, str], uid: Optional[str] = None):
        """
        初始化签到模块
        
        Args:
            cookies: 登录Cookie
            uid: 用户ID
        """
        self.session = cffi_requests.Session()
        self.cookies = cookies
        self.uid = uid
        self.session.cookies.update(cookies)
    
    def get_activity_list(self, course_id: int, class_id: int) -> List[Dict]:
        """
        获取活动列表
        
        Args:
            course_id: 课程ID
            class_id: 班级ID
            
        Returns:
            活动列表
        """
        try:
            url = (
                f"{self.ACTIVITY_LIST_URL}"
                f"?courseId={course_id}&classId={class_id}&uid={self.uid}"
            )
            
            response = self.session.get(
                url,
                headers=self.DEFAULT_HEADERS,
                cookies=self.cookies
            )
            
            if response.status_code != 200:
                print(f"获取活动列表失败，状态码: {response.status_code}")
                return []
            
            data = response.json()
            active_list = data.get('activeList', [])
            
            if not active_list:
                print("当前没有活动")
                return []
            
            print(f"成功获取 {len(active_list)} 个活动")
            return active_list
            
        except Exception as e:
            print(f"获取活动列表异常: {e}")
            return []
    
    def parse_active_id(self, url: str) -> Optional[str]:
        """
        从活动URL中解析activeId
        
        Args:
            url: 活动URL
            
        Returns:
            activeId
        """
        try:
            match = re.search(r'activeId=(\d+)', url)
            if match:
                return match.group(1)
            return None
        except:
            return None
    
    def sign(self, active_id: str) -> bool:
        """
        执行签到
        
        Args:
            active_id: 活动ID
            
        Returns:
            签到是否成功
        """
        try:
            url = (
                f"{self.SIGN_URL}"
                f"?activeId={active_id}"
                f"&uid={self.uid}"
                f"&clientip=&latitude=-1&longitude=-1"
                f"&appType=15&fid=0"
            )
            
            response = self.session.get(
                url,
                headers=self.DEFAULT_HEADERS,
                cookies=self.cookies
            )
            
            if response.status_code != 200:
                print(f"签到请求失败，状态码: {response.status_code}")
                return False
            
            result = response.text.strip()
            if result == "success":
                print(f"签到成功! activeId={active_id}")
                return True
            else:
                print(f"签到失败: {result}")
                return False
                
        except Exception as e:
            print(f"签到异常: {e}")
            return False
    
    def check_and_sign(self, course_id: int, class_id: int, course_name: str = "") -> List[str]:
        """
        检查并自动签到所有未签到的活动
        
        Args:
            course_id: 课程ID
            class_id: 班级ID
            course_name: 课程名称（用于日志）
            
        Returns:
            成功签到的activeId列表
        """
        signed_ids = []
        
        print(f"\n{'='*50}")
        print(f"检查课程: {course_name or course_id}")
        print(f"{'='*50}")
        
        activities = self.get_activity_list(course_id, class_id)
        
        for activity in activities:
            # 检查是否为签到活动且未签到
            active_type = activity.get('activeType')
            status = activity.get('status')
            
            # activeType==2 签到活动, status==1 未签到
            if active_type == 2 and status == 1:
                name = activity.get('nameOne', '未知活动')
                url = activity.get('url', '')
                active_id = self.parse_active_id(url)
                
                if not active_id:
                    print(f"无法解析活动ID: {url}")
                    continue
                
                print(f"\n发现待签到活动:")
                print(f"  名称: {name}")
                print(f"  activeId: {active_id}")
                
                if self.sign(active_id):
                    signed_ids.append(active_id)
            else:
                name = activity.get('nameOne', '未知活动')
                name_two = activity.get('nameTwo', '')
                print(f"  跳过活动: {name} ({name_two})")
        
        return signed_ids
    
    def print_activity_list(self, activities: List[Dict]):
        """
        打印活动列表
        
        Args:
            activities: 活动列表
        """
        if not activities:
            print("没有活动")
            return
        
        print("\n" + "="*60)
        print("活动列表")
        print("="*60)
        
        for i, activity in enumerate(activities, 1):
            active_type = activity.get('activeType')
            status = activity.get('status')
            name = activity.get('nameOne', '未知')
            name_two = activity.get('nameTwo', '')
            name_four = activity.get('nameFour', '')
            
            type_map = {1: '投票', 2: '签到', 4: '问卷', 0: '其他'}
            status_map = {0: '已结束', 1: '进行中', 2: '已结束'}
            
            type_str = type_map.get(active_type, f'类型{active_type}')
            status_str = status_map.get(status, f'状态{status}')
            
            print(f"\n{i}. {name}")
            print(f"   类型: {type_str}")
            print(f"   状态: {status_str}")
            if name_two:
                print(f"   描述: {name_two}")
            if name_four:
                print(f"   时间: {name_four}")
        
        print("\n" + "="*60)


class ChaoxingSignMonitor:
    """签到监控器 - 定时检查并自动签到"""
    
    def __init__(self, sign_module: ChaoxingSign, courses: List[Dict], interval: int = 10):
        """
        初始化监控器
        
        Args:
            sign_module: 签到模块实例
            courses: 要监控的课程列表
            interval: 检查间隔（秒）
        """
        self.sign_module = sign_module
        self.courses = courses
        self.interval = interval
        self.signed_activities: set = set()
        self.running = False
    
    def start(self):
        """启动监控"""
        self.running = True
        print(f"\n开始监控 {len(self.courses)} 门课程，检查间隔: {self.interval}秒")
        print("按 Ctrl+C 停止监控\n")
        
        try:
            while self.running:
                for course in self.courses:
                    course_id = course.get('courseId')
                    class_id = course.get('classId')
                    course_name = course.get('name', '')
                    
                    signed = self.sign_module.check_and_sign(
                        course_id, class_id, course_name
                    )
                    self.signed_activities.update(signed)
                
                print(f"\n下次检查时间: {self.interval}秒后...")
                time.sleep(self.interval)
                
        except KeyboardInterrupt:
            print(f"\n\n监控已停止，共签到 {len(self.signed_activities)} 个活动")
            self.running = False
    
    def stop(self):
        """停止监控"""
        self.running = False


if __name__ == "__main__":
    from login import ChaoxingLogin
    from course import ChaoxingCourse
    
    login = ChaoxingLogin()
    
    if not login.load_cookies_from_file():
        username = input("请输入用户名: ")
        password = input("请输入密码: ")
        if not login.login(username, password):
            print("登录失败")
            exit(1)
        login.save_cookies_to_file()
    
    course_manager = ChaoxingCourse(login.get_cookies(), login.get_uid())
    courses = course_manager.get_course_list()
    
    if courses:
        sign = ChaoxingSign(login.get_cookies(), login.get_uid())
        
        selected = course_manager.select_course(courses)
        if selected:
            activities = sign.get_activity_list(selected['courseId'], selected['classId'])
            sign.print_activity_list(activities)
            
            choice = input("\n是否自动签到? (y/n): ").strip().lower()
            if choice == 'y':
                sign.check_and_sign(
                    selected['courseId'], selected['classId'], selected['name']
                )
