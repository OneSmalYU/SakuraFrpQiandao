import smtplib
import os
import requests  # 新增：用于发送 HTTP 请求
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime


def send_log_email(log_file='checkin.log'):
    """
    发送签到日志邮件（原有功能）
    """
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    sender_email = os.getenv('EMAIL_USERNAME', '')
    sender_password = os.getenv('EMAIL_PASSWORD', '')
    receiver_email = os.getenv('RECEIVER_EMAIL', sender_email)

    if not sender_email or not sender_password:
        print("❌ 邮件配置未设置，跳过邮件发送")
        return False

    try:
        log_content = ""
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                log_content = f.read()
        else:
            log_content = "日志文件不存在"

        is_success = "签到流程完成" in log_content or "验证码验证成功" in log_content
        status_emoji = "✅" if is_success else "❌"
        status_text = "成功" if is_success else "失败"

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = f"{status_emoji} SakuraFrp 签到{status_text} - {datetime.now().strftime('%Y-%m-%d')}"

        body = f"""
SakuraFrp 自动签到报告

状态: {status_emoji} {status_text}
时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{'='*50}
日志内容:
{'='*50}

{log_content[-2000:] if len(log_content) > 2000 else log_content}

{'='*50}
此邮件由自动签到系统发送
        """

        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        if os.path.exists(log_file):
            with open(log_file, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename= {os.path.basename(log_file)}')
            msg.attach(part)

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)

        print(f"✅ 邮件发送成功: {receiver_email}")
        return True

    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")
        return False


def send_serverchan(log_file='checkin.log'):
    """
    通过 Server酱 推送消息到微信
    """
    sendkey = os.getenv('SERVERCHAN_SENDKEY', '')
    if not sendkey:
        print("❌ SERVERCHAN_SENDKEY 未设置，跳过 Server酱 推送")
        return False

    try:
        # 读取日志内容
        log_content = ""
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                log_content = f.read()
        else:
            log_content = "日志文件不存在"

        # 判断签到状态
        is_success = "签到流程完成" in log_content or "验证码验证成功" in log_content
        status_emoji = "✅" if is_success else "❌"
        status_text = "成功" if is_success else "失败"

        # 准备标题和内容
        title = f"{status_emoji} SakuraFrp 签到{status_text} {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # 内容太长时截断（Server酱 免费版限制 32KB 以内，这里取最后 1000 字节约）
        brief_log = log_content[-1000:] if len(log_content) > 1000 else log_content
        content = f"""
签到状态: {status_emoji} {status_text}
执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

【最近日志】
{brief_log}

完整日志请查看 GitHub Actions。
        """

        # 调用 Server酱 接口
        url = f"https://sctapi.ftqq.com/{sendkey}.send"
        data = {
            "title": title,
            "desp": content
        }
        response = requests.post(url, data=data)
        result = response.json()

        if result.get('code') == 0:
            print(f"✅ Server酱 推送成功")
            return True
        else:
            print(f"❌ Server酱 推送失败: {result.get('message')}")
            return False

    except Exception as e:
        print(f"❌ Server酱 推送异常: {e}")
        return False


if __name__ == "__main__":
    # 先发送邮件
    send_log_email()
    # 再尝试 Server酱 推送
    send_serverchan()
