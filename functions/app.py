import json
import akshare as ak
import pandas as pd
import plotly.graph_objects as go
from io import StringIO
import os

def handler(event, context):
    # 设置页面内容
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>A股财务数据查询工具</title>
        <meta charset="UTF-8">
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.8/dist/chart.umd.min.js"></script>
    </head>
    <body class="bg-gray-100">
        <div class="container mx-auto p-4 max-w-4xl">
            <h1 class="text-2xl font-bold text-center my-6 text-red-600">佐力药业单季度财务数据</h1>
            
            <div class="bg-white p-6 rounded-lg shadow-md">
                <div class="mb-4">
                    <input type="text" id="stockCode" placeholder="输入股票代码（如300181）" class="w-full p-2 border border-gray-300 rounded">
                    <button onclick="fetchData()" class="mt-2 bg-blue-500 text-white p-2 rounded w-full">查询数据</button>
                </div>
                
                <div id="dataContainer" class="mt-6"></div>
            </div>
        </div>

        <script>
            function fetchData() {
                const code = document.getElementById('stockCode').value;
                fetch(`/.netlify/functions/fetch_data?code=${code}`)
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('dataContainer').innerHTML = data.html;
                    });
            }
        </script>
    </body>
    </html>
    """

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "text/html; charset=utf-8"
        },
        "body": html_content
    }

def fetch_data(event, context):
    stock_code = event['queryStringParameters'].get('code', '300181')
    
    try:
        # 获取数据
        df = ak.stock_zh_a_quarterly_report(symbol=stock_code)
        df = df[['报告期', '毛利率', '营业收入同比增长率', '扣非净利润同比增长率']].head(10)
        
        # 格式化数据
        df.columns = ['时间', '毛利率', '营收', '扣非']
        for col in ['毛利率', '营收', '扣非']:
            df[col] = df[col].apply(lambda x: f"{x:.2f}%" if pd.notnull(x) else "—")
        
        # 生成表格HTML
        table_html = df.to_html(index=False, classes='min-w-full border-collapse')
        table_html = table_html.replace('<th>营收</th>', '<th class="bg-orange-100 p-2 border">营收</th>')
        table_html = table_html.replace('<th>扣非</th>', '<th class="bg-gray-100 p-2 border">扣非</th>')
        table_html = table_html.replace('<td>', '<td class="p-2 border">')
        
        # 生成图表数据
        chart_data = {
            'labels': df['时间'].tolist(),
            'values': df['营收'].str.replace('%', '').tolist()
        }
        
        html = f"""
        <h2 class="text-xl font-semibold mb-4">财务数据</h2>
        {table_html}
        <div class="mt-6">
            <h2 class="text-xl font-semibold mb-4">营收增长率趋势</h2>
            <canvas id="revenueChart" height="300"></canvas>
            <script>
                new Chart(document.getElementById('revenueChart'), {{
                    type: 'line',
                    data: {{
                        labels: {json.dumps(chart_data['labels'])},
                        datasets: [{{
                            label: '营收同比增长率',
                            data: {json.dumps(chart_data['values'])},
                            borderColor: 'blue',
                            tension: 0.2,
                            pointRadius: 5
                        }}]
                    }},
                    options: {{
                        scales: {{
                            y: {{ title: {{ display: true, text: '增长率(%)' }} }}
                        }}
                    }}
                }});
            </script>
        </div>
        """
        
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({"html": html})
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }