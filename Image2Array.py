import os
import json
import logging
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, 
                            QLabel, QLineEdit, QFileDialog, QMessageBox, QTextEdit)
from PyQt5.QtCore import Qt
from PIL import Image, ImageFile

# 允许加载截断的图片文件
ImageFile.LOAD_TRUNCATED_IMAGES = True

CONFIG_FILE = "config.json"
LOG_DIR = "bin"

# 支持的图片格式列表（包括常见格式和PSD等专业格式）
SUPPORTED_IMAGE_FORMATS = [
    '*.png', '*.jpg', '*.jpeg', '*.bmp', 
    '*.gif', '*.tiff', '*.webp', '*.psd',
    '*.ico', '*.ppm', '*.pgm', '*.pbm'
]

def setup_logging():
    """设置日志记录"""
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    log_file = os.path.join(LOG_DIR, f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logging.info("程序启动")

def rgb_to_rgb565(r, g, b):
    """将RGB888转换为RGB565格式"""
    return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)

def image_to_c_array(image_path, output_header_file):
    """将图片转为RGB565格式的C语言数组"""
    try:
        # 强制.h扩展名（二次保障）
        if not output_header_file.lower().endswith('.h'):
            output_header_file += '.h'

        if not os.path.exists(image_path):
            raise FileNotFoundError(f"图片文件不存在: {image_path}")

        logging.info(f"正在处理图片: {image_path}")
        with Image.open(image_path) as img:
            # 处理包含透明通道的图片
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1])
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
                
            original_width, original_height = img.size

            # 计算缩放比例
            scale = min(160 / original_width, 128 / original_height)
            new_width = int(original_width * scale)
            new_height = int(original_height * scale)
            
            img = img.resize((new_width, new_height), Image.LANCZOS)
            width, height = img.size
            pixels = list(img.getdata())

        # 检查大小限制
        max_size = 851968  # 1310720字节的65%
        if width * height * 2 > max_size:
            raise ValueError(f"图片大小超过限制（当前: {width*height*2}字节，最大: {max_size}字节）")

        # 生成RGB565数据
        rgb565_pixels = [rgb_to_rgb565(r, g, b) for r, g, b in pixels]

        # 写入文件（使用LF换行符保证跨平台一致性）
        with open(output_header_file, 'w', encoding='utf-8', newline='\n') as f:
            f.write("#pragma once\n")
            f.write("#include <pgmspace.h>\n\n")
            f.write(f"// 原始图片: {os.path.basename(image_path)}\n")
            f.write(f"// 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"const unsigned short image_data[{width * height}] PROGMEM = {{\n")
            
            # 每行8个像素，优化格式化
            for i in range(0, len(rgb565_pixels), 8):
                line = ", ".join(f"0x{p:04X}" for p in rgb565_pixels[i:i+8])
                f.write(f"    {line},\n")
                
            f.write("};\n\n")
            f.write(f"#define IMAGE_WIDTH {width}\n")
            f.write(f"#define IMAGE_HEIGHT {height}\n")
            f.write("#define SCREEN_WIDTH 160\n")
            f.write("#define SCREEN_HEIGHT 128\n")

        logging.info(f"转换成功: {output_header_file}")
        QMessageBox.information(None, "成功", f"文件已保存到:\n{output_header_file}")
        
    except Exception as e:
        logging.error(f"转换失败: {str(e)}", exc_info=True)
        QMessageBox.critical(None, "错误", f"转换失败:\n{str(e)}")

class ImageConverterApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Image2Array")
        self.setGeometry(100, 100, 600, 400)
        
        layout = QVBoxLayout()
        
        # 图片路径选择
        self.label_image = QLabel("选择图片:")
        self.entry_image = QLineEdit()
        self.btn_browse_image = QPushButton("浏览...")
        self.btn_browse_image.clicked.connect(self.select_image)
        
        # 输出路径选择
        self.label_output = QLabel("输出头文件:")
        self.entry_output = QLineEdit()
        self.btn_browse_output = QPushButton("浏览...")
        self.btn_browse_output.clicked.connect(self.select_output)
        
        # 转换按钮
        self.btn_convert = QPushButton("转换图片")
        self.btn_convert.clicked.connect(self.convert_image)
        
        # 日志显示
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        
        # 状态栏
        self.status_label = QLabel("就绪")
        self.status_label.setAlignment(Qt.AlignCenter)
        
        # 添加到布局
        layout.addWidget(self.label_image)
        layout.addWidget(self.entry_image)
        layout.addWidget(self.btn_browse_image)
        layout.addWidget(self.label_output)
        layout.addWidget(self.entry_output)
        layout.addWidget(self.btn_browse_output)
        layout.addWidget(self.btn_convert)
        layout.addWidget(self.log_display)
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
    
    def select_image(self):
        """选择图片文件"""
        last_path = load_config()
        path, _ = QFileDialog.getOpenFileName(
            self, "选择图片", last_path,
            f"图片文件 ({' '.join(SUPPORTED_IMAGE_FORMATS)})"
        )
        if path:
            self.entry_image.setText(path)
            save_config(os.path.dirname(path))
            self.status_label.setText(f"已选择: {os.path.basename(path)}")
    
    def select_output(self):
        """选择输出路径（强制.h扩展名）"""
        default_name = ""
        if self.entry_image.text():
            default_name = os.path.splitext(os.path.basename(self.entry_image.text()))[0] + ".h"
            
        path, _ = QFileDialog.getSaveFileName(
            self, "保存头文件", default_name,
            "C头文件 (*.h);;所有文件 (*)"
        )
        if path:
            # 强制添加.h扩展名（即使用户没输入）
            if not path.lower().endswith('.h'):
                path += '.h'
                
                # 检查文件是否已存在
                if os.path.exists(path):
                    reply = QMessageBox.question(
                        self, "文件已存在",
                        "目标文件已存在，是否覆盖？",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    if reply == QMessageBox.No:
                        return self.select_output()  # 重新选择
            
            self.entry_output.setText(path)
            self.status_label.setText(f"将保存到: {os.path.basename(path)}")
    
    def convert_image(self):
        """执行转换操作"""
        image_path = self.entry_image.text()
        output_path = self.entry_output.text()
        
        if not all([image_path, output_path]):
            QMessageBox.warning(self, "警告", "请先选择图片和输出路径！")
            return
        
        self.status_label.setText("转换中...")
        QApplication.processEvents()  # 强制更新UI
        
        try:
            image_to_c_array(image_path, output_path)
            self.status_label.setText("转换完成！")
        except Exception as e:
            self.status_label.setText("转换失败")
        finally:
            # 记录到日志显示框
            with open(os.path.join(LOG_DIR, sorted(os.listdir(LOG_DIR))[-1]), 'r') as f:
                self.log_display.setText(f.read())
            self.log_display.verticalScrollBar().setValue(
                self.log_display.verticalScrollBar().maximum()
            )

def load_config():
    """加载配置文件"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f).get('last_path', '')
        except:
            return ''
    return ''

def save_config(path):
    """保存配置文件"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump({'last_path': path}, f)
    except Exception as e:
        logging.error(f"保存配置失败: {str(e)}")

if __name__ == "__main__":
    setup_logging()
    app = QApplication([])
    app.setStyle('Fusion')  # 使用更现代的UI风格
    
    # 设置全局字体
    font = app.font()
    font.setPointSize(10)
    app.setFont(font)
    
    window = ImageConverterApp()
    window.show()
    app.exec_()