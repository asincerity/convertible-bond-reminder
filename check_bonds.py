#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可转债申购提醒脚本
每天检查是否有新的可转债可以申购，并推送北京天气和日出时间
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
        print(f"获取可���债数据失败: {e}")
        return []


def get_beijing_weather():
    """
    获取北京天气信息
    使用免费的天气API：wttr.in
    """
    try:
        url = "https://wttr.in/Beijing?format=j1&lang=zh"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        current = data['current_condition'][0]
        today = data['weather'][0]
        
        weather_info = {
            'temp': current['temp_C'],
            'feels_like': current['FeelsLikeC'],
            'humidity': current['humidity'],
            'weather_desc': current['lang_zh'][0]['value'] if current.get('lang_zh') else current['weatherDesc'][0]['value'],
            'wind_speed': current['windspeedKmph'],
            'wind_dir': current['winddir16Point'],
            'max_temp': today['maxtempC'],
            'min_temp': today['mintempC'],
            'uv_index': today['uvIndex'],
            'sunrise': today['astronomy'][0]['sunrise'],
            'sunset': today['astronomy'][0]['sunset'],
        }
        
        return weather_info
    except Exception as e:
        print(f"获取天气信息失败: {e}")
        return None


def filter_today_bonds(bonds):
    """
    筛选今天可以申购的可转债
    """
    today = datetime.now().strftime('%Y-%m-%d')
    today_bonds = []
    print(today)
    for bond in bonds:
        cell = bond.get('cell', {})
        apply_date = cell.get('maturity_dt', '')
        print(apply_date)
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


def get_weather_emoji(weather_desc):
    """
    根据天气描述返回对应的 emoji
    """
    weather_desc = weather_desc.lower()
    if '晴' in weather_desc or 'sunny' in weather_desc or 'clear' in weather_desc:
        return '☀️'
    elif '云' in weather_desc or 'cloud' in weather_desc:
        return '☁️'
    elif '雨' in weather_desc or 'rain' in weather_desc:
        return '🌧️'
    elif '雪' in weather_desc or 'snow' in weather_desc:
        return '❄️'
    elif '雾' in weather_desc or 'fog' in weather_desc or 'mist' in weather_desc:
        return '🌫️'
    elif '雷' in weather_desc or 'thunder' in weather_desc:
        return '⛈️'
    else:
        return '🌤️'


def format_weather_section(weather):
    """
    格式化天气信息部分
    """
    if not weather:
        return "\n## 🌤️ 今日天气\n\n⚠️ 天气信息获取失败\n\n"
    
    emoji = get_weather_emoji(weather['weather_desc'])
    
    weather_section = [
        f"\n## {emoji} 北京天气\n\n",
        f"**{weather['weather_desc']}** | 🌡️ {weather['temp']}°C（体感 {weather['feels_like']}°C）\n\n",
        f"- 🌡️ **温度范围**: {weather['min_temp']}°C ~ {weather['max_temp']}°C\n",
        f"- 💧 **湿度**: {weather['humidity']}%\n",
        f"- 🌬️ **风力**: {weather['wind_dir']} {weather['wind_speed']} km/h\n",
        f"- ☀️ **紫外线指数**: {weather['uv_index']}\n",
        f"- 🌅 **日出时间**: {weather['sunrise']}\n",
        f"- 🌇 **日落时间**: {weather['sunset']}\n\n",
    ]
    
    # 添加温馨提示
    temp = int(weather['temp'])
    if temp < 0:
        weather_section.append("🧥 **提示**: 天气寒冷，注意保暖！\n")
    elif temp < 10:
        weather_section.append("🧥 **提示**: 气温较低，多穿点衣服。\n")
    elif temp > 30:
        weather_section.append("🌊 **提示**: 天气炎热，注意防暑降温！\n")
    elif temp > 25:
        weather_section.append("😎 **提示**: 天气温暖舒适。\n")
    
    return ''.join(weather_section)


def format_message(bonds, weather):
    """
    格式化消息内容（包含可转债和天气信息）
    """
    # 标题
    if not bonds:
        title = f"☀️ 早安！今日无可转债申购"
    else:
        title = f"🔔 今日有 {len(bonds)} 只可转债可申购！"
    
    # 开始构建内容
    content_parts = [
        f"# {datetime.now().strftime('%Y年%m月%d日')} ��报\n\n",
    ]
    
    # 添加天气信息
    content_parts.append(format_weather_section(weather))
    content_parts.append("---\n\n")
    
    # 添加可转债信息
    if bonds:
        content_parts.append("## 💰 可转债申购清单\n\n")
        
        for i, bond in enumerate(bonds, 1):
            content_parts.append(f"### {i}. {bond['name']} ({bond['code']})\n")
            content_parts.append(f"- **申购代码**: `{bond['apply_code']}`\n")
            content_parts.append(f"- **正股**: {bond['stock_name']} ({bond['stock_code']})\n")
            content_parts.append(f"- **评级**: {bond['rating']}\n")
            content_parts.append("\n")
        
        content_parts.append("---\n\n")
        content_parts.append("💡 **申购提示**：\n")
        content_parts.append("1. 开盘时间即可申购（9:30-15:00）\n")
        content_parts.append("2. 无需市值，中签后再缴款\n")
        content_parts.append("3. 建议顶格申购（通常1万张）\n")
        content_parts.append("\n🔗 [查看详情](https://www.jisilu.cn/data/cbnew/)\n")
    else:
        content_parts.append("## 💰 可转债申购\n\n")
        content_parts.append("今天没有新的可转债可以申购。\n\n")
        content_parts.append("💤 可以安心做其他事情啦！\n")
    
    content_parts.append("\n---\n")
    content_parts.append(f"\n🤖 *自动推送 by GitHub Actions*")
    
    return title, ''.join(content_parts)


def main():
    """
    主函数
    """
    print(f"开始运行每日早报... {datetime.now()}")
    
    # 获取 Server酱 密钥
    serverchan_key = os.environ.get('SERVERCHAN_KEY')
    
    if not serverchan_key:
        print("❌ 错误：未设置 SERVERCHAN_KEY 环境变量")
        print("请在 GitHub 仓库的 Settings -> Secrets 中添加")
        return
    
    # 获取天气信息
    print("正在获取北京天气信息...")
    weather = get_beijing_weather()
    
    if weather:
        print(f"✅ 天气: {weather['weather_desc']}, 温度: {weather['temp']}°C, 日出: {weather['sunrise']}")
    else:
        print("⚠️ 天气信息获取失败，将继续处理可转债信息")
    
    # 获取可转债数据
    print("正在获取可转债数据...")
    all_bonds = get_convertible_bonds()
    
    if not all_bonds:
        print("⚠️ 未获取到可转债数据")
    else:
        print(f"获取到 {len(all_bonds)} 条可转债数据")
    
    # 筛选今天可申购的
    today_bonds = filter_today_bonds(all_bonds)
    print(f"今日可申购: {len(today_bonds)} 只")
    
    # 格式化并发送通知
    title, content = format_message(today_bonds, weather)
    
    print(f"标题: {title}")
    print("正在发送微信通知...")
    
    send_serverchan_notification(title, content, serverchan_key)
    
    print("✅ 任务完成！")


if __name__ == "__main__":
    main()
