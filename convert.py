import re
import os # Import the os module for path manipulation
from zhconv import convert # Changed to zhconv for conversion

def convert_md_to_simplified_fullwidth(input_filepath, output_filepath):
    """
    Converts Traditional Chinese characters to Simplified Chinese characters
    and half-width symbols to full-width symbols in a Markdown file.
    Specifically handles the correct conversion of Chinese quotation marks.

    Args:
        input_filepath (str): The path to the input Markdown file.
        output_filepath (str): The path where the converted Markdown file will be saved.
    """
    try:
        with open(input_filepath, 'r', encoding='utf-8') as f_in:
            content = f_in.read()

        # 1. Convert Traditional Chinese characters to Simplified Chinese using zhconv
        # 'zh-cn' represents Simplified Chinese (Mainland China)
        simplified_content = convert(content, 'zh-cn')

        # Base map for half-width to full-width symbols (excluding quotation marks)
        half_to_full_map_base = {
            '!': '！', '(': '（', ')': '）', ',': '，', ':': '：', ';': '；', '?': '？', '[': '【', ']': '】'
        }

        # 2. Smartly handle double and single quotation marks
        in_double_quote = False
        in_single_quote = False
        processed_content_with_quotes = []

        for char in simplified_content:
            if char == '"':
                if not in_double_quote:
                    processed_content_with_quotes.append('“') # First double quote, use opening quote
                    in_double_quote = True
                else:
                    processed_content_with_quotes.append('”') # Second double quote, use closing quote
                    in_double_quote = False
            elif char == "'":
                if not in_single_quote:
                    processed_content_with_quotes.append('‘') # First single quote, use opening quote
                    in_single_quote = True
                else:
                    processed_content_with_quotes.append('’') # Second single quote, use closing quote
                    in_single_quote = False
            else:
                processed_content_with_quotes.append(char)

        # Convert the list back to a string
        content_after_quotes = "".join(processed_content_with_quotes)

        # 3. Convert other half-width symbols to full-width (excluding already processed quotes)
        final_fullwidth_content = []
        for char in content_after_quotes:
            final_fullwidth_content.append(half_to_full_map_base.get(char, char))
        final_fullwidth_content = "".join(final_fullwidth_content)

        with open(output_filepath, 'w', encoding='utf-8') as f_out:
            f_out.write(final_fullwidth_content)

        print(f"文件 '{input_filepath}' 已成功转换为简体全角，并保存到 '{output_filepath}'。")

    except FileNotFoundError:
        print(f"错误：未找到文件 '{input_filepath}'。请检查文件路径是否正确。")
    except Exception as e:
        print(f"处理文件时发生错误：{e}")

# --- 使用示例 ---
if __name__ == "__main__":
    while True:
        input_file = input("请输入您的Markdown文件路径（例如：my_document.md）：")

        # Check if the input file exists and is a file
        if not os.path.exists(input_file):
            print("错误：指定的文件不存在。请重新输入。")
            continue
        if not os.path.isfile(input_file):
            print("错误：指定的路径不是一个文件。请输入有效的文件路径。")
            continue

        # Get the directory of the input file
        input_directory = os.path.dirname(input_file)
        # Get the base name of the input file (e.g., "my_document.md")
        input_filename = os.path.basename(input_file)
        
        # Construct the output filename (e.g., "my_document_converted.md")
        # Split the filename into name and extension
        name, ext = os.path.splitext(input_filename)
        output_filename = f"{name}_converted{ext}"
        
        # Construct the full output path in the same directory as the input file
        output_file = os.path.join(input_directory, output_filename)

        # Perform the conversion
        convert_md_to_simplified_fullwidth(input_file, output_file)
        break # Exit the loop after successful conversion or error handling
