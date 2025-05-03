import os
import json
import logging
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QFileDialog, QMessageBox, QTextEdit
from PyQt5.QtCore import Qt
from PIL import Image

CONFIG_FILE = "config.json"

LOG_DIR = "bin"

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
    return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)

def image_to_c_array(image_path, output_header_file):
    """将图片转为 RGB565 格式的 C 语言数组，并保存到指定的头文件"""
    try:
        if not os.path.exists(image_path):
            logging.error(f"图片文件不存在: {image_path}")
            QMessageBox.critical(None, "错误", f"图片文件 '{image_path}' 不存在。")
            return

        logging.info(f"正在处理图片: {image_path}")
        with Image.open(image_path) as img:
            logging.info(f"原始图片尺寸: {img.size}")
            img = img.convert('RGB')
            
            original_width, original_height = img.size

            scale_width = 160 / original_width
            scale_height = 128 / original_height
            scale = min(scale_width, scale_height)

            new_width = int(original_width * scale)
            new_height = int(original_height * scale)

            logging.info(f"图片缩放比例: {scale:.2f}, 最终尺寸: {new_width}x{new_height}")
            img = img.resize((new_width, new_height), Image.LANCZOS)
            
            width, height = img.size
            pixels = list(img.getdata())

        max_size = 851968  # 1310720 字节的 65%
        if width * height * 2 > max_size:
            logging.error(f"图片大小超过限制: {width * height * 2} bytes")
            QMessageBox.critical(None, "错误", "图片大小超过了允许的最大值（1310720 字节的 65%）。")
            return

        rgb565_pixels = [rgb_to_rgb565(r, g, b) for r, g, b in pixels]

        with open(output_header_file, 'w') as f:
            f.write("#pragma once\n")
            f.write("#include <pgmspace.h>\n\n")
            f.write(f"const unsigned short image_data[{width * height}] PROGMEM = {{\n")
            for i, pixel in enumerate(rgb565_pixels):
                if i % 8 == 0:  
                    f.write("\t")
                f.write(f"0x{pixel:04X}, ")
                if (i + 1) % 8 == 0 or i == len(rgb565_pixels) - 1:
                    f.write("\n")
            f.write("};\n\n")
            f.write(f"#define IMAGE_WIDTH {width}\n")
            f.write(f"#define IMAGE_HEIGHT {height}\n")
            f.write(f"#define SCREEN_WIDTH 160\n")  
            f.write(f"#define SCREEN_HEIGHT 128\n")  

        logging.info(f"图片转换完成，文件已保存到: {output_header_file}")
        QMessageBox.information(None, "成功", f"图片转换完成！文件已保存到 {output_header_file}")
    except Exception as e:
        logging.error(f"转换过程中发生错误: {e}")
        QMessageBox.critical(None, "错误", f"转换过程中发生错误：{e}")

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
        return config.get("last_path", "")
    return ""

def save_config(last_path):
    config = {"last_path": last_path}
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

class ImageConverterApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("图片转换工具")
        self.setGeometry(100, 100, 600, 300)

        layout = QVBoxLayout()

        self.label_image_path = QLabel("图片路径:")
        self.entry_image_path = QLineEdit()
        self.btn_browse_image = QPushButton("浏览")
        self.btn_browse_image.clicked.connect(self.select_image)

        self.label_output_path = QLabel("输出路径:")
        self.entry_output_path = QLineEdit()
        self.btn_browse_output = QPushButton("浏览")
        self.btn_browse_output.clicked.connect(self.select_output)

        self.btn_convert = QPushButton("转换图片")
        self.btn_convert.clicked.connect(self.convert_image)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setLineWrapMode(QTextEdit.NoWrap)

        layout.addWidget(self.label_image_path)
        layout.addWidget(self.entry_image_path)
        layout.addWidget(self.btn_browse_image)
        layout.addWidget(self.label_output_path)
        layout.addWidget(self.entry_output_path)
        layout.addWidget(self.btn_browse_output)
        layout.addWidget(self.btn_convert)
        layout.addWidget(self.log_text)

        self.setLayout(layout)

    def select_image(self):
        last_path = load_config()
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择图片",
            last_path,
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_path:
            self.entry_image_path.setText(file_path)
            save_config(os.path.dirname(file_path))

    def select_output(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存 C 语言数组文件",
            "",
            "C 语言头文件 (*.h)"
        )
        if file_path:
            self.entry_output_path.setText(file_path)

    def convert_image(self):
        image_path = self.entry_image_path.text()
        output_header_file = self.entry_output_path.text()
        if not image_path or not output_header_file:
            QMessageBox.warning(self, "警告", "请先选择图片和输出路径！")
            return

        image_to_c_array(image_path, output_header_file)

    def log_message(self, message):
        self.log_text.append(message)
        logging.info(message)

if __name__ == "__main__":
    setup_logging()
    app = QApplication([])
    ex = ImageConverterApp()
    ex.show()
    app.exec_()