#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可转债申购提醒脚本
每天检查是否有新的可转债可以申购
"""

import os
import requests
from datetime import datetime
import json


def get_convertible_bonds():
    """
    获取可转债申购信息
    数据源：集思录 API
    """
    try:
        url = "https://www.jisilu.cn/data/cbnew/cb_list_new/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.jisilu.cn/data/cbnew/'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('rows'):
            return data['rows']
        return []
    except Exception as e:
        print(f"获取数据失败: {e}")
        return []


def filter_today_bonds(bonds):
    """
    筛选今天可以申购的可转债
    """
    today = datetime.now().strftime('%Y-%m-%d')
    today_bonds = []
    
    for bond in bonds:
        cell = bond.get('cell', {})
        # 申购日期
        apply_date = cell.get('apply_date', '')
        
        if apply_date == today:
            today_bonds.append({
                'name': cell.get('bond_nm', '未知'),
                'code': cell.get('bond_id', ''),
                'stock_name': cell.get('stock_nm', ''),
                'stock_code': cell.get('stock_id', ''),
                'rating': cell.get('rating_cd', '无评级'),
                'apply_code': cell.get('apply_cd', ''),
            })
    
    return today_bonds


def send_serverchan_notification(title, content, key):
    """
    通过 Server酱 发送微信通知
    """
    url = f"https://sctapi.ftqq.com/{key}.send"
    
    data = {
        "title": title,
        "desp": content
    }
    
    try:
        response = requests.post(url, data=data, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        if result.get('code') == 0:
            print("✅ 通知发送成功！")
            return True
        else:
            print(f"❌ 通知发送失败: {result.get('message')}")
            return False
    except Exception as e:
        print(f"❌ 发送通知时出错: {e}")
        return False


def format_message(bonds):
    """
    格式化消息内容
    """
    if not bonds:
        return "今日无可转债申购", "今天没有新的可转债可以申购哦~\n\n明天见！👋"
    
    title = f"🔔 今日有 {len(bonds)} 只可转债可申购！"
    
    content_parts = [
        f"## 📅 {datetime.now().strftime('%Y年%m月%d日')} 可转债申购清单\n",
        "---\n"
    ]
    
    for i, bond in enumerate(bonds, 1):
        content_parts.append(f"### {i}. {bond['name']} ({bond['code']})\n")
        content_parts.append(f"- **申购代码**: `{bond['apply_code']}`\n")
        content_parts.append(f"- **正股**: {bond['stock_name']} ({bond['stock_code']})\n")
        content_parts.append(f"- **评级**: {bond['rating']}\n")
        content_parts.append("\n")
    
    content_parts.append("---\n")
    content_parts.append("💡 **申购提示**：\n")
    content_parts.append("1. 开盘时间即可申购（9:30-15:00）\n")
    content_parts.append("2. 无需市值，中签后再缴款\n")
    content_parts.append("3. 建议顶格申购（通常1万张）\n")
    content_parts.append("\n🔗 查看详情：https://www.jisilu.cn/data/cbnew/")
    
    return title, ''.join(content_parts)


def main():
    """
    主函数
    """
    print(f"开始检查可转债申购信息... {datetime.now()}")
    
    # 获取 Server酱 密钥
    serverchan_key = os.environ.get('SERVERCHAN_KEY')
    
    if not serverchan_key:
        print("❌ 错误：未设置 SERVERCHAN_KEY 环境变量")
        print("请在 GitHub 仓库的 Settings -> Secrets 中添加")
        return
    
    # 获取可转债数据
    print("正在获取可转债数据...")
    all_bonds = get_convertible_bonds()
    
    if not all_bonds:
        print("⚠️ 未获取到任何数据")
        return
    
    print(f"获取到 {len(all_bonds)} 条数据")
    
    # 筛选今天可申购的
    today_bonds = filter_today_bonds(all_bonds)
    
    print(f"今日可申购: {len(today_bonds)} 只")
    
    # 格式化并发送通知
    title, content = format_message(today_bonds)
    
    print(f"标题: {title}")
    print("正在发送微信通知...")
    
    send_serverchan_notification(title, content, serverchan_key)
    
    print("✅ 任务完成！")


if __name__ == "__main__":
    main()
