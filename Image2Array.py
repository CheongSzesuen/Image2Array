from PIL import Image
import os

def rgb_to_rgb565(r, g, b):
    """将 RGB888 转换为 RGB565"""
    return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)

def image_to_c_array(image_path, output_header_file, output_image_dir):
    """将图片转为 RGB565 格式的 C 语言数组，并保存到指定的头文件和图像目录"""
    # 打开图片
    with Image.open(image_path) as img:
        # 转换为 RGB 模式
        img = img.convert('RGB')
        
        # 获取原始图片宽高
        original_width, original_height = img.size

        # 按原始比例缩放，确保不超过屏幕尺寸（160x128）
        scale_width = 160 / original_width
        scale_height = 128 / original_height
        scale = min(scale_width, scale_height)

        new_width = int(original_width * scale)
        new_height = int(original_height * scale)

        print(f"图片将按照原始比例缩放，缩放比例为 {scale:.2f}，最终尺寸为 {new_width}x{new_height}。")

        img = img.resize((new_width, new_height), Image.LANCZOS)
        
        # 获取图片宽高
        width, height = img.size
        # 获取图片像素
        pixels = list(img.getdata())

    # 检查生成的数组是否超过限制大小
    max_size = 851968  # 1310720 字节的 65%
    if width * height * 2 > max_size:
        print("Error: Image size exceeds the maximum allowed size (65% of 1310720 bytes).")
        exit(1)

    # 转换为 RGB565 格式
    rgb565_pixels = [rgb_to_rgb565(r, g, b) for r, g, b in pixels]

    # 创建输出图像目录（如果不存在）
    if not os.path.exists(output_image_dir):
        os.makedirs(output_image_dir)

    # 保存 RGB565 数据到文件
    rgb565_file_path = os.path.join(output_image_dir, "image_data.bin")
    with open(rgb565_file_path, 'wb') as f:
        for pixel in rgb565_pixels:
            f.write(pixel.to_bytes(2, byteorder='big'))

    # 写入 C 语言数组到头文件
    with open(output_header_file, 'w') as f:
        f.write("#pragma once\n")
        f.write("#include <pgmspace.h>\n\n")
        f.write(f"const unsigned short image_data[{width * height}] PROGMEM = {{\n")
        for i, pixel in enumerate(rgb565_pixels):
            if i % 8 == 0:  # 每行 8 个元素
                f.write("\t")
            f.write(f"0x{pixel:04X}, ")
            if (i + 1) % 8 == 0 or i == len(rgb565_pixels) - 1:
                f.write("\n")
        f.write("};\n\n")
        f.write(f"#define IMAGE_WIDTH {width}\n")
        f.write(f"#define IMAGE_HEIGHT {height}\n")
        f.write(f"#define SCREEN_WIDTH 160\n")  # 修改为160
        f.write(f"#define SCREEN_HEIGHT 128\n")  # 修改为128

if __name__ == "__main__":
    # 定义目录路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    originimage_dir = os.path.join(script_dir, 'originimage')
    image_dir = os.path.join(script_dir, 'image')
    output_header_file = os.path.join(script_dir, 'image_data.h')

    # 检查 originimage 目录是否存在
    if not os.path.exists(originimage_dir):
        print(f"Error: Origin image directory '{originimage_dir}' does not exist.")
        exit(1)

    # 获取 originimage 目录中的最新图片文件
    image_files = [f for f in os.listdir(originimage_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
    if not image_files:
        print("Error: No images found in originimage directory.")
        exit(1)
    image_files.sort(key=lambda x: os.path.getmtime(os.path.join(originimage_dir, x)), reverse=True)
    image_path = os.path.join(originimage_dir, image_files[0])

    # 执行转换
    image_to_c_array(image_path, output_header_file, image_dir)
    print("转换完成!")