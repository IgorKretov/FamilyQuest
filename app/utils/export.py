"""
Экспорт статистики в разные форматы
"""
import csv
import json
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st
from io import StringIO, BytesIO

class DataExporter:
    def __init__(self, engine, db_conn):
        self.engine = engine
        self.conn = db_conn
    
    def export_tasks_csv(self, child_id=None):
        """Экспорт заданий в CSV"""
        cursor = self.conn.cursor()
        
        if child_id:
            cursor.execute('''
                SELECT * FROM tasks 
                WHERE child_id = ? 
                ORDER BY created_at DESC
            ''', (child_id,))
        else:
            cursor.execute('SELECT * FROM tasks ORDER BY created_at DESC')
        
        columns = [description[0] for description in cursor.description]
        data = cursor.fetchall()
        
        # Создаем CSV в памяти
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(columns)
        writer.writerows(data)
        
        return output.getvalue()
    
    def export_children_csv(self):
        """Экспорт данных детей в CSV"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM children ORDER BY points DESC')
        
        columns = [description[0] for description in cursor.description]
        data = cursor.fetchall()
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(columns)
        writer.writerows(data)
        
        return output.getvalue()
    
    def export_achievements_csv(self, child_id=None):
        """Экспорт достижений в CSV"""
        cursor = self.conn.cursor()
        
        if child_id:
            cursor.execute('''
                SELECT a.*, d.name, d.description, d.emoji 
                FROM achievements a
                JOIN achievements_def d ON a.achievement_id = d.id
                WHERE a.child_id = ?
                ORDER BY a.unlocked_at DESC
            ''', (child_id,))
        else:
            cursor.execute('''
                SELECT a.*, d.name, d.description, d.emoji 
                FROM achievements a
                JOIN achievements_def d ON a.achievement_id = d.id
                ORDER BY a.unlocked_at DESC
            ''')
        
        columns = [description[0] for description in cursor.description]
        data = cursor.fetchall()
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(columns)
        writer.writerows(data)
        
        return output.getvalue()
    
    def generate_report(self, child_id=None, days=30):
        """Сгенерировать отчёт за период"""
        cursor = self.conn.cursor()
        
        if child_id:
            cursor.execute('''
                SELECT 
                    date(created_at) as day,
                    COUNT(*) as tasks_count,
                    SUM(points) as total_points
                FROM tasks 
                WHERE child_id = ? 
                    AND completed = 1
                    AND date(created_at) >= date('now', ?)
                GROUP BY date(created_at)
                ORDER BY day DESC
            ''', (child_id, f'-{days} days'))
        else:
            cursor.execute('''
                SELECT 
                    date(created_at) as day,
                    COUNT(*) as tasks_count,
                    SUM(points) as total_points
                FROM tasks 
                WHERE completed = 1
                    AND date(created_at) >= date('now', ?)
                GROUP BY date(created_at)
                ORDER BY day DESC
            ''', (f'-{days} days',))
        
        report_data = cursor.fetchall()
        
        # Создаем DataFrame для удобного отображения
        df = pd.DataFrame(report_data, columns=['Дата', 'Заданий', 'Баллов'])
        return df
    
    def get_child_statistics(self, child_id):
        """Получить полную статистику по ребёнку"""
        cursor = self.conn.cursor()
        
        # Основная информация
        cursor.execute('SELECT * FROM children WHERE id = ?', (child_id,))
        child = cursor.fetchone()
        
        # Количество заданий по категориям
        cursor.execute('''
            SELECT category, COUNT(*) as count, SUM(points) as total_points
            FROM tasks 
            WHERE child_id = ? AND completed = 1
            GROUP BY category
        ''', (child_id,))
        category_stats = cursor.fetchall()
        
        # Динамика по дням (последние 30 дней)
        cursor.execute('''
            SELECT 
                date(completed_at) as day,
                COUNT(*) as tasks,
                SUM(points) as points
            FROM tasks 
            WHERE child_id = ? AND completed = 1
                AND date(completed_at) >= date('now', '-30 days')
            GROUP BY date(completed_at)
            ORDER BY day
        ''', (child_id,))
        daily_stats = cursor.fetchall()
        
        # Достижения
        cursor.execute('''
            SELECT COUNT(*) FROM achievements WHERE child_id = ?
        ''', (child_id,))
        achievements_count = cursor.fetchone()[0]
        
        return {
            'child': child,
            'category_stats': category_stats,
            'daily_stats': daily_stats,
            'achievements_count': achievements_count
        }

def render_export_section(exporter):
    """Рендеринг секции экспорта"""
    st.subheader("📤 Экспорт данных")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 Экспорт детей (CSV)"):
            csv_data = exporter.export_children_csv()
            st.download_button(
                label="💾 Скачать children.csv",
                data=csv_data,
                file_name=f"children_export_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("📥 Экспорт заданий (CSV)"):
            csv_data = exporter.export_tasks_csv()
            st.download_button(
                label="💾 Скачать tasks.csv",
                data=csv_data,
                file_name=f"tasks_export_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    with col3:
        if st.button("📥 Экспорт достижений (CSV)"):
            csv_data = exporter.export_achievements_csv()
            st.download_button(
                label="💾 Скачать achievements.csv",
                data=csv_data,
                file_name=f"achievements_export_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    st.markdown("---")
    st.subheader("📊 Отчёты")
    
    days = st.slider("Период (дней)", min_value=7, max_value=90, value=30)
    
    if st.button("📈 Сгенерировать отчёт"):
        df = exporter.generate_report(days=days)
        
        if not df.empty:
            st.dataframe(df)
            
            # Простая статистика
            total_tasks = df['Заданий'].sum()
            total_points = df['Баллов'].sum()
            avg_per_day = total_tasks / days
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Всего заданий", total_tasks)
            with col2:
                st.metric("Всего баллов", total_points)
            with col3:
                st.metric("В среднем в день", f"{avg_per_day:.1f}")
            
            # График
            st.line_chart(df.set_index('Дата')[['Заданий', 'Баллов']])
        else:
            st.info("Нет данных за выбранный период")
