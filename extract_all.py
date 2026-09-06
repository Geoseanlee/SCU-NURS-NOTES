import os
import re
import glob
import zipfile
import html as html_lib

def html_to_text(html_content):
    # Remove script and style tags
    html_content = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', html_content, flags=re.S|re.I)
    # Replace block level elements with newlines
    html_content = re.sub(r'<(br|/p|/div|/li|/h[1-6])\s*/?>', '\n', html_content, flags=re.I)
    # Add a prefix to list items for readability
    html_content = re.sub(r'<li[^>]*>', '- ', html_content, flags=re.I)
    # Remove all other HTML tags
    text = re.sub(r'<[^>]+>', '', html_content)
    # Unescape HTML entities (e.g., &nbsp;, &amp;)
    text = html_lib.unescape(text)
    # Split, strip whitespace from lines, and filter out empty lines
    lines = [l.strip() for l in text.splitlines()]
    # Return consolidated lines
    return '\n'.join([l for l in lines if l])

def numeric_prefix(path):
    name = os.path.basename(path)
    m = re.match(r'^(\d+)', name)
    return int(m.group(1)) if m else 9999

def process_module(course_dir, module_dir):
    material_path = os.path.join(course_dir, module_dir, 'material')
    if not os.path.exists(material_path):
        return None, 0
    
    epub_files = glob.glob(os.path.join(material_path, '*.epub'))
    if not epub_files:
        return None, 0
    
    # Sort files numerically based on the leading number in their filename
    epub_files.sort(key=numeric_prefix)
    
    module_output = []
    success_count = 0
    
    for epub in epub_files:
        name = os.path.basename(epub)
        try:
            with zipfile.ZipFile(epub) as z:
                names = z.namelist()
                target = None
                # Check for index.html (case insensitive)
                for n in names:
                    if n.lower().endswith('index.html'):
                        target = n
                        break
                # If not found, look for any html/xhtml file
                if not target:
                    for n in names:
                        if n.lower().endswith(('.html', '.xhtml')):
                            target = n
                            break
                
                if target:
                    content = z.read(target).decode('utf-8', errors='ignore')
                    text = html_to_text(content)
                    success_count += 1
                else:
                    text = "[ERROR: No HTML or XHTML content found inside the EPUB]"
        except Exception as e:
            text = f"[ERROR extracting or parsing EPUB: {e}]"
            
        module_output.append(f"===== FILE: {name} =====\n{text}\n")
    
    output_text = "\n\n".join(module_output)
    output_path = os.path.join(course_dir, module_dir, 'extracted_content.txt')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output_text)
        
    return output_path, success_count

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    courses = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d)) and d.startswith('NURS')]
    courses.sort()
    
    print("=" * 60)
    print("STARTING UNIFIED EPUB EXTRACTION PROCESS")
    print("=" * 60)
    
    total_extracted_modules = 0
    total_files_processed = 0
    
    for course in courses:
        course_path = os.path.join(base_dir, course)
        modules = [d for d in os.listdir(course_path) if os.path.isdir(os.path.join(course_path, d)) and d.startswith('module')]
        modules.sort(key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 999)
        
        print(f"\nCourse: {course}")
        print("-" * 30)
        
        for module in modules:
            out_file, count = process_module(course_path, module)
            if out_file:
                print(f"  [SUCCESS] {module}: Extracted {count} files -> {os.path.basename(out_file)}")
                total_extracted_modules += 1
                total_files_processed += count
            else:
                print(f"  [SKIPPED] {module}: No 'material' directory or EPUB files found.")
                
    print("\n" + "=" * 60)
    print(f"SUMMARY: Processed {total_extracted_modules} modules, extracting {total_files_processed} total EPUB documents.")
    print("=" * 60)

if __name__ == '__main__':
    main()
