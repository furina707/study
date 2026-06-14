"""
超星学习通 API 主入口
提供命令行界面和完整功能集成
"""

import sys
import argparse
from login import ChaoxingLogin
from course import ChaoxingCourse
from sign import ChaoxingSign, ChaoxingSignMonitor


def print_banner():
    """打印欢迎横幅"""
    banner = """
╔════════════════════════════════════════════════════════════╗
║           超星学习通 API 工具                              ║
║                                                            ║
║  功能:                                                     ║
║    1. 账号密码登录                                         ║
║    2. 获取课程列表                                         ║
║    3. 查看签到活动                                         ║
║    4. 自动签到                                             ║
║    5. 签到监控模式                                         ║
╚════════════════════════════════════════════════════════════╝
    """
    print(banner)


def login_flow() -> ChaoxingLogin:
    """登录流程"""
    print("\n[登录模块]")
    
    login = ChaoxingLogin()
    
    # 尝试加载已保存的Cookie
    if login.load_cookies_from_file():
        print("检测到已保存的Cookie")
        if login.check_login_status():
            print("Cookie有效，继续使用")
            return login
        else:
            print("Cookie已过期，需要重新登录")
    
    # 输入账号密码
    username = input("请输入用户名 (手机号/邮箱): ").strip()
    password = input("请输入密码: ").strip()
    
    if not username or not password:
        print("用户名或密码不能为空")
        sys.exit(1)
    
    # 执行登录
    if login.login(username, password):
        print("登录成功!")
        login.save_cookies_to_file()
        return login
    else:
        print("登录失败!")
        sys.exit(1)


def course_flow(login: ChaoxingLogin):
    """课程流程"""
    print("\n[课程模块]")
    
    course_manager = ChaoxingCourse(login.get_cookies(), login.get_uid())
    courses = course_manager.get_course_list()
    
    if not courses:
        print("未找到课程")
        return []
    
    course_manager.print_course_list(courses)
    return courses


def sign_flow(login: ChaoxingLogin, courses: list):
    """签到流程"""
    print("\n[签到模块]")
    
    if not courses:
        print("没有可选课程")
        return
    
    # 选择课程
    course_manager = ChaoxingCourse(login.get_cookies(), login.get_uid())
    selected = course_manager.select_course(courses)
    
    if not selected:
        return
    
    sign = ChaoxingSign(login.get_cookies(), login.get_uid())
    
    # 获取活动列表
    activities = sign.get_activity_list(selected['courseId'], selected['classId'])
    sign.print_activity_list(activities)
    
    if not activities:
        return
    
    # 询问是否自动签到
    choice = input("\n是否自动签到? (y/n): ").strip().lower()
    if choice == 'y':
        signed = sign.check_and_sign(
            selected['courseId'], selected['classId'], selected['name']
        )
        print(f"\n签到完成，成功签到 {len(signed)} 个活动")


def monitor_flow(login: ChaoxingLogin, courses: list):
    """监控流程"""
    print("\n[监控模式]")
    
    if not courses:
        print("没有可选课程")
        return
    
    # 选择要监控的课程
    course_manager = ChaoxingCourse(login.get_cookies(), login.get_uid())
    
    print("\n请选择要监控的课程 (输入序号，用逗号分隔，输入 all 监控全部):")
    course_manager.print_course_list(courses)
    
    choice = input("\n选择: ").strip()
    
    if choice.lower() == 'all':
        selected_courses = courses
    else:
        try:
            indices = [int(x.strip()) - 1 for x in choice.split(',')]
            selected_courses = [courses[i] for i in indices if 0 <= i < len(courses)]
        except (ValueError, IndexError):
            print("输入无效")
            return
    
    if not selected_courses:
        print("未选择课程")
        return
    
    print(f"\n已选择 {len(selected_courses)} 门课程进行监控")
    
    # 输入检查间隔
    try:
        interval = int(input("检查间隔 (秒，默认10): ").strip() or "10")
    except ValueError:
        interval = 10
    
    # 启动监控
    sign = ChaoxingSign(login.get_cookies(), login.get_uid())
    monitor = ChaoxingSignMonitor(sign, selected_courses, interval)
    monitor.start()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='超星学习通 API 工具')
    parser.add_argument('-u', '--username', help='用户名')
    parser.add_argument('-p', '--password', help='密码')
    parser.add_argument('-m', '--mode', choices=['login', 'course', 'sign', 'monitor'],
                        default='login', help='运行模式')
    parser.add_argument('-i', '--interval', type=int, default=10,
                        help='监控模式检查间隔(秒)')
    
    args = parser.parse_args()
    
    print_banner()
    
    # 登录
    login = login_flow()
    
    if args.mode == 'login':
        print(f"\n登录成功! UID: {login.get_uid()}")
        return
    
    # 获取课程
    courses = course_flow(login)
    
    if args.mode == 'course':
        return
    
    if args.mode == 'sign':
        sign_flow(login, courses)
    elif args.mode == 'monitor':
        if not courses:
            print("没有课程")
            return
        
        sign = ChaoxingSign(login.get_cookies(), login.get_uid())
        monitor = ChaoxingSignMonitor(sign, courses, args.interval)
        monitor.start()


def interactive_mode():
    """交互模式"""
    print_banner()
    
    while True:
        print("\n请选择功能:")
        print("1. 登录")
        print("2. 查看课程")
        print("3. 签到")
        print("4. 启动监控")
        print("5. 退出")
        
        choice = input("\n请输入选项 (1-5): ").strip()
        
        if choice == '1':
            login = login_flow()
            courses = course_flow(login)
            
            while True:
                print("\n登录后操作:")
                print("1. 刷新课程列表")
                print("2. 查看签到活动")
                print("3. 自动签到")
                print("4. 启动监控")
                print("5. 返回主菜单")
                
                sub_choice = input("\n请选择 (1-5): ").strip()
                
                if sub_choice == '1':
                    courses = course_flow(login)
                elif sub_choice == '2':
                    if courses:
                        course_manager = ChaoxingCourse(login.get_cookies(), login.get_uid())
                        selected = course_manager.select_course(courses)
                        if selected:
                            sign = ChaoxingSign(login.get_cookies(), login.get_uid())
                            activities = sign.get_activity_list(selected['courseId'], selected['classId'])
                            sign.print_activity_list(activities)
                    else:
                        print("没有课程")
                elif sub_choice == '3':
                    sign_flow(login, courses)
                elif sub_choice == '4':
                    if courses:
                        sign = ChaoxingSign(login.get_cookies(), login.get_uid())
                        monitor = ChaoxingSignMonitor(sign, courses, 10)
                        monitor.start()
                    else:
                        print("没有课程")
                elif sub_choice == '5':
                    break
                else:
                    print("无效选项")
        
        elif choice == '5':
            print("再见!")
            break
        else:
            print("无效选项，请重新选择")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main()
    else:
        interactive_mode()
