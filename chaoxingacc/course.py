"""
超星学习通课程模块
处理课程列表获取和课程信息
"""

import json
from typing import List, Dict, Optional
from curl_cffi import requests as cffi_requests


class ChaoxingCourse:
    """超星学习通课程管理类"""
    
    # API端点
    COURSE_LIST_URL = "http://mooc-api.chaoxing.com/mycourse/backclazzdata"
    CHAPTER_URL = "https://mobilelearn.chaoxing.com/ppt/api204688"
    
    # 默认请求头
    DEFAULT_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
        'Referer': 'https://i.chaoxing.com/',
    }
    
    def __init__(self, cookies: Dict[str, str], uid: Optional[str] = None):
        """
        初始化课程模块
        
        Args:
            cookies: 登录Cookie
            uid: 用户ID
        """
        self.session = cffi_requests.Session()
        self.cookies = cookies
        self.uid = uid
        self.session.cookies.update(cookies)
    
    def get_course_list(self) -> List[Dict]:
        """
        获取课程列表
        
        Returns:
            课程列表，每个课程包含courseId, classId, name等信息
        """
        try:
            response = self.session.get(
                self.COURSE_LIST_URL,
                headers=self.DEFAULT_HEADERS,
                cookies=self.cookies
            )
            
            if response.status_code != 200:
                print(f"获取课程列表失败，状态码: {response.status_code}")
                return []
            
            data = response.json()
            
            if data.get('result') != 1:
                print(f"获取课程列表失败: {data.get('msg', '未知错误')}")
                return []
            
            channel_list = data.get('channelList', [])
            courses = []
            
            for channel in channel_list:
                # 提取课程信息
                content = channel.get('content', {})
                course = content.get('course', {})
                
                if course:
                    course_info = {
                        'courseId': course.get('id'),
                        'classId': content.get('id'),
                        'name': course.get('data', {}).get('name', '未知课程'),
                        'teacher': course.get('data', {}).get('teacherfactor', '未知教师'),
                        'school': course.get('data', {}).get('schoolfactor', '未知学校'),
                        'image': course.get('data', {}).get('imageurl', ''),
                    }
                    courses.append(course_info)
            
            print(f"成功获取 {len(courses)} 门课程")
            return courses
            
        except Exception as e:
            print(f"获取课程列表异常: {e}")
            return []
    
    def print_course_list(self, courses: List[Dict]):
        """
        打印课程列表
        
        Args:
            courses: 课程列表
        """
        if not courses:
            print("没有课程")
            return
        
        print("\n" + "="*60)
        print("课程列表")
        print("="*60)
        
        for i, course in enumerate(courses, 1):
            print(f"\n{i}. {course['name']}")
            print(f"   课程ID: {course['courseId']}")
            print(f"   班级ID: {course['classId']}")
            print(f"   教师: {course['teacher']}")
            print(f"   学校: {course['school']}")
        
        print("\n" + "="*60)
    
    def get_chapter_list(self, course_id: int, class_id: int) -> List[Dict]:
        """
        获取章节列表
        
        Args:
            course_id: 课程ID
            class_id: 班级ID
            
        Returns:
            章节列表
        """
        try:
            url = f"{self.CHAPTER_URL}?courseId={course_id}&classId={class_id}&uid={self.uid}"
            
            response = self.session.get(
                url,
                headers=self.DEFAULT_HEADERS,
                cookies=self.cookies
            )
            
            if response.status_code != 200:
                print(f"获取章节列表失败，状态码: {response.status_code}")
                return []
            
            data = response.json()
            
            if not data.get('result'):
                print(f"获取章节列表失败")
                return []
            
            chapters = data.get('data', [])
            print(f"成功获取 {len(chapters)} 个章节")
            return chapters
            
        except Exception as e:
            print(f"获取章节列表异常: {e}")
            return []
    
    def select_course(self, courses: List[Dict]) -> Optional[Dict]:
        """
        让用户选择课程
        
        Args:
            courses: 课程列表
            
        Returns:
            选择的课程信息
        """
        if not courses:
            print("没有可选课程")
            return None
        
        self.print_course_list(courses)
        
        while True:
            try:
                choice = input(f"\n请选择课程 (1-{len(courses)}): ").strip()
                index = int(choice) - 1
                
                if 0 <= index < len(courses):
                    selected = courses[index]
                    print(f"\n已选择: {selected['name']}")
                    return selected
                else:
                    print(f"请输入 1-{len(courses)} 之间的数字")
            except ValueError:
                print("请输入有效的数字")
            except KeyboardInterrupt:
                print("\n取消选择")
                return None


if __name__ == "__main__":
    # 测试课程模块
    from login import ChaoxingLogin
    
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
        selected = course_manager.select_course(courses)
        if selected:
            print(f"\n选中课程: {selected['name']}")
            print(f"课程ID: {selected['courseId']}")
            print(f"班级ID: {selected['classId']}")
